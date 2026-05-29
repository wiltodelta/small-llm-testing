# small-llm-testing

Benchmark small LLMs locally via llama.cpp on Apple Silicon (M5, 32 GB unified
memory, ~24.96 GB GPU working set).

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

- `maintain.sh` -- uv sync + uv-outdated + uv-secure + ruff check/fix + format + pyright.
  Note: `set -e` makes the whole script abort at `uv-secure` if any dependency has a
  CVE, before reaching ruff/pyright. To validate code edits when an unrelated transitive
  CVE blocks it, run directly: `uv run ruff check && uv run ruff format --check && uv run pyright`.
- `benchmark.py` -- starts llama-server per model, runs 16 prompts x N samples,
  saves per-model and aggregated results
- `generate_test_image.py` -- creates `assets/test_chart.png` for vision prompts

## Configuration

- `MODELS` list in `benchmark.py` defines all configs. Each `ModelConfig` has:
  - `temperature`, `top_p`, `top_k` (vendor-recommended defaults)
  - `thinking: bool` -- toggles `chat_template_kwargs={"enable_thinking": False}` per request
  - `image_min_tokens` -- Qwen-only; forces visual token floor for OCR/chart accuracy
  - `server_args` -- per-model llama-server overrides (e.g. `-c 8192` for 27B, or
    `--spec-type draft-mtp --spec-draft-n-max 2 -np 1` for the 27B MTP A/B run --
    MTP needs `supports_vision=False` since `--mmproj` is unsupported with MTP)
- `DEFAULT_SERVER_ARGS` in `benchmark.py` applies to every server start:
  `-ngl 99 -fa on -ub 1024 -c 16384`. KV cache stays at the f16 default (NOT q8_0):
  on 32 GB everything fits, and f16 KV is ~1.7x faster decode than q8_0 on this M5
  (llama-bench Qwen3.6-27B: 6.32 vs 3.72 tg t/s). Quantized K on Metal is costly.
  q8_0 KV was a 16 GB-machine memory hack -- do not re-add it.
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

## Memory class (M5, ~24.96 GB working set)

Measure the real GPU working set (the ceiling for weights + KV + compute buffers) with
a one-line Swift Metal query (do not guess it):
`echo 'import Metal; print(MTLCreateSystemDefaultDevice()!.recommendedMaxWorkingSetSize)' | swift -`

- Gemma 4 26B-A4B Q4_K_M (~16.8 GB) and Qwen 3.6 27B Q4_K_M (~16.8 GB) fit
  comfortably (these were OOM / kernel-panic on the old 16 GB machine).
- Qwen 3.6 35B-A3B UD-Q4_K_M (~22.1 GB) excluded -- too marginal (88% of working
  set, <3 GB left for KV + compute). A Q3_K_M (~17 GB) quant would fit if revisited.
- Phi-4-Reasoning 15B -- excluded for speed (7.9 tok/s), not memory.
- Zyphra ZAYA1-8B -- excluded: hybrid-Mamba MoE, no working llama.cpp path
  (official deploy is a custom vLLM fork), text-only.
