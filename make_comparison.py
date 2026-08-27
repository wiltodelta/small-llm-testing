"""Regenerate published benchmark summaries from results/benchmark.json.

COMPARISON.md is the full analytical view (think vs no-think, fail breakdown). The
README quick-choice table is refreshed from the same data. Run after a benchmark:

    uv run python make_comparison.py

Numbers come straight from benchmark.json, never hand-typed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from benchmark import MODELS, BenchmarkData, ModelDict, count_fail_kinds

log = logging.getLogger(__name__)
RESULTS_DIR = Path(__file__).parent / "results"
README_PATH = Path(__file__).parent / "README.md"
QUICK_CHOICE_START = "<!-- BEGIN GENERATED QUICK CHOICE -->"
QUICK_CHOICE_END = "<!-- END GENERATED QUICK CHOICE -->"
QUICK_CHOICES = {
    "gemma-4-e2b-Q8_0-think": (
        "Gemma 4 E2B",
        "Q8_0 + MTP",
        "think",
        "Compact reasoning",
    ),
    "gemma-4-26b-a4b-Q4_K_M-nothink": (
        "Gemma 4 26B-A4B",
        "UD-Q4_K_M + MTP",
        "direct",
        "Low-latency near-perfect answers",
    ),
    "mellum2-12b-a2.5b-think-Q4_K_M": (
        "Mellum2-12B-A2.5B",
        "Q4_K_M",
        "native think",
        "Background wiki-audit agent",
    ),
}


def _fail_counts(model: ModelDict) -> tuple[int, int, int, int]:
    return count_fail_kinds(a["fail_reason"] for p in model["prompts"] for a in p["attempts"] if not a["ok"])


def _think_pairs(models: dict[str, ModelDict]) -> list[str]:
    """Base labels that have both a `-think` and a `-nothink` config.

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


def _render_quick_choice(models: dict[str, ModelDict], timestamp: str) -> str:
    """Render the README decision table from the current curated model results."""
    curated_names = [model.name for model in MODELS]
    if set(QUICK_CHOICES) != set(curated_names):
        msg = "QUICK_CHOICES metadata must exactly match benchmark.MODELS"
        raise ValueError(msg)
    missing = [config for config in curated_names if config not in models]
    if missing:
        msg = f"benchmark.json is missing curated configs: {', '.join(missing)}"
        raise ValueError(msg)
    lines = [
        f"Measured {timestamp[:10]} on Apple M5, 32 GB, with f16 KV.",
        "",
        "| Model | Quant | Mode | Score | Suite time | tok/s | Choose it for |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for model_config in MODELS:
        config = model_config.name
        label, quant, mode, use_case = QUICK_CHOICES[config]
        repo = model_config.hf.partition(":")[0]
        model = models[config]
        lines.append(
            f"| [{label}](https://huggingface.co/{repo}) | {quant} | {mode} | "
            f"{model['passes']}/{model['attempts_total']} | "
            f"{model['total_time_s']:.0f}s | {model['gen_tok_per_s']:.1f} | {use_case} |"
        )
    return "\n".join(lines)


def _write_if_changed(path: Path, content: str) -> bool:
    """Write content only when it differs, returning whether the file changed."""
    if path.exists() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def _replace_generated_block(text: str, replacement: str) -> str:
    """Replace the unique generated README block while preserving its markers."""
    if text.count(QUICK_CHOICE_START) != 1 or text.count(QUICK_CHOICE_END) != 1:
        msg = "README must contain exactly one quick-choice marker pair"
        raise ValueError(msg)
    before, remainder = text.split(QUICK_CHOICE_START, maxsplit=1)
    _, after = remainder.split(QUICK_CHOICE_END, maxsplit=1)
    return f"{before}{QUICK_CHOICE_START}\n{replacement}\n{QUICK_CHOICE_END}{after}"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # json.loads is Any at the boundary; we trust benchmark.json matches the schema written by
    # benchmark._save_json. From here on the typed view lets pyright check every key access.
    data: BenchmarkData = json.loads((RESULTS_DIR / "benchmark.json").read_text())
    models: dict[str, ModelDict] = {m["model"]: m for m in data["models"]}
    quick_choice = _render_quick_choice(models, data["timestamp"])
    # The suite size changed with the agent-scenario expansion, so the denominator is
    # computed from the data rather than hardcoded: old benchmark.json files stay honest.
    suite_attempts = max(m["attempts_total"] for m in data["models"])

    lines: list[str] = [
        "# Benchmark comparison",
        "",
        f"Generated from `benchmark.json` ({data['timestamp']}). Apple M5, 32 GB, f16 KV.",
        f"Test set: discriminating text core plus agent-scenario categories, n=3 per prompt. "
        f"Every config scores out of `/{suite_attempts}`.",
        "",
        "Caveats: (1) fails split `wrong/timeout/empty/truncated` -- only `wrong` is a model",
        "verdict; the other three mean the harness stopped the attempt. (2) `tok/s` from this",
        "long suite is thermally throttled toward the end; use `llama-bench` on a cool machine",
        "for peak decode speed.",
        "",
        "## All configs",
        "",
        "| Model | Passes | Fails w/t/e/x | Total time | tok/s |",
        "|---|---|---|---|---|",
    ]
    for name, m in models.items():
        w, t, e, x = _fail_counts(m)
        lines.append(
            f"| {name} | {m['passes']}/{m['attempts_total']} | {w}/{t}/{e}/{x} | "
            f"{m['total_time_s']:.0f}s | {m['gen_tok_per_s']:.1f} |"
        )

    lines += [
        "",
        "## Thinking vs no-thinking",
        "",
        "| Config | think | nothink | think fails w/t/e/x |",
        "|---|---|---|---|",
    ]
    for base in _think_pairs(models):
        th, no = models[f"{base}-think"], models[f"{base}-nothink"]
        w, t, e, x = _fail_counts(th)
        lines.append(
            f"| {base} | {th['passes']}/{th['attempts_total']} | "
            f"{no['passes']}/{no['attempts_total']} | {w}/{t}/{e}/{x} |"
        )

    out = RESULTS_DIR / "COMPARISON.md"
    comparison = "\n".join(lines) + "\n"
    changed = _write_if_changed(out, comparison)
    log.info("%s %s (%d configs)", "Wrote" if changed else "Unchanged", out, len(models))

    original_readme = README_PATH.read_text()
    readme = _replace_generated_block(original_readme, quick_choice)
    changed = _write_if_changed(README_PATH, readme)
    log.info("%s quick-choice table in %s", "Updated" if changed else "Unchanged", README_PATH)


if __name__ == "__main__":
    main()
