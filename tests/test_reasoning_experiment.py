"""Tests for the bounded-thinking experiment configuration."""

from __future__ import annotations

import pytest

import benchmark
import reasoning_experiment


def test_experiment_variants_are_explicit_and_target_aligned() -> None:
    models = reasoning_experiment.experiment_models()

    assert [model.name for model in models] == [
        "mellum2-12b-a2.5b-think-budget6144",
        "ling-3.0-tiny-direct",
        "ling-3.0-tiny-think-budget6144",
        "granite-4.2-8b-direct",
        "granite-4.2-8b-low-effort",
        "granite-4.2-8b-think-budget6144",
    ]
    assert models[0].server_args[-2:] == ("--reasoning-budget", "6144")
    assert models[1].thinking is False
    assert models[2].server_args[-2:] == ("--reasoning-budget", "6144")
    assert models[3].thinking is False
    assert models[4].low_effort is True
    assert models[5].server_args[-2:] == ("--reasoning-budget", "6144")


def test_main_rejects_missing_retired_weights_before_opening_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_assets(models: object, *, require_weights: bool) -> list[str]:
        assert models
        assert require_weights is True
        return ["retired/model.gguf"]

    def unexpected_socket(*args: object, **kwargs: object) -> object:
        pytest.fail("port probe must follow asset preflight")

    monkeypatch.setattr(
        benchmark,
        "missing_model_assets",
        missing_assets,
    )
    monkeypatch.setattr(
        reasoning_experiment.socket,
        "socket",
        unexpected_socket,
    )

    with pytest.raises(RuntimeError, match=r"experiment assets missing: retired/model\.gguf"):
        reasoning_experiment.main()
