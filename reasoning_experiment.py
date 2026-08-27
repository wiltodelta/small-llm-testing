"""Run the bounded-thinking experiment without replacing canonical benchmark results."""

from __future__ import annotations

import json
import logging
import socket
from dataclasses import replace
from datetime import UTC, datetime

import benchmark

log = logging.getLogger(__name__)

PORT = 8081
REASONING_BUDGET = 6144
TARGET_CATEGORIES = frozenset({"consistency", "longcontext"})
SNAPSHOT_TAG = "reasoning-experiment"


def _current(name: str) -> benchmark.ModelConfig:
    return next(model for model in benchmark.CURRENT_TEXT_MODELS if model.name == name)


def experiment_models() -> list[benchmark.ModelConfig]:
    """Return the six inference variants under comparison."""
    mellum = _current("mellum2-12b-a2.5b-think-Q4_K_M")
    ling = benchmark.ModelConfig(
        name="ling-3.0-tiny-Q8_0-think",
        hf="bloomer010/Ling-3.0-tiny-GGUF:Ling-3.0-tiny-Q8_0.gguf",
        revision="76d03bfc93a2b0ec84aac5f187cdf3793541e2a7",
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        thinking=True,
    )
    granite = benchmark.ModelConfig(
        name="granite-4.2-8b-Q8_0-low-effort",
        hf="bartowski/granite-4.2-8b-GGUF:granite-4.2-8b-Q8_0.gguf",
        revision="a592100df8fe4931c7cffbac7b28e8176a1d52da",
        temperature=1.0,
        top_p=0.95,
        top_k=0,
        thinking=True,
        low_effort=True,
    )
    budget_args = ("--reasoning-budget", str(REASONING_BUDGET))
    return [
        replace(
            mellum,
            name="mellum2-12b-a2.5b-think-budget6144",
            server_args=budget_args,
        ),
        replace(ling, name="ling-3.0-tiny-direct", thinking=False),
        replace(
            ling,
            name="ling-3.0-tiny-think-budget6144",
            server_args=(*ling.server_args, *budget_args),
        ),
        replace(granite, name="granite-4.2-8b-direct", thinking=False, low_effort=False),
        replace(granite, name="granite-4.2-8b-low-effort", low_effort=True),
        replace(
            granite,
            name="granite-4.2-8b-think-budget6144",
            server_args=budget_args,
            low_effort=False,
        ),
    ]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    models = experiment_models()
    missing = benchmark.missing_model_assets(models, require_weights=True)
    if missing:
        raise RuntimeError(f"experiment assets missing: {', '.join(missing)}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError(f"port {PORT} is already in use")
    prompts = [prompt for prompt in benchmark.PROMPTS if prompt.category in TARGET_CATEGORIES]
    results = benchmark.run_benchmark(
        models,
        port=PORT,
        n=3,
        prompts=prompts,
        save_aggregate_progress=False,
        snapshot_tag=SNAPSHOT_TAG,
        wait_for_idle=True,
    )
    if len(results) != len(models):
        raise RuntimeError(f"experiment incomplete: finished {len(results)} of {len(models)} variants")
    path = benchmark.RESULTS_DIR / "benchmark.reasoning-experiment.json"
    model_data: list[benchmark.ModelDict] = []
    for model in models:
        snapshot = benchmark.RESULTS_DIR / f"benchmark.{model.name}.{SNAPSHOT_TAG}.json"
        snapshot_data: benchmark.BenchmarkData = json.loads(snapshot.read_text())
        model_data.extend(snapshot_data["models"])
    data: benchmark.BenchmarkData = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "models": model_data,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    log.info("Saved combined experiment results: %s", path)


if __name__ == "__main__":
    main()
