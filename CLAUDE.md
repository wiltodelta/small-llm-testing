# small-llm-testing

You are a **principal Python engineer** maintaining a reproducible local LLM benchmark.

Benchmark small LLMs locally via llama.cpp on Apple Silicon (M5). Working-set
ceiling and per-model footprints: `docs/hardware-notes.md`.

## How to run

```bash
# Install dependencies
uv sync

# Run the curated routine benchmark (n=3 samples per prompt)
uv run python benchmark.py

# Add any current challengers, or run every current text configuration
uv run python benchmark.py --include-challengers
uv run python benchmark.py --full-sweep

# Explicit filters search the routine, challenger, and agentic text sets
uv run python benchmark.py --model gemma-4-e2b   # curated E2B thinking config
uv run python benchmark.py --model -think        # all thinking configs

# Category-filtered reliability recheck (high n); never publishes canonical results
uv run python benchmark.py --model gemma-4-e2b --category structured,consistency -n 20

# Quick smoke test
uv run python benchmark.py -n 1 --no-wait-for-idle
```

Default llama-server port: **8080**.

Normal CLI runs wait automatically before each model until two consecutive 30-second
checks report one-minute load below 4.0. Use `--no-wait-for-idle` only for smoke/debug
runs whose timing will not be interpreted.

## Scripts

- `maintain.sh` -- the canonical Python gate, run after `uv sync`.
- `benchmark.py` -- starts llama-server per model, runs the 22-prompt suite
  (text core plus agent-scenario categories) x N samples, and saves per-model results.
  A full sweep publishes `benchmark.json` and `RESULTS.md` only after all selected
  configs finish; `--category` runs never publish canonical results.
- `make_comparison.py` -- regenerates `results/COMPARISON.md` and the README quick-choice
  table from a complete `benchmark.json`.
- `reasoning_experiment.py` -- reproduces the completed direct, low-effort, and
  6,144-token bounded-thinking screen without replacing canonical results; its preflight
  requires the retired Ling and Granite weights, dropped from the local model
  cache at retirement.
- `tests/` -- pytest unit tests for the pure verifier logic (`v_number`, `v_json`,
  `v_python_exec`, ...) and the comparison aggregation helpers. No llama-server needed.

## Configuration

For the mandatory model-research checklist, per-flag `ModelConfig` semantics,
`DEFAULT_SERVER_ARGS`, the per-model `n_ctx` that the article answer budget derives from,
and the f16-vs-q8_0 KV justification, see `docs/configuration.md`.

## Test set

Verifier catalog, `/66` scoring, per-category rationale, and the think/no-think
evaluation method: see `docs/benchmark-design.md`.

## Result files

- `results/benchmark.json`, `results/RESULTS.md`, and `results/COMPARISON.md` -- published
  canonical raw data, prompt detail, and cross-run comparison.
- `results/benchmark.<model-name>.json` -- gitignored per-model snapshot (saved after each
  model finishes; safe against mid-run crashes/sleep). Category-filtered runs write
  `results/benchmark.<model-name>.<categories>.json` instead, never the canonical files.

## Known issues

llama-server start failures, the Mellum2 PR requirement, port-8080 staleness, and the
jetsam OOM hazard: see `docs/troubleshooting.md`.
