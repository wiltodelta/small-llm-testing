"""Regenerate results/COMPARISON.md from results/benchmark.json.

COMPARISON.md is the analytical view (think vs no-think, MTP speedup by size, fail
breakdown) on top of the raw RESULTS.md. Run after a benchmark to refresh it:

    uv run python make_comparison.py

Numbers come straight from benchmark.json, never hand-typed.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from benchmark import fail_kind

log = logging.getLogger(__name__)
RESULTS_DIR = Path(__file__).parent / "results"
# A Qwen config name: <size-label>[-mtp]-<think|nothink>. Gemma names don't match.
_NAME_RE = re.compile(r"(?P<size>qwen[\d.]+-[\dab]+-\w+?)(?P<mtp>-mtp)?-(?P<mode>think|nothink)$")


def _fail_counts(model: Any) -> tuple[int, int, int]:
    kinds = [fail_kind(a["fail_reason"]) for p in model["prompts"] for a in p["attempts"] if not a["ok"]]
    return kinds.count("wrong"), kinds.count("timeout"), kinds.count("empty")


def _qwen_sizes(models: dict[str, Any]) -> list[str]:
    """Distinct Qwen size-labels (non-MTP names), sorted."""
    sizes: set[str] = set()
    for name in models:
        m = _NAME_RE.match(name)
        if m and not m.group("mtp"):
            sizes.add(m.group("size"))
    return sorted(sizes)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data: Any = json.loads((RESULTS_DIR / "benchmark.json").read_text())
    models: dict[str, Any] = {m["model"]: m for m in data["models"]}

    lines: list[str] = [
        "# Benchmark comparison",
        "",
        f"Generated from `benchmark.json` ({data['timestamp']}). Apple M5, 32 GB, f16 KV.",
        "Test set: 9-prompt discriminating core, n=3. Scores: vision-on configs `/27`,",
        "MTP configs `/18` (vision-off -- `--mmproj` unsupported with MTP).",
        "",
        "Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,",
        "not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward",
        "the end (27B ran last); use `llama-bench` on a cool machine for peak decode speed.",
        "(3) MTP vs non-MTP accuracy is comparable only on shared non-vision prompts.",
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

    sizes = _qwen_sizes(models)

    lines += [
        "",
        "## Thinking vs no-thinking (non-MTP)",
        "",
        "| Size | think | nothink | think fails w/t/e |",
        "|---|---|---|---|",
    ]
    for size in sizes:
        th, no = models.get(f"{size}-think"), models.get(f"{size}-nothink")
        if not (th and no):
            continue
        w, t, e = _fail_counts(th)
        lines.append(
            f"| {size} | {th['passes']}/{th['attempts_total']} | {no['passes']}/{no['attempts_total']} | {w}/{t}/{e} |"
        )

    lines += [
        "",
        "## MTP tok/s speedup (mtp / non-mtp, same mode)",
        "",
        "| Size | think | nothink |",
        "|---|---|---|",
    ]
    for size in sizes:
        cells: list[str] = [f"| {size} "]
        for mode in ("think", "nothink"):
            base, mtp = models.get(f"{size}-{mode}"), models.get(f"{size}-mtp-{mode}")
            if base and mtp and base["gen_tok_per_s"] > 0:
                cells.append(f"| {mtp['gen_tok_per_s'] / base['gen_tok_per_s']:.2f}x ")
            else:
                cells.append("| - ")
        lines.append("".join(cells) + "|")

    out = RESULTS_DIR / "COMPARISON.md"
    out.write_text("\n".join(lines) + "\n")
    log.info("Wrote %s (%d configs)", out, len(models))


if __name__ == "__main__":
    main()
