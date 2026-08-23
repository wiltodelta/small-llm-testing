"""Tests for the pure verifier logic in benchmark.py.

The verifiers decide every pass/fail in the suite, so a bug here silently corrupts
all results. These tests pin their behavior with no llama-server dependency.
"""

from __future__ import annotations

import io
import json
import urllib.error
from typing import TYPE_CHECKING

import pytest

import benchmark
from benchmark import (
    AGENTIC_TEXT_MODELS,
    CHALLENGERS,
    CURRENT_TEXT_MODELS,
    FULL_SWEEP_MODELS,
    MODELS,
    PROMPTS,
    ModelConfig,
    SamplingPreset,
    _missing_model_assets,
    _run_one_attempt,
    _select_models,
    _strip_think,
    fail_kind,
    run_benchmark,
    v_json,
    v_number,
    v_python_exec,
    v_regex,
    v_yes_no,
)

if TYPE_CHECKING:
    from pathlib import Path

# Retired Muse config kept so DFlash attach and reasoning_strength stay tested.
# Retired 2026-08-23 but kept as a fixture: it is the only preset exercising
# direct_sampling + reasoning_effort together, and that seam outlives the model.
_RETIRED_QWEN38 = ModelConfig(
    name="qwen3.8-27b-Q4_K_M-think",
    hf="unsloth/Qwen3.8-27B-GGUF:Qwen3.8-27B-Q4_K_M.gguf",
    temperature=1.0,
    top_p=0.95,
    top_k=20,
    thinking=True,
    direct_sampling=SamplingPreset(temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5),
    reasoning_effort="xhigh",
)

_RETIRED_MUSE = ModelConfig(
    name="muse-glimmer-30b-high-Q4_K_XL",
    hf="unsloth/Muse-Glimmer-30B-GGUF:Muse-Glimmer-30B-UD-Q4_K_XL.gguf",
    temperature=1.0,
    top_p=0.95,
    top_k=64,
    reasoning_strength="high",
)


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


def test_challenger_model_set_is_explicit() -> None:
    assert {model.name for model in CHALLENGERS} == {
        "nemotron-3.5-lightning-30b-a3b-Q3_K_M",
    }
    assert len(CURRENT_TEXT_MODELS) == len(MODELS) + len(CHALLENGERS)


def test_full_sweep_model_set_is_explicit_and_unique() -> None:
    assert {model.name for model in AGENTIC_TEXT_MODELS} == {"north-mini-code-1.0-Q4_K_M"}
    assert len(FULL_SWEEP_MODELS) == 8
    assert len({model.name for model in FULL_SWEEP_MODELS}) == len(FULL_SWEEP_MODELS)


def test_select_models_defaults_to_curated() -> None:
    assert _select_models(None, include_challengers=False) == MODELS


def test_select_models_includes_challengers() -> None:
    assert _select_models(None, include_challengers=True) == list(CURRENT_TEXT_MODELS)


def test_select_models_full_sweep() -> None:
    assert _select_models(None, include_challengers=False, full_sweep=True) == list(FULL_SWEEP_MODELS)


def test_resolve_local_path_honors_pinned_revision(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cache = tmp_path / "models--example--model"
    expected = cache / "snapshots" / "pinned" / "model.gguf"
    current = cache / "snapshots" / "current" / "model.gguf"
    expected.parent.mkdir(parents=True)
    current.parent.mkdir(parents=True)
    expected.touch()
    current.touch()
    (cache / "refs").mkdir()
    (cache / "refs" / "main").write_text("current")
    monkeypatch.setattr(benchmark, "HF_HUB_DIR", tmp_path)

    assert benchmark._resolve_local_path("example/model:model.gguf") == current
    assert benchmark._resolve_local_path("example/model:model.gguf", revision="pinned") == expected
    assert benchmark._resolve_local_path("example/model:model.gguf", revision="missing") is None


def test_select_models_filter_excludes_retired_models_and_searches_agentic_set() -> None:
    assert _select_models("qwen3.6", include_challengers=False) == []
    assert _select_models("nanbeige", include_challengers=False) == []
    assert _select_models("muse-glimmer", include_challengers=False) == []
    assert _select_models("lfm2.5-2.6b", include_challengers=False) == []
    # Retired 2026-08-23: too slow to finish an article answer on this machine.
    assert _select_models("qwen3.8", include_challengers=False) == []
    assert [model.name for model in _select_models("nemotron", include_challengers=False)] == [
        "nemotron-3.5-lightning-30b-a3b-Q3_K_M",
    ]
    assert _select_models("north-mini", include_challengers=False) == AGENTIC_TEXT_MODELS


def test_nemotron_uses_embedded_mtp() -> None:
    selected = _select_models("nemotron-3.5", include_challengers=False)
    assert len(selected) == 1
    assert selected[0].server_args == ("--spec-type", "draft-mtp")
    assert selected[0].top_k == 0


def test_missing_model_assets_deduplicates_shared_weight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_path(hf: str, *, revision: str | None = None) -> None:
        return None

    monkeypatch.setattr(benchmark, "_resolve_local_path", missing_path)

    assert _missing_model_assets(MODELS[:2]) == [MODELS[0].hf]


def test_missing_model_assets_allows_absent_weights_outside_full_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_path(hf: str, *, revision: str | None = None) -> None:
        return None

    monkeypatch.setattr(benchmark, "_resolve_local_path", missing_path)

    assert _missing_model_assets(CHALLENGERS, require_weights=False) == []


def test_missing_model_assets_requires_gemma_mtp_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "gemma.gguf"
    model_path.touch()

    def resolved_path(hf: str) -> Path:
        return model_path

    monkeypatch.setattr(benchmark, "_resolve_local_path", resolved_path)

    assert _missing_model_assets(MODELS[:2]) == ["unsloth/gemma-4-E2B-it-GGUF:mtp-*.gguf"]


def test_missing_model_assets_requires_muse_dflash_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "muse.gguf"
    model_path.touch()

    def resolved_path(hf: str) -> Path:
        return model_path

    monkeypatch.setattr(benchmark, "_resolve_local_path", resolved_path)

    expected = ["unsloth/Muse-Glimmer-30B-GGUF:dflash-kquant.gguf"]
    assert _missing_model_assets([_RETIRED_MUSE]) == expected
    assert _missing_model_assets([_RETIRED_MUSE], require_weights=False) == expected


def test_start_server_attaches_muse_dflash(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "muse.gguf"
    model_path.touch()
    (tmp_path / "dflash-kquant.gguf").touch()
    captured: list[str] = []

    def popen(cmd: list[str], **kwargs: object) -> object:
        captured.extend(cmd)
        return object()

    def resolved_path(hf: str) -> Path:
        return model_path

    def wait_for_server(port: int) -> None:
        return None

    monkeypatch.setattr(benchmark, "_resolve_local_path", resolved_path)
    monkeypatch.setattr(benchmark.subprocess, "Popen", popen)
    monkeypatch.setattr(benchmark, "_wait_for_server", wait_for_server)

    benchmark._start_server(_RETIRED_MUSE, 8081)

    assert captured[captured.index("--spec-type") + 1] == "draft-dflash"
    assert captured[captured.index("--spec-draft-n-max") + 1] == "15"
    assert str(tmp_path / "dflash-kquant.gguf") in captured


def test_start_server_stops_process_when_health_check_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.touch()

    class Process:
        terminated = False
        waited = False

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: int | None = None) -> None:
            self.waited = True

    process = Process()

    def popen(cmd: list[str], **kwargs: object) -> Process:
        return process

    def resolved_path(hf: str) -> Path:
        return model_path

    def wait_for_server(port: int) -> None:
        raise TimeoutError

    monkeypatch.setattr(benchmark, "_resolve_local_path", resolved_path)
    monkeypatch.setattr(benchmark.subprocess, "Popen", popen)
    monkeypatch.setattr(benchmark, "_wait_for_server", wait_for_server)

    with pytest.raises(TimeoutError):
        benchmark._start_server(MODELS[-1], 8081)

    assert process.terminated
    assert process.waited


@pytest.mark.parametrize(("thinking", "expected"), [(False, "low"), (True, "high")])
def test_chat_sends_muse_reasoning_strength(
    monkeypatch: pytest.MonkeyPatch,
    thinking: bool,
    expected: str,
) -> None:
    payloads: list[dict[str, object]] = []

    class Response:
        status = 200

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "ok"}}], "usage": {"completion_tokens": 1}}).encode()

    def urlopen(request: object, timeout: int) -> Response:
        payloads.append(json.loads(request.data.decode()))
        return Response()

    monkeypatch.setattr(benchmark.urllib.request, "urlopen", urlopen)

    benchmark._chat([{"role": "user", "content": "test"}], _RETIRED_MUSE, 8081, thinking=thinking)

    assert payloads[0]["chat_template_kwargs"] == {
        "enable_thinking": thinking,
        "reasoning_strength": expected,
    }


@pytest.mark.parametrize(
    ("thinking", "expected_sampling", "expected_effort"),
    [
        (True, (1.0, 0.95, 20, 0.0), "xhigh"),
        (False, (0.7, 0.8, 20, 1.5), None),
    ],
)
def test_chat_sends_qwen38_mode_specific_preset(
    monkeypatch: pytest.MonkeyPatch,
    thinking: bool,
    expected_sampling: tuple[float, float, int, float],
    expected_effort: str | None,
) -> None:
    payloads: list[dict[str, object]] = []

    class Response:
        status = 200

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "ok"}}], "usage": {"completion_tokens": 1}}).encode()

    def urlopen(request: object, timeout: int) -> Response:
        payloads.append(json.loads(request.data.decode()))
        return Response()

    monkeypatch.setattr(benchmark.urllib.request, "urlopen", urlopen)
    benchmark._chat([{"role": "user", "content": "test"}], _RETIRED_QWEN38, 8081, thinking=thinking)

    payload = payloads[0]
    actual_sampling = (payload["temperature"], payload["top_p"], payload["top_k"], payload["presence_penalty"])
    assert actual_sampling == expected_sampling
    assert payload["chat_template_kwargs"] == {"enable_thinking": thinking}
    assert payload.get("reasoning_effort") == expected_effort


def test_full_sweep_mode_does_not_publish_aggregate_progress(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    aggregate_writes: list[str] = []

    def is_downloaded(model: benchmark.ModelConfig) -> bool:
        return True

    def start_server(model: benchmark.ModelConfig, port: int) -> object:
        return object()

    def stop_server(proc: object) -> None:
        return None

    def save_json(results: list[benchmark.ModelResult]) -> Path:
        aggregate_writes.append("json")
        return tmp_path / "benchmark.json"

    def save_markdown(results: list[benchmark.ModelResult]) -> Path:
        aggregate_writes.append("markdown")
        return tmp_path / "RESULTS.md"

    monkeypatch.setattr(benchmark, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(benchmark, "PROMPTS", [])
    monkeypatch.setattr(benchmark, "_is_model_downloaded", is_downloaded)
    monkeypatch.setattr(benchmark, "_start_server", start_server)
    monkeypatch.setattr(benchmark, "_stop_server", stop_server)
    monkeypatch.setattr(benchmark, "_save_json", save_json)
    monkeypatch.setattr(benchmark, "_save_markdown", save_markdown)

    results = run_benchmark([MODELS[0]], save_aggregate_progress=False)

    assert len(results) == 1
    assert aggregate_writes == []
    assert (tmp_path / f"benchmark.{MODELS[0].name}.json").exists()


def test_main_does_not_publish_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    class Args:
        model = "gemma-4-e2b"
        include_challengers = False
        full_sweep = False
        port = 8081
        n_runs = 1
        category = None

    aggregate_writes: list[str] = []

    def no_missing_assets(
        models: list[benchmark.ModelConfig],
        *,
        require_weights: bool,
    ) -> list[str]:
        return []

    def no_results(
        models: list[benchmark.ModelConfig],
        port: int,
        n: int,
        *,
        prompts: list[benchmark.Prompt],
        save_aggregate_progress: bool,
        snapshot_tag: str | None,
    ) -> list[benchmark.ModelResult]:
        return []

    def save_json(results: list[benchmark.ModelResult]) -> None:
        aggregate_writes.append("json")

    def save_markdown(results: list[benchmark.ModelResult]) -> None:
        aggregate_writes.append("markdown")

    monkeypatch.setattr(benchmark, "_parse_args", Args)
    monkeypatch.setattr(benchmark, "_missing_model_assets", no_missing_assets)
    monkeypatch.setattr(benchmark, "run_benchmark", no_results)
    monkeypatch.setattr(benchmark, "_save_json", save_json)
    monkeypatch.setattr(benchmark, "_save_markdown", save_markdown)

    with pytest.raises(SystemExit, match="3"):
        benchmark.main()

    assert aggregate_writes == []


def test_api_error_records_elapsed_wall_time(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise TimeoutError

    times = iter((100.0, 107.25))
    monkeypatch.setattr(benchmark, "_chat", raise_timeout)
    monkeypatch.setattr(benchmark.time, "monotonic", lambda: next(times))

    attempt = _run_one_attempt(PROMPTS[0], MODELS[0], port=8080)

    assert attempt.time_s == 7.25
    assert attempt.fail_reason == "api error: TimeoutError"


def test_api_error_records_http_status_and_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_http(*args: object, **kwargs: object) -> None:
        raise urllib.error.HTTPError(
            "http://127.0.0.1:8080/v1/chat/completions",
            400,
            "Bad Request",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"unknown field"}}'),
        )

    monkeypatch.setattr(benchmark, "_chat", raise_http)

    attempt = _run_one_attempt(PROMPTS[0], MODELS[0], port=8080)

    assert attempt.fail_reason == 'api error: HTTPError 400 {"error":{"message":"unknown field"}}'


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

    def test_array_of_strings_case_and_order_insensitive(self) -> None:
        ok, _ = v_json({"members": ["Ro Aldis", "Petal Vun", "Sena Marn"]})(
            '{"members": ["sena marn", "RO ALDIS", " petal vun "]}'
        )
        assert ok

    def test_array_wrong_length_fails(self) -> None:
        ok, _ = v_json({"members": ["Ro Aldis", "Petal Vun", "Sena Marn"]})('{"members": ["Ro Aldis", "Petal Vun"]}')
        assert not ok

    def test_array_different_member_fails(self) -> None:
        ok, _ = v_json({"members": ["Ro Aldis", "Petal Vun"]})('{"members": ["Ro Aldis", "Dana Ott"]}')
        assert not ok

    def test_array_not_a_list_fails(self) -> None:
        ok, _ = v_json({"members": ["Ro Aldis"]})('{"members": "Ro Aldis"}')
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
            ("truncated: hit the 12288-token generation cap", "truncated"),
            ("no number ~=24", "wrong"),
            ("missing key 'age'", "wrong"),
            ("", "wrong"),
        ],
    )
    def test_classification(self, reason: str, expected: str) -> None:
        assert fail_kind(reason) == expected
