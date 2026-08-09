"""Tests for the pure aggregation helpers in make_comparison.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

import make_comparison
from make_comparison import (
    QUICK_CHOICE_END,
    QUICK_CHOICE_START,
    QUICK_CHOICES,
    _fail_counts,
    _render_quick_choice,
    _replace_generated_block,
    _think_pairs,
    _write_if_changed,
)

if TYPE_CHECKING:
    from pathlib import Path


def _attempt(ok: bool, fail_reason: str = "") -> dict[str, Any]:
    return {"ok": ok, "fail_reason": fail_reason}


class TestThinkPairs:
    def test_pairs_with_both_modes(self) -> None:
        models = {
            "gemma-4-e2b-Q8_0-think": {},
            "gemma-4-e2b-Q8_0-nothink": {},
            "qwen3.5-2b-Q8_0-mtp-think": {},
            "qwen3.5-2b-Q8_0-mtp-nothink": {},
        }
        assert _think_pairs(models) == ["gemma-4-e2b-Q8_0", "qwen3.5-2b-Q8_0-mtp"]

    def test_think_without_nothink_is_excluded(self) -> None:
        models = {"mellum2-think": {}, "phi-4-mini-Q8_0": {}}
        assert _think_pairs(models) == []

    def test_result_is_sorted(self) -> None:
        models = {
            "zeta-think": {},
            "zeta-nothink": {},
            "alpha-think": {},
            "alpha-nothink": {},
        }
        assert _think_pairs(models) == ["alpha", "zeta"]


class TestFailCounts:
    def test_counts_by_kind(self) -> None:
        model = {
            "prompts": [
                {
                    "attempts": [
                        _attempt(ok=True),
                        _attempt(ok=False, fail_reason="no number ~=24"),
                        _attempt(ok=False, fail_reason="exec timeout"),
                        _attempt(ok=False, fail_reason="empty"),
                    ]
                }
            ]
        }
        assert _fail_counts(model) == (1, 1, 1)

    def test_passing_attempts_are_not_counted(self) -> None:
        model = {"prompts": [{"attempts": [_attempt(ok=True), _attempt(ok=True)]}]}
        assert _fail_counts(model) == (0, 0, 0)


class TestQuickChoice:
    def test_renders_curated_metrics(self) -> None:
        models = {
            config: {
                "passes": index,
                "attempts_total": 36,
                "total_time_s": 12.6,
                "gen_tok_per_s": 34.56,
            }
            for index, config in enumerate(QUICK_CHOICES, start=30)
        }

        rendered = _render_quick_choice(models, "2026-07-30T06:17:44+00:00")  # type: ignore[arg-type]

        assert "Measured 2026-07-30 on Apple M5, 32 GB, with f16 KV." in rendered
        assert "| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) |" in rendered
        assert "| Q8_0 + MTP | think | 30/36 | 13s | 34.6 | Compact reasoning |" in rendered
        assert "| Q4_K_M | native think | 35/36 | 13s | 34.6 |" in rendered

    def test_rejects_incomplete_benchmark(self) -> None:
        with pytest.raises(ValueError, match="missing curated configs"):
            _render_quick_choice({}, "2026-07-30")

    def test_rejects_metadata_drift(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(make_comparison, "QUICK_CHOICES", {})

        with pytest.raises(ValueError, match="exactly match"):
            _render_quick_choice({}, "2026-07-30")

    def test_replaces_only_generated_block(self) -> None:
        original = f"before\n{QUICK_CHOICE_START}\nold\n{QUICK_CHOICE_END}\nafter\n"

        updated = _replace_generated_block(original, "new")

        assert updated == f"before\n{QUICK_CHOICE_START}\nnew\n{QUICK_CHOICE_END}\nafter\n"

    def test_requires_one_marker_pair(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            _replace_generated_block("no markers", "new")

    def test_incomplete_benchmark_does_not_overwrite_outputs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "benchmark.json").write_text('{"timestamp": "test", "models": []}')
        comparison = results_dir / "COMPARISON.md"
        comparison.write_text("published comparison\n")
        readme = tmp_path / "README.md"
        readme.write_text(f"{QUICK_CHOICE_START}\npublished table\n{QUICK_CHOICE_END}\n")
        monkeypatch.setattr(make_comparison, "RESULTS_DIR", results_dir)
        monkeypatch.setattr(make_comparison, "README_PATH", readme)

        with pytest.raises(ValueError, match="missing curated configs"):
            make_comparison.main()

        assert comparison.read_text() == "published comparison\n"
        assert "published table" in readme.read_text()

    def test_write_if_changed_skips_identical_content(self, tmp_path: Path) -> None:
        path = tmp_path / "output.md"

        assert _write_if_changed(path, "content\n") is True
        assert _write_if_changed(path, "content\n") is False
        assert path.read_text() == "content\n"
