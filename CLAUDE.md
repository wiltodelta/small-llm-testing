# small-llm-testing

Benchmark small LLMs locally via llama.cpp on Apple Silicon (M5, 32 GB unified
memory, ~24.96 GB GPU working set).

## How to run

```bash
# Install dependencies
uv sync

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
- `benchmark.py` -- starts llama-server per model, runs 12 prompts x N samples,
  saves per-model and aggregated results (`benchmark.json` + `RESULTS.md`)
- `make_comparison.py` -- regenerates `results/COMPARISON.md` (think vs no-think,
  fail breakdown) from `benchmark.json`. Run after a benchmark; numbers
  are read from the data, never hand-typed.

## Configuration

- `MODELS` list in `benchmark.py` defines all configs. Each `ModelConfig` has:
  - `temperature`, `top_p`, `top_k` (vendor-recommended, verified per model card)
  - `presence_penalty` (default 0.0) and `repetition_penalty` (default 1.0, sent as llama.cpp
    `repeat_penalty`) -- vendor anti-repetition knobs. Qwen sets presence_penalty 1.5 (0.0 on
    the 27B thinking); LFM2.5 sets repetition_penalty 1.05. Both target thinking-mode looping.
  - `thinking: bool` -- gates whether this config thinks on `THINKING_CATEGORIES`. `_chat`
    sends `chat_template_kwargs={"enable_thinking": <thinking>}` on EVERY request: models with
    a toggle (Qwen3, Gemma 4) honor it; GLM (its toggle is `thinking:{type}`, not enable_thinking)
    and toggle-less models (Ministral/Phi/LFM/Mellum) ignore the kwarg and run at their default.
  - `server_args` -- per-model llama-server overrides (e.g. `-c 8192` for 27B, or
    `--spec-type draft-mtp --spec-draft-n-max 2 -np 1` for the Qwen MTP runs -- all Qwen
    use MTP; the non-MTP A/B variant was dropped after MTP strictly dominated)
- `DEFAULT_SERVER_ARGS` in `benchmark.py` applies to every server start:
  `-ngl 99 -fa on -ub 1024 -c 16384`. KV cache stays at the f16 default (NOT q8_0):
  on 32 GB everything fits, and f16 KV is ~1.7x faster decode than q8_0 on this M5
  (llama-bench Qwen3.6-27B: 6.32 vs 3.72 tg t/s). Quantized K on Metal is costly.
  q8_0 KV was a 16 GB-machine memory hack -- do not re-add it.
- llama-server binary: `/opt/homebrew/bin/llama-server`
- `REQUEST_TIMEOUT = 120` -- thinking models loop on translation prompts; fail fast
- `DEFAULT_N_RUNS = 3` -- each prompt sampled this many times to average out temperature

## Test set

12 text prompts (discriminating core) across 4 categories: math (3), reasoning (4),
coding (3, executed), structured (2). Every config is scored on the same prompts
(`/36` at n=3). Trimmed from the original 16 -- trivial prompts that every model passed
(math_div, math_percent, logic_syllogism_yes, code_total, both translations) and the
brittle substring `summarize` were dropped (no signal, ceiling). Vision (3 chart-OCR
prompts) was removed too: it was supported unevenly across the model set (text-only for
Qwen-MTP / Phi / GLM / LFM / Mellum, and the Gemma 4 12B QAT mmproj fails to load), and
the mmproj path was a recurring source of server-start failures. The `structured`
category (JSON extraction + strict-format output) probes instruction-following /
function-calling -- the strength of agentic models (Ministral / GLM / Qwen3.6) that the
reasoning core alone misses. Verifiers (no LLM judge -- all mechanical):

- `v_number(expected, tol)` -- finds any decimal in answer matching expected within tolerance
- `v_yes_no(want_yes)` -- first yes/no token must match (catches "yes, but actually no")
- `v_regex(pattern)` -- regex search (used by `format_primes` for strict comma-list output)
- `v_python_exec(test_cases)` -- extracts Python from `\`\`\`python\`\`\`` block, runs it
  in a subprocess, asserts each `(call_expr, expected_value)` returns expected. Expected
  values are embedded via `repr()` (NOT `json.dumps`, which turns `True`->`true` -> NameError)
- `v_json(expected)` -- parses the first `{...}` span (tolerates a ```\`\`\`json``` fence or
  prose), checks each key; numbers compare by value, strings case-insensitively

`_strip_think(text)` removes `<think>...</think>` blocks before verification.

**Per-category thinking:** `_thinks(cfg, prompt)` gates thinking to
`THINKING_CATEGORIES` (math/reasoning/coding). `structured` is deliberately excluded --
thinking on JSON/strict-format tasks wastes tokens and can break the format -- so the
gate is meaningful: `-think` configs run the structured prompts direct.

**Fail classification:** `fail_kind` splits failures into `wrong` / `timeout` /
`empty` so the summary table never conflates "too slow to finish" with "wrong answer".
Speed (tok/s) from a long suite run is thermally throttled -- use `llama-bench` on a
cool machine for true peak decode speed; the suite's tok/s is for relative A/Bs.

**Evaluating accuracy-affecting toggles (think/no-think, sampling): run BOTH variants and
read per-category, never judge from the aggregate.** Both Gemma 4 and Qwen run a
think/nothink pair for exactly this reason. A mistake made here: "Gemma thinking only
slows it, no accuracy gain" was concluded from an aggregate (35 vs 36) compared against a
non-comparable older prompt set; the per-category data actually showed thinking is worth
+6..+9 on dense small/mid Gemma (it rescues math_modular/multistep and reasoning). The
aggregate hid it because `structured` is at ceiling for everyone and dilutes the signal.

## Result files

- `results/benchmark.json` -- aggregated raw results (latest run, all models)
- `results/benchmark.<model-name>.json` -- per-model snapshot (saved after each model
  finishes; safe against mid-run crashes/sleep)
- `results/RESULTS.md` -- formatted summary table
- `results/COMPARISON.md` -- cross-run comparison table

## Known issues

- llama-server's `-hf` resolver hangs on some Qwen repos even when files are cached.
  We always start with `-m <local_path>` discovered under `~/.cache/huggingface/hub/`.
- Mellum2 needs a recent llama.cpp: the `mellum` architecture landed in PR #23966
  (merged 2026-06-02, build ~9580+). Older builds fail to start its server with
  `unknown model architecture: 'mellum'`. `brew upgrade llama.cpp` if you hit this.
- Qwen3 thinking-mode loops on trivial prompts (translations, "reply with one word")
  and overflows max_tokens or hits REQUEST_TIMEOUT. Fix: use no-think mode for short
  factual queries; thinking only helps on math/word-problems/code.
- Stale `python3.1` processes can hold port 8080 after a previous llama-server crashes.
  Check `lsof -i :8080` before starting a new run.
- Do not run a benchmark concurrently with large model downloads. A ~17 GB model in the
  GPU working set plus a multi-GB download piling on memory pressure gets llama-server
  killed by macOS jetsam mid-run (the log cuts off with no traceback). Finish downloads
  first, then start the run.

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
