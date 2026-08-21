"""Tests for the agent-scenario prompt extensions.

Pins the suite inventory (like the pinned model sets), the consistency-pair gold
answers, and the long-context article's integrity: the two variants must differ in
exactly one planted contradiction, the needle fact must be unique, and stated work
counts must match the listings. A drift here silently corrupts the scenario results.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

import benchmark
from benchmark import (
    FERREL_ARTICLE,
    FERREL_ARTICLE_BAD,
    MODELS,
    PROMPTS,
    THINKING_CATEGORIES,
    _chat,
    _ferrel_article,
    _filter_prompts,
    run_benchmark,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_prompt_set_is_pinned() -> None:
    # Literal names pin the suite; a prompt must not silently appear or vanish.
    assert [p.name for p in PROMPTS] == [
        "math_mul",
        "math_multistep",
        "math_modular",
        "word_speed",
        "word_age",
        "logic_syllogism_no",
        "logic_negation",
        "code_fizzbuzz",
        "code_palindrome",
        "code_reverse_words",
        "json_person",
        "format_primes",
        "json_fields",
        "cons_date_shift",
        "cons_digit_swap",
        "cons_dead_action",
        "cons_unit_equivalent",
        "cons_complementary",
        "cons_relative_rank",
        "longctx_inconsistent",
        "longctx_consistent",
        "longctx_needle",
    ]


def test_category_counts() -> None:
    assert Counter(p.category for p in PROMPTS) == {
        "math": 3,
        "reasoning": 4,
        "coding": 3,
        "structured": 3,
        "consistency": 6,
        "longcontext": 3,
    }


def test_thinking_gate_covers_reasoning_like_categories() -> None:
    # `structured` stays excluded: thinking on strict-format tasks wastes tokens.
    assert frozenset({"math", "reasoning", "coding", "consistency", "longcontext"}) == THINKING_CATEGORIES


class TestConsistencyPrompts:
    # Gold answers per prompt: half contradict, half do not, so an always-yes or
    # always-no bias scores 50%.
    GOLD: ClassVar[dict[str, bool]] = {
        "cons_date_shift": True,
        "cons_digit_swap": True,
        "cons_dead_action": True,
        "cons_unit_equivalent": False,
        "cons_complementary": False,
        "cons_relative_rank": False,
    }

    @pytest.mark.parametrize(("name", "want_yes"), sorted(GOLD.items()))
    def test_verifier_accepts_gold_answer(self, name: str, want_yes: bool) -> None:
        prompt = next(p for p in PROMPTS if p.name == name)
        gold = "Yes." if want_yes else "No."
        assert prompt.verify(gold) == (True, "")
        opposite = "No." if want_yes else "Yes."
        ok, _ = prompt.verify(opposite)
        assert not ok

    def test_all_consistency_prompts_are_two_statements(self) -> None:
        for prompt in PROMPTS:
            if prompt.category == "consistency":
                content = str(prompt.messages[0]["content"])
                assert content.startswith("Statement A: ")
                assert "\nStatement B: " in content
                assert "Answer with one word: yes or no." in content

    def test_balance_is_even(self) -> None:
        # Three contradictions and three non-contradictions, no accidental drift.
        assert sorted(self.GOLD.values()) == [False, False, False, True, True, True]


class TestFerrelArticle:
    def test_variants_differ_only_in_planted_year(self) -> None:
        assert FERREL_ARTICLE_BAD.replace("1891", "1887") == FERREL_ARTICLE
        assert len(FERREL_ARTICLE_BAD) == len(FERREL_ARTICLE)

    def test_contradiction_year_appears_once(self) -> None:
        assert FERREL_ARTICLE_BAD.count("1891") == 1
        assert "1891" not in FERREL_ARTICLE

    def test_birth_year_stated_consistently_in_reference(self) -> None:
        # Lead, Early life, and Legacy all carry 1887 in the consistent variant.
        assert FERREL_ARTICLE.count("1887") == 3
        assert FERREL_ARTICLE_BAD.count("1887") == 2

    def test_needle_year_is_unique(self) -> None:
        assert FERREL_ARTICLE.count("1928") == 1

    def test_length_bounds(self) -> None:
        # Long enough to be a real article-scale prompt, short enough that a capped
        # answer fits the smallest server context in the fleet (-c 8192).
        assert 9000 <= len(FERREL_ARTICLE) <= 14000

    def test_builder_is_deterministic(self) -> None:
        assert _ferrel_article(1887) == FERREL_ARTICLE
        assert _ferrel_article(1887) == _ferrel_article(1887)

    def test_stated_work_counts_match_listings(self) -> None:
        # Counts promised in the lead/section openers must match the actual lists.
        assert "five operas" in FERREL_ARTICLE
        assert "four symphonies" in FERREL_ARTICLE
        assert "seven string quartets" in FERREL_ARTICLE
        assert "more than sixty songs" in FERREL_ARTICLE
        for title in (
            "The Salt Garden",
            "The Winter Lock",
            "North of Halmen",
            "The Cartographer's Daughter",
            "The Lantern Procession",
        ):
            assert FERREL_ARTICLE.count(title) == 1, title
        # The chamber section lists quartets as "No. N (YYYY)"; nothing else uses
        # that format, so this pins the seven listed quartets.
        assert len(re.findall(r"No\. \d+ \(\d{4}\)", FERREL_ARTICLE)) == 7


class TestLongcontextPrompts:
    def test_prompts_carry_article_and_output_cap(self) -> None:
        for name in ("longctx_inconsistent", "longctx_consistent", "longctx_needle"):
            prompt = next(p for p in PROMPTS if p.name == name)
            content = str(prompt.messages[0]["content"])
            assert prompt.max_completion_tokens == 4096
            assert len(content) > 9000
            assert "Augustin Ferrel" in content

    def test_inconsistent_variant_planted_in_prompt(self) -> None:
        bad = next(p for p in PROMPTS if p.name == "longctx_inconsistent")
        assert "1891" in str(bad.messages[0]["content"])
        good = next(p for p in PROMPTS if p.name == "longctx_consistent")
        assert "1891" not in str(good.messages[0]["content"])

    def test_gold_answers(self) -> None:
        golds = {"longctx_inconsistent": "Yes.", "longctx_consistent": "No.", "longctx_needle": "1928"}
        for name, gold in golds.items():
            prompt = next(p for p in PROMPTS if p.name == name)
            assert prompt.verify(gold) == (True, "")


class TestFilterPrompts:
    def test_selects_requested_categories(self) -> None:
        selected = _filter_prompts(PROMPTS, ["structured", "consistency"])
        assert {p.category for p in selected} == {"structured", "consistency"}
        assert len(selected) == 9

    def test_normalizes_case_and_whitespace(self) -> None:
        assert _filter_prompts(PROMPTS, [" Math "]) == [p for p in PROMPTS if p.category == "math"]

    def test_unknown_category_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown categories: mathh"):
            _filter_prompts(PROMPTS, ["mathh"])


def test_chat_respects_per_prompt_token_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads: list[dict[str, Any]] = []

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "ok"}}], "usage": {"completion_tokens": 1}}).encode()

    def urlopen(request: object, timeout: int) -> Response:
        payloads.append(json.loads(request.data.decode()))  # type: ignore[attr-defined]
        return Response()

    monkeypatch.setattr(benchmark.urllib.request, "urlopen", urlopen)

    _chat([{"role": "user", "content": "test"}], MODELS[0], 8081, thinking=True, max_tokens_cap=4096)
    _chat([{"role": "user", "content": "test"}], MODELS[0], 8081, thinking=True)

    assert payloads[0]["max_tokens"] == 4096  # capped below the 16384 think default
    assert payloads[1]["max_tokens"] == 16384


def test_filtered_run_writes_tagged_snapshot_and_skips_publish(
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
    monkeypatch.setattr(benchmark, "_is_model_downloaded", is_downloaded)
    monkeypatch.setattr(benchmark, "_start_server", start_server)
    monkeypatch.setattr(benchmark, "_stop_server", stop_server)
    monkeypatch.setattr(benchmark, "_save_json", save_json)
    monkeypatch.setattr(benchmark, "_save_markdown", save_markdown)

    math_prompts = _filter_prompts(PROMPTS, ["math"])
    results = run_benchmark(
        [MODELS[0]],
        prompts=math_prompts,
        save_aggregate_progress=False,
        snapshot_tag="math",
    )

    assert len(results) == 1
    assert aggregate_writes == []
    assert (tmp_path / f"benchmark.{MODELS[0].name}.math.json").exists()
    # The untagged full-suite snapshot must not be touched by a filtered run.
    assert not (tmp_path / f"benchmark.{MODELS[0].name}.json").exists()
