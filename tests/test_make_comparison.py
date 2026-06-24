"""Tests for the pure aggregation helpers in make_comparison.py."""

from __future__ import annotations

from typing import Any

from make_comparison import _fail_counts, _think_pairs


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
