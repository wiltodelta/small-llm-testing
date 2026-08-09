# small-llm-testing

You are a **principal Python engineer** maintaining a reproducible local LLM benchmark.

Benchmark small LLMs locally via llama.cpp on Apple Silicon (M5, 32 GB unified
memory, ~24.96 GB GPU working set).

## How to run

```bash
# Install dependencies
uv sync

# Run the curated routine benchmark (n=3 samples per prompt)
uv run python benchmark.py

# Filter by substring match
uv run python benchmark.py --model gemma-4-e2b   # both gemma-4-e2b modes
uv run python benchmark.py --model -think        # all thinking configs

# Quick smoke test
uv run python benchmark.py -n 1
```

Default llama-server port: **8080**. Wrap long runs with `nohup caffeinate -dimu`
so a closed lid doesn't kill them.

## Scripts

- `maintain.sh` -- uv sync + uv-outdated + uv-secure + ruff check/fix + format + pyright + pytest.
- `benchmark.py` -- starts llama-server per model, runs 12 prompts x N samples,
  saves per-model and aggregated results (`benchmark.json` + `RESULTS.md`)
- `make_comparison.py` -- regenerates `results/COMPARISON.md` and the README quick-choice
  table from a complete `benchmark.json`; numbers are never hand-typed.
- `tests/` -- pytest unit tests for the pure verifier logic (`v_number`, `v_json`,
  `v_python_exec`, ...) and the comparison aggregation helpers. No llama-server needed.

## Configuration

Per-flag `ModelConfig` semantics, `DEFAULT_SERVER_ARGS`, and the f16-vs-q8_0 KV
justification: see `docs/configuration.md`.

## Test set

Verifier catalog, `/36` scoring, per-category rationale, and the think/no-think
evaluation method: see `docs/benchmark-design.md`.

## Result files

- `results/benchmark.json`, `results/RESULTS.md`, and `results/COMPARISON.md` -- published
  canonical raw data, prompt detail, and cross-run comparison.
- `results/benchmark.<model-name>.json` -- gitignored per-model snapshot (saved after each
  model finishes; safe against mid-run crashes/sleep).

## Known issues

llama-server start failures, the Mellum2 PR requirement, port-8080 staleness, and the
jetsam OOM hazard: see `docs/troubleshooting.md`.

## Memory class

Measured model footprints and the working-set ceiling (M5): see `docs/hardware-notes.md`.
