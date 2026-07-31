"""Tests for the pure verifier logic in benchmark.py.

The verifiers decide every pass/fail in the suite, so a bug here silently corrupts
all results. These tests pin their behavior with no llama-server dependency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import benchmark
from benchmark import (
    MODELS,
    PROMPTS,
    _run_one_attempt,
    _strip_think,
    fail_kind,
    v_json,
    v_number,
    v_python_exec,
    v_regex,
    v_yes_no,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_default_model_set_is_curated() -> None:
    # Literal names intentionally pin the routine core; do not derive this set from MODELS.
    assert {model.name for model in MODELS} == {
        "gemma-4-e2b-Q8_0-think",
        "gemma-4-e2b-Q8_0-nothink",
        "gemma-4-26b-a4b-Q4_K_M-think",
        "gemma-4-26b-a4b-Q4_K_M-nothink",
        "lfm2.5-8b-a1b-Q8_0",
        "mellum2-12b-a2.5b-think-Q4_K_M",
    }


def test_api_error_records_elapsed_wall_time(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise TimeoutError

    times = iter((100.0, 107.25))
    monkeypatch.setattr(benchmark, "_chat", raise_timeout)
    monkeypatch.setattr(benchmark.time, "monotonic", lambda: next(times))

    attempt = _run_one_attempt(PROMPTS[0], MODELS[0], port=8080)

    assert attempt.time_s == 7.25
    assert attempt.fail_reason == "api error: TimeoutError"


def test_save_json_creates_nested_results_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    results_dir = tmp_path / "challengers" / "north"
    monkeypatch.setattr(benchmark, "RESULTS_DIR", results_dir)

    path = benchmark._save_json([])

    assert path == results_dir / "benchmark.json"
    assert path.exists()


class TestStripThink:
    def test_removes_think_block(self) -> None:
        assert _strip_think("<think>pondering</think>42") == "42"

    def test_removes_multiline_think_block(self) -> None:
        assert _strip_think("<think>\nline1\nline2\n</think>\nanswer") == "answer"

    def test_no_think_block_is_trimmed(self) -> None:
        assert _strip_think("  plain answer  ") == "plain answer"

    def test_unclosed_think_block_is_left_intact(self) -> None:
        # Only fully closed <think>...</think> pairs are stripped.
        assert _strip_think("<think>still thinking") == "<think>still thinking"


class TestVNumber:
    def test_exact_match(self) -> None:
        ok, _ = v_number(391)("The answer is 391.")
        assert ok

    def test_within_tolerance(self) -> None:
        ok, _ = v_number(2.25, tol=0.01)("2.25 hours")
        assert ok

    def test_outside_tolerance(self) -> None:
        ok, reason = v_number(2.25, tol=0.01)("2.5 hours")
        assert not ok
        assert "2.25" in reason

    def test_negative_number(self) -> None:
        ok, _ = v_number(-5)("result: -5")
        assert ok

    def test_picks_matching_number_among_several(self) -> None:
        # 1024 mod 1000 = 24: the answer mentions both 1024 and 24; 24 must match.
        ok, _ = v_number(24)("1024 mod 1000 is 24")
        assert ok

    def test_empty_answer_fails(self) -> None:
        ok, reason = v_number(1)("")
        assert not ok
        assert reason == "empty"

    def test_strips_think_before_matching(self) -> None:
        ok, _ = v_number(158)("<think>62*3=186, 186-28=158</think>158")
        assert ok


class TestVYesNo:
    def test_first_token_yes(self) -> None:
        ok, _ = v_yes_no(want_yes=True)("Yes, that follows.")
        assert ok

    def test_first_token_no(self) -> None:
        ok, _ = v_yes_no(want_yes=False)("No, not valid.")
        assert ok

    def test_yes_but_actually_no_is_caught(self) -> None:
        # The first yes/no token wins, so "yes ... no" fails a want_no check.
        ok, reason = v_yes_no(want_yes=False)("Yes, but actually no.")
        assert not ok
        assert "yes" in reason

    def test_no_token_present(self) -> None:
        ok, reason = v_yes_no(want_yes=True)("maybe, it depends")
        assert not ok
        assert reason == "no yes/no token"

    def test_empty_answer_fails(self) -> None:
        ok, reason = v_yes_no(want_yes=True)("")
        assert not ok
        assert reason == "empty"


class TestVRegex:
    def test_match(self) -> None:
        ok, _ = v_regex(r"^\s*2\s*,\s*3\s*,\s*5\s*,\s*7\s*,\s*11\s*\.?\s*$")("2, 3, 5, 7, 11")
        assert ok

    def test_trailing_period_allowed(self) -> None:
        ok, _ = v_regex(r"^\s*2\s*,\s*3\s*,\s*5\s*,\s*7\s*,\s*11\s*\.?\s*$")("2, 3, 5, 7, 11.")
        assert ok

    def test_leading_prose_fails_strict_format(self) -> None:
        ok, reason = v_regex(r"^\s*2\s*,\s*3\s*,\s*5\s*,\s*7\s*,\s*11\s*\.?\s*$")(
            "The first five primes are 2, 3, 5, 7, 11"
        )
        assert not ok
        assert "no regex match" in reason

    def test_empty_answer_fails(self) -> None:
        ok, reason = v_regex(r"x")("")
        assert not ok
        assert reason == "empty"


class TestVJson:
    def test_exact_object(self) -> None:
        ok, _ = v_json({"name": "Maria", "age": 34})('{"name": "Maria", "age": 34}')
        assert ok

    def test_tolerates_json_fence_and_prose(self) -> None:
        ok, _ = v_json({"name": "Maria", "age": 34})('Here you go:\n```json\n{"name": "Maria", "age": 34}\n```')
        assert ok

    def test_number_as_string_compares_by_value(self) -> None:
        ok, _ = v_json({"age": 34})('{"age": "34"}')
        assert ok

    def test_string_case_insensitive(self) -> None:
        ok, _ = v_json({"name": "maria"})('{"name": "MARIA"}')
        assert ok

    def test_missing_key_fails(self) -> None:
        ok, reason = v_json({"name": "Maria", "age": 34})('{"name": "Maria"}')
        assert not ok
        assert "age" in reason

    def test_wrong_value_fails(self) -> None:
        ok, reason = v_json({"age": 34})('{"age": 35}')
        assert not ok
        assert "age" in reason

    def test_no_json_object(self) -> None:
        ok, reason = v_json({"age": 34})("no object here")
        assert not ok
        assert reason == "no JSON object"

    def test_invalid_json(self) -> None:
        ok, reason = v_json({"age": 34})("{age: 34,}")
        assert not ok
        assert reason == "invalid JSON"

    def test_bool_not_confused_with_int(self) -> None:
        # In Python True == 1; the verifier must not accept True where 1 is wanted.
        ok, _ = v_json({"flag": 1})('{"flag": true}')
        assert not ok


class TestVPythonExec:
    def test_correct_function_passes(self) -> None:
        response = "```python\ndef fizzbuzz(n: int) -> str:\n    return 'Fizz' if n % 3 == 0 else str(n)\n```"
        ok, _ = v_python_exec([("fizzbuzz(3)", "Fizz"), ("fizzbuzz(7)", "7")])(response)
        assert ok

    def test_wrong_output_fails(self) -> None:
        response = "```python\ndef double(n):\n    return n + 1\n```"
        ok, reason = v_python_exec([("double(2)", 4)])(response)
        assert not ok
        assert "double(2)" in reason

    def test_bare_true_expected_value(self) -> None:
        # repr() (not json.dumps) embeds the expected value, so True stays True.
        response = "```python\ndef is_empty(s):\n    return len(s) == 0\n```"
        ok, _ = v_python_exec([("is_empty('')", True), ("is_empty('x')", False)])(response)
        assert ok

    def test_no_code_block_falls_back_to_raw(self) -> None:
        response = "def add(a, b):\n    return a + b"
        ok, _ = v_python_exec([("add(2, 3)", 5)])(response)
        assert ok

    def test_empty_response(self) -> None:
        ok, reason = v_python_exec([("f()", 1)])("")
        assert not ok
        assert reason == "empty"

    def test_runtime_exception_is_reported(self) -> None:
        response = "```python\ndef boom(n):\n    raise ValueError('nope')\n```"
        ok, reason = v_python_exec([("boom(1)", 1)])(response)
        assert not ok
        assert "ValueError" in reason


class TestFailKind:
    @pytest.mark.parametrize(
        ("reason", "expected"),
        [
            ("exec timeout", "timeout"),
            ("Server timed out", "timeout"),
            ("empty", "empty"),
            ("api error: URLError", "empty"),
            ("no number ~=24", "wrong"),
            ("missing key 'age'", "wrong"),
            ("", "wrong"),
        ],
    )
    def test_classification(self, reason: str, expected: str) -> None:
        assert fail_kind(reason) == expected
