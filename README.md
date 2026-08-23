# small-llm-testing

Benchmark small LLMs locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) on Apple Silicon.

## Quick model choice

These are the latest measured results for the curated routine set. Score is mechanical
accuracy on the 22-prompt suite (`/66`, three samples per prompt). `tok/s` measures
generation on long responses; suite time also captures how much reasoning each model
emits, so use both when choosing an interactive model.

<!-- BEGIN GENERATED QUICK CHOICE -->
Measured 2026-08-21 on Apple M5, 32 GB, with f16 KV.

| Model | Quant | Mode | Score | Suite time | tok/s | Choose it for |
|---|---|---|---:|---:|---:|---|
| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) | Q8_0 + MTP | think | 65/66 | 765s | 29.9 | Compact reasoning |
| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) | Q8_0 + MTP | direct | 47/66 | 103s | 30.1 | Maximum compact-model throughput |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) | UD-Q4_K_M + MTP | think | 63/66 | 1758s | 17.5 | Fast MoE reasoning |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) | UD-Q4_K_M + MTP | direct | 64/66 | 88s | 19.7 | Low-latency near-perfect answers |
| [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF) | Q8_0 | native | 63/66 | 706s | 29.9 | Small active-parameter MoE |
| [Mellum2-12B-A2.5B](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M) | Q4_K_M | native think | 66/66 | 473s | 26.8 | Background wiki-audit agent |
<!-- END GENERATED QUICK CHOICE -->

See the [full comparison](results/COMPARISON.md) for every measured configuration and
the [raw benchmark data](results/benchmark.json) for reproducibility. Long sequential
runs thermally throttle this Mac, so suite `tok/s` is best for relative comparison;
measure peak decode speed with `llama-bench` on a cool machine.

## Default routine set

The six configurations in the quick-choice table are the default run. Gemma runs in
both thinking and direct mode, with its separate `mtp-*.gguf` draft head auto-attached
for lossless speculative decoding. LFM and Mellum each run once using their documented
default behavior.

### Future benchmark policy

The broad 2026-07-29 sweep remains in git history for provenance. Models that no longer
help choose a local model are excluded from current reruns:

| Status | Models | Reason |
|--------|--------|--------|
| Current challenger recheck | Nemotron 3.5 Lightning | Its 2026-08-18 fails were 300s request timeouts, not wrong answers; rerun on the corrected budget (derived article cap, `REQUEST_TIMEOUT` 1800s) |
| Separate multimodal track | Fara1.5-4B | Requires screenshots, browser actions, and irreversible-action checks |
| Agentic text only | North Mini Code | Accurate on the old text core, does not beat Mellum2; keep for tool-use measurement |
| Retired from reruns | Gemma E4B, 12B, 31B; Qwen 3.5 and 3.6; Ministral 3; GLM-4.7-Flash; Granite 4.1; OLMo 3.1; Ornith 9B/35B; Agents-A1 4B; LFM2.5-2.6B; Nanbeige4.2-3B; Muse Glimmer 30B | Duplicated a stronger speed/accuracy point, or consumed too much time for a text-only result |
| Recheck only after runtime fixes | Laguna-XS-2.1; Ling-3.0-tiny | Laguna: Metal overflow. Ling: GGUF cached and loaded on llama.cpp 10544, but PATH `llama-server` is still `llama-cpp-bundled` 10380 |
| Runtime-incompatible | Bonsai 27B, ZAYA1-8B | Require a custom runtime rather than the common upstream llama.cpp build |
| Too slow or obsolete | Phi-4-Reasoning 15B, Phi-4-mini | Poor local latency or no longer a useful generation comparison |

New models enter as one challenger at a time. They join the routine set only when the
same local complete-suite run adds a useful Pareto point or a capability the existing
text core does not measure.

### Latest model search

The 2026-08-20 search used the Hugging Face API against the machine's working-set
limit, upstream llama.cpp support, and the vendor's recommended inference settings:

| Model | Decision |
|-------|----------|
| [LFM2.5-2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B) | Accurate on the agent-scenario suite but dominated by Gemma 4 E2B thinking. Retired; see the [verified preset](docs/configuration.md#lfm25-26b). |
| [Nanbeige4.2-3B](https://huggingface.co/Nanbeige/Nanbeige4.2-3B) | Thinking timed out on consistency and long-context; direct mode missed contradiction pairs. Retired; see the [verified presets](docs/configuration.md#nanbeige42-3b). |
| [Fara1.5-4B](https://huggingface.co/microsoft/Fara1.5-4B) | Upstream llama.cpp passed a safe synthetic browser smoke, but this is not an end-to-end reliability result. Evaluate through the official agent harness; see the [runtime and preset record](docs/configuration.md#fara15-4b). |
| [North Mini Code 1.0](https://huggingface.co/blog/CohereLabs/introducing-north-mini-code) | Accurate on the old text core, does not beat Mellum2. Stays on the agentic track. |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | **Retired 2026-08-23, on speed.** Sampling was never the problem; it decodes at 1.5-3.3 tok/s here, so one article answer runs past an hour. Neither a newer llama.cpp build nor a DFlash2 draft brings it into range, and the slowness is llama.cpp's, not the model's (MLX runs it at Qwen3.6 speed). Preset and measurements kept in the [preset](docs/configuration.md#qwen38-27b). |
| [Muse Glimmer 30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) | Dominated on the 12-prompt core; 22-prompt rerun never finished. Retired; see the [verified preset](docs/configuration.md#muse-glimmer-30b). |
| [Nemotron 3.5 Lightning 30B-A3B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) | Keep as challenger. Official sampling matches; local `Q3_K_M` is the memory-safe quant. Its fails have always been budget artifacts: 300s timeouts in the 2026-08-18 snapshot, then six `empty` results in the 2026-08-21 sweep, each exactly 4,096 tokens cut mid-thought. See the [preset](docs/configuration.md#nemotron-35-lightning-30b-a3b). |
| [Ling-3.0-tiny](https://huggingface.co/inclusionAI/Ling-3.0-tiny) | Next challenger once PATH llama-server includes BailingMoE3. 7.9B/1.3B, MacBook-oriented, Q8_0 cached and smoke-tested on build 10544. See the [preset](docs/configuration.md#ling-30-tiny). |
| [Ornith-1.5-9B](https://huggingface.co/ornith-ai/Ornith-1.5-9B) | Official GGUF, 9.53 GB Q8_0. Successor to retired Ornith 1.0. One-at-a-time after Ling. |
| [LFM2.5-1.2B-Thinking](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Thinking) | Smaller than the already-dominated 2.6B. Skip. |
| [Ling-3.0-flash](https://huggingface.co/inclusionAI/Ling-3.0-flash) | 124B-A5.1B, far beyond the working set. |
| [Laguna S 2.1](https://huggingface.co/poolside/Laguna-S-2.1) | Do not download on this machine. The official 118B-A8B model's smallest published upstream GGUF is 96 GB, far beyond the working set. |
| [MiMo V2.5](https://huggingface.co/XiaomiMiMo/MiMo-V2.5) | Exclude from local runs. The official model is 310B-A15B and its deployment guidance targets multi-GPU vLLM or SGLang rather than this memory class. |
| [GLM-5.2](https://huggingface.co/zai-org/GLM-5.2), [MiniMax-M2.7](https://huggingface.co/MiniMaxAI/MiniMax-M2.7), [Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | Flagship sizes, not this memory class. |

## Hardware

- Apple M5, 32 GB unified memory, macOS Tahoe.
- Apple GPU `recommendedMaxWorkingSetSize` is ~24.96 GB (26800603136 bytes) on this
  machine, measured via Metal `MTLCreateSystemDefaultDevice().recommendedMaxWorkingSetSize`.
  This is the practical ceiling for model weights + KV cache + compute buffers.

## Prerequisites

```bash
brew install llama.cpp
```

Use a recent build (≥ 9580): the `mellum` architecture used by Mellum2 was added in
[PR #23966](https://github.com/ggml-org/llama.cpp/pull/23966) (merged 2026-06-02). Older
builds fail to start its server with `unknown model architecture: 'mellum'`.

Ling-3.0-tiny needs a build containing
[PR #26608](https://github.com/ggml-org/llama.cpp/pull/26608) (BailingMoE3, merged
2026-08-17, build 10544+). PATH `llama-server` on this machine is still
`llama-cpp-bundled` 10380 and cannot load it. See [troubleshooting](docs/troubleshooting.md).

## Download models first

Models are large. Pre-download with `huggingface_hub` to avoid
the bench timing out during cold-start:

```bash
uv run --with huggingface_hub python -c "
from huggingface_hub import hf_hub_download
# Gemma pulls a main GGUF plus the separate MTP draft head the harness auto-attaches.
for repo, files in [
    ('unsloth/gemma-4-E2B-it-GGUF', ['gemma-4-E2B-it-Q8_0.gguf', 'mtp-gemma-4-E2B-it.gguf']),
    ('unsloth/gemma-4-26B-A4B-it-GGUF', ['gemma-4-26B-A4B-it-UD-Q4_K_M.gguf', 'mtp-gemma-4-26B-A4B-it.gguf']),
    ('LiquidAI/LFM2.5-8B-A1B-GGUF', ['LFM2.5-8B-A1B-Q8_0.gguf']),
    ('JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M', ['Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf']),
    ('bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF', ['NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q3_K_M.gguf']),
    ('unsloth/North-Mini-Code-1.0-GGUF', ['North-Mini-Code-1.0-UD-Q4_K_M.gguf']),
]:
    for f in files:
        hf_hub_download(repo, f)
"
```

llama-server's built-in `-hf` resolver has hung on some repositories even when files
were cached, so the bench loads via local `-m` paths it discovers under
`~/.cache/huggingface/hub/`.

## Usage

```bash
# Install project dependencies
uv sync

# Run the curated routine benchmark (n=3 samples per prompt)
uv run python benchmark.py

# Run the routine set plus all current text challengers
uv run python benchmark.py --include-challengers

# Run all 10 current text configurations
uv run python benchmark.py --full-sweep

# If port 8080 is taken (e.g. another dev server), run on the next free port:
uv run python benchmark.py --port 8081

# Run one model's configs (substring match -- e.g. both gemma-4-e2b modes)
uv run python benchmark.py --model gemma-4-e2b

# An explicit filter searches routine, challenger, and current agentic text sets
uv run python benchmark.py --model north-mini

# Run only thinking configs
uv run python benchmark.py --model -think

# Reliability recheck of the agent-report categories at higher sample count.
# Filtered runs write tagged snapshots (results/benchmark.<model>.<categories>.json)
# and never replace the canonical benchmark.json / RESULTS.md.
uv run python benchmark.py --model gemma-4-e2b --category structured,consistency -n 20

# Smaller sample size for a quick smoke test
uv run python benchmark.py -n 1
```

### Avoiding sleep mid-run

Long thinking-mode runs can take 30-60 minutes per model. Wrap with
`caffeinate -dimu` and `nohup` so a closed lid doesn't kill the process:

```bash
nohup caffeinate -dimu uv run python benchmark.py > /tmp/bench.log 2>&1 &
disown
```

For an unattended low-priority remeasurement of all 10 current text configurations:

```bash
nohup nice -n 10 caffeinate -dimu uv run python benchmark.py \
  --full-sweep --port 8081 > /tmp/small-llm-full-sweep.log 2>&1 &
disown
```

This covers the six-config routine, Nemotron, and North Mini Code. Previous dominated challengers and the 25 historical configurations are retired
from reruns. Before starting, the harness verifies every required GGUF and companion
MTP head and exits with status 2 when an asset is missing. Outside a full sweep, absent
main weights may still be skipped, but a downloaded config with a missing companion
aborts instead of silently running a different preset. Completed configs are saved only
to their per-model snapshots; the canonical aggregate is replaced only after all 10
configs finish, so a
server failure cannot publish a partial comparison.

Do not start Fara1.5-4B with this command. It is a multimodal browser agent with a
separate screenshot/action evaluation path, not a member of the text suite.

After each model the bench writes `results/benchmark.<model>.json` so a crash
mid-run does not lose prior results. Outside a full sweep, a model whose server never
comes up (unsupported architecture, OOM, bad file) is logged and **skipped** rather than
crashing the whole run.

## Test set (22 text prompts, discriminating core plus agent scenario)

Each prompt is run `n=3` times; sampled models expose run-to-run variance, while an
officially deterministic preset repeats the same decode. Every config is scored on the
same prompts (`/66` at n=3). The original core was trimmed from 16 prompts to a
**discriminating set**: prompts that every model passed (simple division/percent, the
easy syllogism, `total()` sum, the two translations) and the brittle substring-matched
`summarize` were dropped. What remains separates models:

| Category | Prompts | Verifier type |
|----------|---------|---------------|
| math | math_mul (23x17), math_multistep ((45+17)*3-28), math_modular (2^10 mod 1000) | numeric with tolerance |
| reasoning | word_speed (multi-step), word_age (algebra), logic_syllogism_no (real-world override trap), logic_negation | numeric / yes-no first-token |
| coding | code_fizzbuzz, code_palindrome, code_reverse_words | **executes the code** against test cases via subprocess |
| structured | json_person (extract name+age to JSON), json_fields (string+int+bool+array with distractor year), format_primes (strict comma-list) | parsed JSON (`v_json`) / strict regex |
| consistency | cons_date_shift, cons_digit_swap, cons_dead_action, cons_unit_equivalent, cons_complementary, cons_relative_rank | yes-no first-token; fictional entities, balanced 3 contradictions / 3 consistent pairs |
| longcontext | longctx_inconsistent, longctx_consistent, longctx_needle | yes-no / numeric over a ~2.5k-token generated encyclopedia article with one planted (or no) contradiction |

The `structured` category probes **instruction-following / function-calling**, a
dimension that a pure reasoning core misses. `consistency` and `longcontext` model the
**background data-auditing agent** (does a model notice that two wiki-style statements
cannot both be true, over a statement pair or a whole article; see
[benchmark design](docs/benchmark-design.md#agent-scenario-categories)).
All verification is mechanical (no LLM judge): numbers, yes/no, regex, executed code, and
parsed JSON.

The 3 chart-OCR **vision** prompts were removed earlier: vision was supported unevenly
across the historical set, and the `--mmproj` path was a recurring source of
server-start failures. The suite is uniformly text.

**Per-category thinking.** A `-think` config enables thinking only for
`math`/`reasoning`/`coding`/`consistency`/`longcontext` (`THINKING_CATEGORIES` in
`benchmark.py`). `structured` is deliberately excluded -- thinking on JSON/strict-format
tasks wastes tokens and can break the format -- so `-think` configs run those prompts
direct. Long-context prompts are marked `article_sized` and derive their generation cap
per model as `n_ctx - ARTICLE_PROMPT_RESERVE` (12,288 at the default context). It was a
flat 4,096 until 2026-08-21, when every `empty` result in the sweep turned out to be
exactly 4,096 tokens cut mid-thought rather than a model failing to answer.

## Sampling parameters

Each model uses parameters verified against its official model card; see the
[complete preset record](docs/configuration.md#full-sweep-presets). `min_p=0` is pinned
on every request (server default may clip the tail).

| Model | Temperature | top_p | top_k | presence / repetition penalty | Source |
|---|---|---|---|---|---|
| Gemma 4 | 1.0 | 0.95 | 64 | - | [Gemma cards](https://ai.google.dev/gemma/docs/core) |
| LFM2.5-8B-A1B | 0.2 | 1.0 | 80 | repetition 1.05 | [official model card](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) |
| Mellum2-12B | 0.6 | 0.95 | 20 | - | [official model card](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking) |

The exact researched presets for Qwen3.8-27B, LFM2.5-2.6B, Nanbeige4.2-3B, and Fara1.5-4B,
including context, output, thinking, tool-template, and scenario controls, are recorded
in [configuration notes](docs/configuration.md#researched-challenger-presets).

Notes:
- **repetition_penalty** is LFM2.5's documented anti-loop knob and is sent as llama.cpp
  `repeat_penalty`.
- **Gemma 4 has a thinking toggle** (`enable_thinking`, unlike Gemma 3), so it runs a
  think/nothink pair. `enable_thinking` is sent on every request; toggle-less models
  ignore it.

## Server flags applied to all models

```
-ngl 99 -fa on -ub 1024
```

Context comes from `ModelConfig.n_ctx` (default 16,384) rather than a shared flag, so one
model's memory bound cannot size the whole fleet's answer budget.

KV cache is left at the **f16 default**, not quantized. On the 32 GB machine every
model fits with f16 KV, and f16 is measurably faster than q8_0 KV. Measured on this M5
(llama-bench, Qwen3.6-27B Q4_K_M, build 9380):

| KV type (k/v) | tg128 (decode t/s) | pp256 (prompt t/s) |
|---|---|---|
| **f16 / f16** | **6.32** | **156** |
| f16 / q8_0 | 5.08 | 114 |
| q8_0 / q8_0 (old default) | 3.72 | 96 |
| q8_0 / f16 | 3.41 | 76 |

f16 KV is ~1.7x faster decode than the old `q8_0/q8_0` -- quantized K on Metal is
especially costly. `q8_0` KV was a 16 GB-machine memory hack and is no longer used.
`-fa on` stays (it helps with f16 KV too; it is only *required* when KV is quantized).

Do not read the 6.32 above as "what a 27B does here". It is Qwen3.6 on build 9380.
Qwen3.8-27B Q4_K_M on build 10380 measures 1.46 tok/s cold, and which of the two
differences explains the gap is unresolved -- see
[cold llama-bench](docs/hardware-notes.md#cold-llama-bench-2026-08-22-build-10380-m5-f16-kv).

The curated models use the default `n_ctx` of 16,384. North Mini Code ran at 8,192 until
2026-08-21; it is verified to load and serve at 16,384 on this M5 (24.96 GB working set).

Multi-token prediction: every Gemma run uses a separate `mtp-*.gguf` draft file that
`_start_server` auto-attaches via `--model-draft`. It enables MTP with `--spec-type draft-mtp
--spec-draft-n-max 2 -np 1`. It is lossless (verified byte-identical output) and runs
1.2-2.2x faster. `-np > 1` is not yet supported with MTP, so MTP runs are single-stream.

## Findings

Key dated verdicts are recorded here alongside the published generated results. Full
current numbers live in `results/COMPARISON.md`, regenerated after each run:

- **Current speed/accuracy leader: Mellum2-12B-A2.5B.** Small Gemma thinking configs
  also reach the accuracy ceiling, while Gemma 26B-A4B no-think is the fastest
  near-perfect direct configuration. See the generated comparison for current numbers.
- **Thinking is valuable only when the model can finish.** It consistently repairs
  math/reasoning failures in small Gemma and Qwen configs. The dense Qwen 27B instead
  repeatedly hit the request cap on coding, so its thinking and direct modes tied on
  total accuracy while thinking took far longer. Those failures are timeouts, not
  verifier-rejected code.
- **The new native reasoning models are accurate but slow.** Ornith 9B and Agents-A1 4B
  both reached the ceiling in the dated run but were much slower. GLM also reached the
  ceiling and was faster, while Mellum2 retained a large latency advantage.
- **MTP is the only Qwen decode mode now.** An earlier A/B kept a non-MTP variant; MTP
  strictly dominated (1.2-1.65x faster, same accuracy, and the speed pulls think-coding
  back under the timeout), so the non-MTP variants were dropped.
- **The `structured` dimension was at ceiling for the original two prompts -- every
  config scored 6/6.** JSON extraction and strict comma-list output were trivial for
  nearly every model. `json_fields` (2026-08-17) adds array, boolean-false, and
  distractor-year extraction; whether it separates models will show in the next
  complete run.
- **f16 KV cache, not q8_0.** On 32 GB the f16 default fits every model and decodes
  ~1.7x faster than the old q8_0 KV hack (llama-bench, 27B). Quantized K on Metal is costly.
- **Speed numbers are throttling-sensitive.** Long suite runs throttle thermally; treat
  the suite's tok/s as relative and measure peak with `llama-bench` on a cool machine.

## Results

See the [full comparison](results/COMPARISON.md), [per-prompt results](results/RESULTS.md),
and [raw benchmark data](results/benchmark.json). Run `uv run python make_comparison.py`
after a complete benchmark to refresh the comparison and README quick-choice table.

**Reading the numbers:**

- **Fails are split `wrong/timeout/empty/truncated`.** Only `wrong` is a model verdict:
  the attempt finished on its own and the verifier rejected it. A timeout means the answer
  ran past `REQUEST_TIMEOUT` (currently 1800s); `truncated` means the generation cap cut
  the model off mid-answer. Both are speed or budget limits, not reasoning failures, and
  they are why big think-mode configs score low.
- **`REQUEST_TIMEOUT` and the generation cap are one setting.** An attempt reaches its cap
  only if `REQUEST_TIMEOUT >= cap / decode tok/s`. Check that against the slowest config in
  a run before reading its long-context column as a model result.
- **Speed vs accuracy are separate concerns.** Absolute `tok/s` from a long full-suite
  run is depressed by thermal throttling that accumulates over hours (early configs run
  cooler/faster than late ones). For true peak decode speed, measure one model on a cool
  machine with `llama-bench`, not the tail of a multi-hour suite. The suite's tok/s is
  fine for *relative* comparisons measured back-to-back (think/no-think).
- **think vs no-think is compared on the same MTP model.** Both modes run the same
  prompt suite from the same MTP GGUF, so any pass-total difference is a real mode
  effect, not a prompt-set or build artifact. Compare think and direct on the same run.
