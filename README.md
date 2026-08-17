# small-llm-testing

Benchmark small LLMs locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) on Apple Silicon.

## Quick model choice

These are the latest measured results for the curated routine set. Score is mechanical
accuracy on the 12-prompt suite (`/36`, three samples per prompt). `tok/s` measures
generation on long responses; suite time also captures how much reasoning each model
emits, so use both when choosing an interactive model.

<!-- BEGIN GENERATED QUICK CHOICE -->
Measured 2026-08-17 on Apple M5, 32 GB, with f16 KV.

| Model | Quant | Mode | Score | Suite time | tok/s | Choose it for |
|---|---|---|---:|---:|---:|---|
| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) | Q8_0 + MTP | think | 36/36 | 267s | 45.0 | Compact reasoning |
| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) | Q8_0 + MTP | direct | 27/36 | 57s | 44.8 | Maximum compact-model throughput |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) | UD-Q4_K_M + MTP | think | 36/36 | 489s | 20.4 | Fast MoE reasoning |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) | UD-Q4_K_M + MTP | direct | 35/36 | 44s | 21.3 | Low-latency near-perfect answers |
| [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF) | Q8_0 | native | 36/36 | 195s | 29.8 | Small active-parameter MoE |
| [Mellum2-12B-A2.5B](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M) | Q4_K_M | native think | 36/36 | 208s | 26.9 | Single-config coding and reasoning |
<!-- END GENERATED QUICK CHOICE -->

See the [full comparison](results/COMPARISON.md) for every measured configuration and
the [raw benchmark data](results/benchmark.json) for reproducibility. Long sequential
runs thermally throttle this Mac, so suite `tok/s` is best for relative comparison;
measure peak decode speed with `llama-bench` on a cool machine. The 2026-08-09 run
overlapped other workloads, especially for the final challengers, so its speed results
are conservative; mechanical accuracy scores are unaffected.

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
| Current challenger recheck | Qwen3.8-27B, Nemotron 3.5 Lightning, Muse Glimmer 30B, North Mini Code, Nanbeige4.2-3B, LFM2.5-2.6B | Rerun cleanly, then use agentic tests where the text core is insufficient |
| Separate multimodal track | Fara1.5-4B | Requires screenshots, browser actions, and irreversible-action checks |
| Retired from reruns | Gemma E4B, 12B, 31B; Qwen 3.5 and 3.6; Ministral 3; GLM-4.7-Flash; Granite 4.1; OLMo 3.1; Ornith 9B/35B; Agents-A1 4B | Duplicated a stronger speed/accuracy point, scored poorly, or consumed too much time for a text-only result |
| Recheck only after runtime fixes | Laguna-XS-2.1 | Metal overflow produced mostly empty output; upstream fix required |
| Runtime-incompatible | Bonsai 27B, ZAYA1-8B | Require a custom runtime rather than the common upstream llama.cpp build |
| Too slow or obsolete | Phi-4-Reasoning 15B, Phi-4-mini | Poor local latency or no longer a useful generation comparison |

New models enter as one challenger at a time. They join the routine set only when the
same local `/36` run adds a useful Pareto point or a capability the existing text core
does not measure.

### Latest model search

The latest search checked recent official releases against the machine's working-set
limit, upstream llama.cpp support, and the vendor's recommended inference settings:

| Model | Decision |
|-------|----------|
| [LFM2.5-2.6B](https://huggingface.co/LiquidAI/LFM2.5-2.6B) | Accurate but too verbose and slow to add a routine Pareto point. Keep as a historical challenger; see the [generated comparison](results/COMPARISON.md) and [verified preset](docs/configuration.md#lfm25-26b). |
| [Nanbeige4.2-3B](https://huggingface.co/Nanbeige/Nanbeige4.2-3B) | Thinking is accurate but impractically slow; direct mode loses too much accuracy. Move to the agentic track; see the [generated comparison](results/COMPARISON.md) and [verified presets](docs/configuration.md#nanbeige42-3b). |
| [Fara1.5-4B](https://huggingface.co/microsoft/Fara1.5-4B) | Upstream llama.cpp passed a safe synthetic browser smoke, but this is not an end-to-end reliability result. Evaluate through the official agent harness; see the [runtime and preset record](docs/configuration.md#fara15-4b). |
| [North Mini Code 1.0](https://huggingface.co/blog/CohereLabs/introducing-north-mini-code) | Measured locally. The 30B-A3B MoE loaded with upstream llama.cpp from the 19.2 GB `UD-Q4_K_M` GGUF and passed 36/36 in 328 seconds. It is accurate but does not beat Mellum2 on this text core, so it moves to the agentic track where its tool-use training can be measured. |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Added as a current dense challenger in think and direct modes. The text suite uses Unsloth's 17.1 GB `Q4_K_M` without the optional vision projector; the preset is prepared but has not been loaded or benchmarked locally. |
| [Muse Glimmer 30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) | Added as a current challenger using the 15.9 GB `UD-Q4_K_XL` GGUF and its quantized DFlash drafter. Run the text core first, then evaluate its agentic and multimodal claims separately. |
| [Nemotron 3.5 Lightning 30B-A3B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) | Added as a current challenger. The normal 25.48 GB `Q4_K_M` exceeds this Mac's Metal working-set ceiling, so the local preset uses the 19.82 GB `Q3_K_M` GGUF with embedded MTP and records the quantization caveat. |
| [Laguna S 2.1](https://huggingface.co/poolside/Laguna-S-2.1) | Do not download on this machine. The official 118B-A8B model's smallest published upstream GGUF is 96 GB, far beyond the working set. |
| [MiMo V2.5](https://huggingface.co/XiaomiMiMo/MiMo-V2.5) | Exclude from local runs. The official model is 310B-A15B and its deployment guidance targets multi-GPU vLLM or SGLang rather than this memory class. |

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

Muse Glimmer requires a build containing
[PR #26841](https://github.com/ggml-org/llama.cpp/pull/26841), merged 2026-08-10.
Homebrew stable build 10330 predates that merge and fails with
`unknown model architecture: 'muse-glimmer'`; use a newer stable build or `--HEAD`.

Nemotron 3.5 Lightning GGUFs require llama.cpp build 10362 or newer. The current
Bartowski files were produced with that release and include their MTP layers.

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
    ('LiquidAI/LFM2.5-2.6B-GGUF', ['LFM2.5-2.6B-Q8_0.gguf']),
    ('mradermacher/Nanbeige4.2-3B-GGUF', ['Nanbeige4.2-3B.Q8_0.gguf']),
    ('bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF', ['NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q3_K_M.gguf']),
    ('unsloth/Muse-Glimmer-30B-GGUF', ['Muse-Glimmer-30B-UD-Q4_K_XL.gguf', 'dflash-kquant.gguf']),
    ('unsloth/North-Mini-Code-1.0-GGUF', ['North-Mini-Code-1.0-UD-Q4_K_M.gguf']),
]:
    for f in files:
        hf_hub_download(repo, f)
# Pin the newly prepared Qwen artifact to the exact revision used by benchmark.py.
hf_hub_download(
    'unsloth/Qwen3.8-27B-GGUF',
    'Qwen3.8-27B-Q4_K_M.gguf',
    revision='fdd03b8bbd279c1694563650e79d85a2373d9934',
)
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

# Run all 14 current text configurations
uv run python benchmark.py --full-sweep

# If port 8080 is taken (e.g. another dev server), run on the next free port:
uv run python benchmark.py --port 8081

# Run one model's configs (substring match -- e.g. both gemma-4-e2b modes)
uv run python benchmark.py --model gemma-4-e2b

# An explicit filter searches routine, challenger, and current agentic text sets
uv run python benchmark.py --model nanbeige

# Run only thinking configs
uv run python benchmark.py --model -think

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

For an unattended low-priority remeasurement of all 14 current text configurations:

```bash
nohup nice -n 10 caffeinate -dimu uv run python benchmark.py \
  --full-sweep --port 8081 > /tmp/small-llm-full-sweep.log 2>&1 &
disown
```

This covers the six-config routine, LFM2.5-2.6B, both Nanbeige4.2-3B modes, both
Qwen3.8-27B modes, Nemotron, Muse Glimmer, and North Mini Code. The 25 dominated,
weak, or text-inappropriate historical configurations are retired from reruns. Before
starting, the harness verifies every required GGUF and companion MTP or DFlash head and
exits with status 2 when an asset is missing. Outside a full sweep, absent main weights
may still be skipped, but a downloaded config with a missing companion aborts instead of
silently running a different preset. Completed configs are saved only to their per-model
snapshots; the canonical aggregate is replaced only after all 14 configs finish, so a
server failure cannot publish a partial comparison.

Do not start Fara1.5-4B with this command. It is the separate 15th configuration to rerun,
but it is a multimodal browser agent with a separate screenshot/action evaluation path,
not a member of the text `/36` suite.

After each model the bench writes `results/benchmark.<model>.json` so a crash
mid-run does not lose prior results. Outside a full sweep, a model whose server never
comes up (unsupported architecture, OOM, bad file) is logged and **skipped** rather than
crashing the whole run.

## Test set (12 text prompts, discriminating core)

Each prompt is run `n=3` times; sampled models expose run-to-run variance, while an
officially deterministic preset repeats the same decode. Every config is scored on the
same prompts (`/36` at n=3). Trimmed from the original 16 to a
**discriminating core**: prompts that every model passed (simple division/percent, the
easy syllogism, `total()` sum, the two translations) and the brittle substring-matched
`summarize` were dropped. What remains actually separates models:

| Category | Prompts | Verifier type |
|----------|---------|---------------|
| math | math_mul (23x17), math_multistep ((45+17)*3-28), math_modular (2^10 mod 1000) | numeric with tolerance |
| reasoning | word_speed (multi-step), word_age (algebra), logic_syllogism_no (real-world override trap), logic_negation | numeric / yes-no first-token |
| coding | code_fizzbuzz, code_palindrome, code_reverse_words | **executes the code** against test cases via subprocess |
| structured | json_person (extract name+age to JSON), format_primes (strict comma-list) | parsed JSON (`v_json`) / strict regex |

The `structured` category probes **instruction-following / function-calling**, a
dimension that a pure reasoning core misses.
All verification is mechanical (no LLM judge): numbers, yes/no, regex, executed code, and
parsed JSON.

The 3 chart-OCR **vision** prompts were removed earlier: vision was supported unevenly
across the historical set, and the `--mmproj` path was a recurring source of
server-start failures. The suite is uniformly text.

**Per-category thinking.** A `-think` config enables thinking only for
`math`/`reasoning`/`coding` (`THINKING_CATEGORIES` in `benchmark.py`). `structured` is
deliberately excluded -- thinking on JSON/strict-format tasks wastes tokens and can break
the format -- so `-think` configs run those prompts direct.

## Sampling parameters

Each model uses parameters verified against its official model card; see the
[complete preset record](docs/configuration.md#full-sweep-presets). `min_p=0` is pinned
on every request (server default may clip the tail).

| Model | Temperature | top_p | top_k | presence / repetition penalty | Source |
|---|---|---|---|---|---|
| Gemma 4 | 1.0 | 0.95 | 64 | - | [Gemma cards](https://ai.google.dev/gemma/docs/core) |
| LFM2.5-8B-A1B | 0.2 | 1.0 | 80 | repetition 1.05 | [official model card](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) |
| Mellum2-12B | 0.6 | 0.95 | 20 | - | [official model card](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking) |
| Qwen3.8-27B think | 1.0 | 0.95 | 20 | - | [official model card](https://huggingface.co/Qwen/Qwen3.8-27B) |
| Qwen3.8-27B direct | 0.7 | 0.8 | 20 | presence 1.5 | [official model card](https://huggingface.co/Qwen/Qwen3.8-27B) |

The exact researched presets for LFM2.5-2.6B, Nanbeige4.2-3B, and Fara1.5-4B,
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
-ngl 99 -fa on -ub 1024 -c 16384
```

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

The curated models use the default `-c 16384`.

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
- **The `structured` dimension is at ceiling -- every config scores 6/6.** JSON extraction
  and strict comma-list output are trivial for nearly every model, so the category adds a
  flat +6 to most without separating them. To make it discriminating it needs harder
  tasks (nested objects, conditional extraction, format traps).
- **f16 KV cache, not q8_0.** On 32 GB the f16 default fits every model and decodes
  ~1.7x faster than the old q8_0 KV hack (llama-bench, 27B). Quantized K on Metal is costly.
- **Speed numbers are throttling-sensitive.** Long suite runs throttle thermally; treat
  the suite's tok/s as relative and measure peak with `llama-bench` on a cool machine.

## Results

See the [full comparison](results/COMPARISON.md), [per-prompt results](results/RESULTS.md),
and [raw benchmark data](results/benchmark.json). Run `uv run python make_comparison.py`
after a complete benchmark to refresh the comparison and README quick-choice table.

**Reading the numbers:**

- **Fails are split `wrong/timeout/empty`.** A timeout means the answer ran past
  `REQUEST_TIMEOUT` (currently 300s) -- too slow to finish, not a wrong answer. This matters for
  big think-mode configs: e.g. 27B-think scores low mostly on timeouts (long reasoning
  traces at a few tok/s), which is a speed limit, not a reasoning failure.
- **Speed vs accuracy are separate concerns.** Absolute `tok/s` from a long full-suite
  run is depressed by thermal throttling that accumulates over hours (early configs run
  cooler/faster than late ones). For true peak decode speed, measure one model on a cool
  machine with `llama-bench`, not the tail of a multi-hour suite. The suite's tok/s is
  fine for *relative* comparisons measured back-to-back (think/no-think).
- **think vs no-think is compared on the same MTP model.** Both modes run the same
  12-prompt core (`/36` at n=3) from the same MTP GGUF, so any pass-total difference is a
  real mode effect, not a prompt-set or build artifact.
