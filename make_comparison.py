"""Regenerate results/COMPARISON.md from results/benchmark.json.

COMPARISON.md is the analytical view (think vs no-think, fail breakdown) on top of the
raw RESULTS.md. Run after a benchmark to refresh it:

    uv run python make_comparison.py

Numbers come straight from benchmark.json, never hand-typed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from benchmark import BenchmarkData, ModelDict, count_fail_kinds

log = logging.getLogger(__name__)
RESULTS_DIR = Path(__file__).parent / "results"


def _fail_counts(model: ModelDict) -> tuple[int, int, int]:
    return count_fail_kinds(a["fail_reason"] for p in model["prompts"] for a in p["attempts"] if not a["ok"])


def _think_pairs(models: dict[str, ModelDict]) -> list[str]:
    """Base labels that have BOTH a `-think` and a `-nothink` config (Gemma and Qwen).

    The base is the name minus the trailing `-think` (e.g. `gemma-4-e2b-Q8_0` or
    `qwen3.5-2b-Q8_0-mtp`).
    """
    bases: list[str] = []
    for name in models:
        if name.endswith("-think"):
            base = name[: -len("-think")]
            if f"{base}-nothink" in models:
                bases.append(base)
    return sorted(bases)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # json.loads is Any at the boundary; we trust benchmark.json matches the schema written by
    # benchmark._save_json. From here on the typed view lets pyright check every key access.
    data: BenchmarkData = json.loads((RESULTS_DIR / "benchmark.json").read_text())
    models: dict[str, ModelDict] = {m["model"]: m for m in data["models"]}

    lines: list[str] = [
        "# Benchmark comparison",
        "",
        f"Generated from `benchmark.json` ({data['timestamp']}). Apple M5, 32 GB, f16 KV.",
        "Test set: 12-prompt text discriminating core, n=3. Every config scores out of `/36`.",
        "",
        "Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,",
        "not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward",
        "the end (27B ran last); use `llama-bench` on a cool machine for peak decode speed.",
        "",
        "## All configs",
        "",
        "| Model | Passes | Fails w/t/e | Total time | tok/s |",
        "|---|---|---|---|---|",
    ]
    for name, m in models.items():
        w, t, e = _fail_counts(m)
        lines.append(
            f"| {name} | {m['passes']}/{m['attempts_total']} | {w}/{t}/{e} | "
            f"{m['total_time_s']:.0f}s | {m['gen_tok_per_s']:.1f} |"
        )

    lines += [
        "",
        "## Thinking vs no-thinking (Gemma 4 and Qwen; Qwen are MTP)",
        "",
        "| Config | think | nothink | think fails w/t/e |",
        "|---|---|---|---|",
    ]
    for base in _think_pairs(models):
        th, no = models[f"{base}-think"], models[f"{base}-nothink"]
        w, t, e = _fail_counts(th)
        lines.append(
            f"| {base} | {th['passes']}/{th['attempts_total']} | {no['passes']}/{no['attempts_total']} | {w}/{t}/{e} |"
        )

    out = RESULTS_DIR / "COMPARISON.md"
    out.write_text("\n".join(lines) + "\n")
    log.info("Wrote %s (%d configs)", out, len(models))


if __name__ == "__main__":
    main()
