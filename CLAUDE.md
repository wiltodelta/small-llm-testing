# small-llm-testing

Benchmark small LLMs locally via llama.cpp on Apple Silicon M4 16GB.

## How to run

```bash
# Install dependencies
uv sync

# Generate test chart for vision prompts (only once)
uv run python generate_test_image.py

# Run full benchmark (n=3 samples per prompt)
uv run python benchmark.py

# Filter to a single model variant (substring match)
uv run python benchmark.py --model gemma-4-e2b
uv run python benchmark.py --model Q8_0-think    # all thinking variants

# Quick smoke test
uv run python benchmark.py -n 1
```

Default llama-server port: **8080**. Wrap long runs with `nohup caffeinate -dimu`
so a closed lid doesn't kill them.

## Scripts

- `maintain.sh` -- uv sync + ruff check/fix + format + pyright
- `benchmark.py` -- starts llama-server per model, runs 16 prompts x N samples,
  saves per-model and aggregated results
- `generate_test_image.py` -- creates `assets/test_chart.png` for vision prompts

## Configuration

- `MODELS` list in `benchmark.py` defines all configs. Each `ModelConfig` has:
  - `temperature`, `top_p`, `top_k` (vendor-recommended defaults)
  - `thinking: bool` -- toggles `chat_template_kwargs={"enable_thinking": False}` per request
  - `image_min_tokens` -- Qwen-only; forces visual token floor for OCR/chart accuracy
  - `server_args` -- per-model llama-server overrides (e.g. `-c 8192` for 9B)
- `DEFAULT_SERVER_ARGS` in `benchmark.py` applies to every server start:
  `-ngl 99 -fa on -ub 1024 -c 16384 --cache-type-k q8_0 --cache-type-v q8_0`
- llama-server binary: `/opt/homebrew/bin/llama-server`
- `REQUEST_TIMEOUT = 120` -- thinking models loop on translation prompts; fail fast
- `DEFAULT_N_RUNS = 3` -- each prompt sampled this many times to average out temperature

## Test set

16 prompts across 7 categories (math, reasoning, coding, language, translation, vision).
Verifiers replace substring matching with:

- `v_number(expected, tol)` -- finds any decimal in answer matching expected within tolerance
- `v_yes_no(want_yes)` -- first yes/no token must match (catches "yes, but actually no")
- `v_regex(pattern)` -- regex search
- `v_python_exec(test_cases)` -- extracts Python from `\`\`\`python\`\`\`` block, runs it
  in a subprocess, asserts each `(call_expr, expected_value)` returns expected

`_strip_think(text)` removes `<think>...</think>` blocks before verification.

## Result files

- `results/benchmark.json` -- aggregated raw results (latest run, all models)
- `results/benchmark.<model-name>.json` -- per-model snapshot (saved after each model
  finishes; safe against mid-run crashes/sleep)
- `results/RESULTS.md` -- formatted summary table
- `results/COMPARISON.md` -- cross-run comparison table

## Known issues

- llama-server's `-hf` resolver hangs on some Qwen repos even when files are cached.
  We always start with `-m <local_path>` discovered under `~/.cache/huggingface/hub/`.
- `--image-min-tokens 1024` is Qwen-only. Gemma 4 mmproj caps image_max_pixels lower
  and rejects this flag (image_max_pixels < image_min_pixels). Field `image_min_tokens`
  on ModelConfig is opt-in.
- Qwen3 thinking-mode loops on trivial prompts (translations, "reply with one word")
  and overflows max_tokens or hits REQUEST_TIMEOUT. Fix: use no-think mode for short
  factual queries; thinking only helps on math/word-problems/code.
- Stale `python3.1` processes can hold port 8080 after a previous llama-server crashes.
  Check `lsof -i :8080` before starting a new run.

## Models that don't fit on M4 16GB

- Gemma 4 26B-A4B (~15 GB Q4) -- OOM
- Qwen 3.6 27B Q2_K_XL (~11.8 GB) -- kernel panic during model load
  (Apple GPU recommendedMaxWorkingSetSize is only 12.7 GB on this M4)
- Qwen 3.6 35B-A3B (any quant) -- same memory class
