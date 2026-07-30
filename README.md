# small-llm-testing

Benchmark small LLMs locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) on Apple Silicon.

## Models

| Model | Parameters | Quant | Release | Announcement |
|-------|-----------|-------|---------|--------------|
| [Gemma 4 E2B](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF) | 2B effective | Q8_0 + MTP | 2026 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Gemma 4 E4B](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF) | 4B effective | Q4_K_M + MTP | 2026 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Qwen3.5-2B](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF) | 2B | Q8_0 | March 2026 | [Qwen3.5 release](https://qwenlm.github.io/blog/qwen3/) |
| [Qwen3.5-4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF) | 4B | Q8_0 | March 2026 | same |
| [Qwen3.5-9B](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF) | 9B | Q8_0 | March 2026 | same |
| [Gemma 4 12B](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF) | 12B dense | Q4_K_M + MTP (~6.6 GB) | 2026 | Google (Apache-2.0) |
| [Gemma 4 26B-A4B](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF) | 26B total / 4B active (MoE) | UD-Q4_K_M + MTP (~17 GB) | 2026 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Gemma 4 31B](https://huggingface.co/unsloth/gemma-4-31B-it-qat-GGUF) | 31B dense | QAT UD-Q4_K_XL + MTP (~17 GB) | 2026 | Google (Apache-2.0) |
| [Qwen 3.6 27B](https://huggingface.co/unsloth/Qwen3.6-27B-GGUF) | 27B dense | Q4_K_M (~16.8 GB) | 2026 | [Qwen3.6 release](https://qwenlm.github.io/blog/qwen3/) |
| [Qwen 3.6 35B-A3B](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF) | 35B total / 3B active (MoE) | UD-Q4_K_M + MTP (~21 GB) | 2026 | [Qwen3.6 release](https://qwenlm.github.io/blog/qwen3/) |
| [Ministral 3 8B](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF) | 8B | Q8_0 (~9 GB) | Dec 2025 | Mistral AI (Apache-2.0) |
| [Ministral 3 14B](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF) | 14B | Q4_K_M (~8.2 GB) | Dec 2025 | Mistral AI (Apache-2.0) |
| [GLM-4.7-Flash](https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF) | 30B-A3B MoE (3B active) | Q4_K_M (~18.3 GB) | 2026 | Zhipu (MIT) |
| [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF) | 8B total / 1.5B active (MoE) | Q8_0 (~9 GB) | 2026 | Liquid AI (lfm1.0) |
| [Mellum2-12B-A2.5B](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M) | 12B total / 2.5B active (MoE, coding) | Q4_K_M (~8.1 GB) | 2026 | JetBrains (Apache-2.0) |
| [Granite 4.1-8b](https://huggingface.co/ibm-granite/granite-4.1-8b-GGUF) | ~8B | Q8_0 (~9 GB) | 2026 | IBM (Apache-2.0) |
| [Ornith-1.0-35B](https://huggingface.co/SEBK4C/Ornith-1.0-35B-MTP-GGUF) | 35B total / ~3B active (MoE, coding) | Q4_K_M + MTP (~21.7 GB) | 2026 | DeepReinforce (MIT) |
| [Ornith-1.0-9B](https://huggingface.co/deepreinforce-ai/Ornith-1.0-9B-GGUF) | 9B dense (agentic coding) | Q8_0 (~9.8 GB) | June 2026 | DeepReinforce (MIT) |
| [Agents-A1-4B](https://huggingface.co/InternScience/Agents-A1-4B-Q8_0-GGUF) | 4B dense (agentic) | Q8_0 (~4.3 GB) | July 2026 | InternScience (Apache-2.0) |
| [OLMo 3.1 32B Instruct](https://huggingface.co/unsloth/Olmo-3.1-32B-Instruct-GGUF) | 32B dense | Q4_K_M (~19.5 GB) | 2026 | Allen AI (Apache-2.0) |

Qwen 3.5 covers the small tier (Qwen 3.6 ships large-only: 27B and 35B-A3B), so the
two generations do not overlap in size. Qwen3.5-0.8B is dropped -- too small to think
productively (it loops on trivial prompts and times out, a net loss vs no-think).

Each Qwen model runs **2 configs: `-mtp-think` and `-mtp-nothink`** -- thinking mode on
(better reasoning, much slower) vs off (fast direct), both loaded from the
[MTP GGUF](https://huggingface.co/unsloth/Qwen3.6-27B-MTP-GGUF) with multi-token prediction
(`--spec-type draft-mtp`). An earlier A/B kept a non-MTP variant of each; it was dropped
because MTP strictly dominated -- 1.2-1.65x faster decode at the same accuracy, and the
extra speed pulls most think-mode coding back under the request timeout. MTP heads ship for
the whole Qwen 3.5 / 3.6 line.

Gemma 4 (unlike Gemma 3) has an `enable_thinking` toggle, so each Gemma runs a
**think + nothink pair** -- the same think/nothink A/B as Qwen. Measured, thinking is
worth +3..+9 for Gemma (math_modular/multistep, reasoning) on every size except 26b-a4b
(ceiling either way), at higher wall time but no timeouts. Gemma is loaded from **Unsloth
GGUFs, which ship a separate `mtp-*.gguf` MTP draft head** that the harness auto-attaches
for lossless multi-token-prediction speculative decoding (measured 1.2-2.1x faster, e.g.
e2b-think 34 -> 73 tok/s, byte-identical output). Ornith 35B also runs a think + nothink
pair (it honors `enable_thinking`). Ornith 9B and Agents-A1 are native reasoning models
with no documented direct-mode toggle, so each runs once. The other families
(Ministral 3, GLM-4.7-Flash, LFM2.5, Mellum2, Granite 4.1, OLMo 3.1 Instruct) run one
config each with no MTP. GLM, LFM2.5, and Mellum reason by default; Ministral, Granite,
and OLMo are plain instruct. The suite is text-only (see Test set below).

### Memory class reference

The machine has a 32 GB unified-memory budget with a ~25 GB GPU working set (see
Hardware below). The largest configs -- Qwen 3.6 35B-A3B (~21 GB at `-c 8192`), GLM-4.7-Flash
and the ~17 GB Gemma 31B / 26B-A4B and Qwen 27B -- all fit. Excluded:

| Model | Status |
|-------|--------|
| Laguna-XS-2.1 33B | Excluded after measurement -- arch support works (llama.cpp >= 10090, PR #25165), but the Metal f16 overflow in its MoE down-projection makes it return EMPTY output for most prompts (2026-07-23 run: 21/36 empty think, 6/36 nothink). Fix is upstream PR #25442; re-add when it lands. |
| Bonsai 27B 1-bit / ternary | Excluded from the comparable suite -- its Q1_0/Q2_0 hybrid-attention kernels require the PrismML llama.cpp fork. The upstream Homebrew runtime used by every other result cannot load those custom quants. |
| Phi-4-Reasoning 15B | Excluded -- too slow (7.9 tok/s, most prompts timeout). Not a memory limit. |
| Phi-4-mini | Excluded 2026-07 -- released 2025-02, a generation older than the rest; weakest vendor GPQA of the set (25.2); greedy temp=0 makes n=3 sampling degenerate. Comparison no longer informative. |
| Zyphra ZAYA1-8B | Excluded -- hybrid-Mamba MoE, no working llama.cpp path (official deploy is a custom vLLM fork); text-only. |

`Gemma 4 26B-A4B` (~16.8 GB) runs at default ctx; `Qwen 3.6 27B` (~16.8 GB) uses
`-c 8192` for KV headroom. `Qwen3.5-9B` no longer needs the old `-c 8192` override --
on the ~25 GB working set it runs at default ctx (model + KV ~12.5 GB).

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

## Download models first

Models are large (1--10 GB each). Pre-download with `huggingface_hub` to avoid
the bench timing out during cold-start:

```bash
uv run --with huggingface_hub python -c "
from huggingface_hub import hf_hub_download
# Text-only suite. Gemma + Qwen pull a main GGUF plus its MTP draft head for speculative
# decoding (Gemma's draft is a separate mtp-*.gguf the harness auto-attaches; Qwen's is
# embedded in the -MTP GGUF).
for repo, files in [
    ('unsloth/gemma-4-E2B-it-GGUF', ['gemma-4-E2B-it-Q8_0.gguf', 'mtp-gemma-4-E2B-it.gguf']),
    ('unsloth/gemma-4-E4B-it-GGUF', ['gemma-4-E4B-it-Q4_K_M.gguf', 'mtp-gemma-4-E4B-it.gguf']),
    ('unsloth/gemma-4-12b-it-GGUF', ['gemma-4-12b-it-Q4_K_M.gguf', 'mtp-gemma-4-12b-it.gguf']),
    ('unsloth/gemma-4-26B-A4B-it-GGUF', ['gemma-4-26B-A4B-it-UD-Q4_K_M.gguf', 'mtp-gemma-4-26B-A4B-it.gguf']),
    ('unsloth/gemma-4-31B-it-qat-GGUF', ['gemma-4-31B-it-qat-UD-Q4_K_XL.gguf', 'mtp-gemma-4-31B-it.gguf']),
    # Qwen runs from the MTP GGUFs (multi-token prediction; non-MTP variants dropped).
    ('unsloth/Qwen3.5-2B-MTP-GGUF',  ['Qwen3.5-2B-Q8_0.gguf']),
    ('unsloth/Qwen3.5-4B-MTP-GGUF',  ['Qwen3.5-4B-Q8_0.gguf']),
    ('unsloth/Qwen3.5-9B-MTP-GGUF',  ['Qwen3.5-9B-Q8_0.gguf']),
    ('unsloth/Qwen3.6-27B-MTP-GGUF', ['Qwen3.6-27B-Q4_K_M.gguf']),
    ('unsloth/Qwen3.6-35B-A3B-MTP-GGUF', ['Qwen3.6-35B-A3B-UD-Q4_K_M.gguf']),
    # Other families.
    ('mistralai/Ministral-3-8B-Instruct-2512-GGUF',  ['Ministral-3-8B-Instruct-2512-Q8_0.gguf']),
    ('mistralai/Ministral-3-14B-Instruct-2512-GGUF', ['Ministral-3-14B-Instruct-2512-Q4_K_M.gguf']),
    ('unsloth/GLM-4.7-Flash-GGUF', ['GLM-4.7-Flash-Q4_K_M.gguf']),
    ('LiquidAI/LFM2.5-8B-A1B-GGUF', ['LFM2.5-8B-A1B-Q8_0.gguf']),
    ('JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M', ['Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf']),
    ('ibm-granite/granite-4.1-8b-GGUF', ['granite-4.1-8b-Q8_0.gguf']),
    ('deepreinforce-ai/Ornith-1.0-9B-GGUF', ['ornith-1.0-9b-Q8_0.gguf']),
    ('InternScience/Agents-A1-4B-Q8_0-GGUF', ['Agents-A1-4B-Q8_0.gguf']),
    ('unsloth/Olmo-3.1-32B-Instruct-GGUF', ['Olmo-3.1-32B-Instruct-Q4_K_M.gguf']),
]:
    for f in files:
        hf_hub_download(repo, f)
"
```

llama-server's built-in `-hf` resolver hangs on some Qwen repos even when files
are cached, so the bench loads via local `-m` paths it discovers under
`~/.cache/huggingface/hub/`.

## Usage

```bash
# Install project dependencies
uv sync

# Run full benchmark (n=3 samples per prompt; expect a multi-hour run)
uv run python benchmark.py

# If port 8080 is taken (e.g. another dev server), run on the next free port:
uv run python benchmark.py --port 8081

# Run one model's configs (substring match -- e.g. both gemma-4-e2b modes)
uv run python benchmark.py --model gemma-4-e2b

# Run only the thinking configs (Gemma + Qwen + Ornith)
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

After each model the bench writes `results/benchmark.<model>.json` so a crash
mid-run does not lose prior results. A model whose server never comes up (unsupported
architecture, OOM, bad file) is logged and **skipped** rather than crashing the whole run.

## Test set (12 text prompts, discriminating core)

Each prompt is sampled `n=3` times at temperature > 0; we report passes/n. Every config
is scored on the same prompts (`/36` at n=3). Trimmed from the original 16 to a
**discriminating core**: prompts that every model passed (simple division/percent, the
easy syllogism, `total()` sum, the two translations) and the brittle substring-matched
`summarize` were dropped. What remains actually separates models:

| Category | Prompts | Verifier type |
|----------|---------|---------------|
| math | math_mul (23x17), math_multistep ((45+17)*3-28), math_modular (2^10 mod 1000) | numeric with tolerance |
| reasoning | word_speed (multi-step), word_age (algebra), logic_syllogism_no (real-world override trap), logic_negation | numeric / yes-no first-token |
| coding | code_fizzbuzz, is_palindrome, reverse_words | **executes the code** against test cases via subprocess |
| structured | json_person (extract name+age to JSON), format_primes (strict comma-list) | parsed JSON (`v_json`) / strict regex |

The `structured` category probes **instruction-following / function-calling** -- the
strength of agentic models (Ministral / GLM / Qwen3.6) that a pure reasoning core misses.
All verification is mechanical (no LLM judge): numbers, yes/no, regex, executed code, and
parsed JSON.

The 3 chart-OCR **vision** prompts were removed earlier: vision was supported unevenly
across the set (text-only for Qwen-MTP / GLM / LFM / Mellum, and the Gemma 4 12B QAT
mmproj fails to load on this llama.cpp build), and the `--mmproj` path was a recurring
source of server-start failures. The suite is uniformly text.

**Per-category thinking.** A `-think` config enables thinking only for
`math`/`reasoning`/`coding` (`THINKING_CATEGORIES` in `benchmark.py`). `structured` is
deliberately excluded -- thinking on JSON/strict-format tasks wastes tokens and can break
the format -- so `-think` configs run those prompts direct.

## Sampling parameters

Each model uses parameters verified against its official model card; see `MODELS` in
`benchmark.py`. `min_p=0` is pinned on every request (server default may clip the tail).

| Model | Temperature | top_p | top_k | presence / repetition penalty | Source |
|---|---|---|---|---|---|
| Gemma 4 (all) | 1.0 | 0.95 | 64 | - | [Gemma cards](https://ai.google.dev/gemma/docs/core) ("all use cases") |
| Qwen thinking | 1.0 | 0.95 | 20 | presence 1.5 (0.0 on 27B) | [Qwen cards](https://qwenlm.github.io/blog/qwen3/) ("general" preset; 0.6/0.95 is the "precise coding" preset) |
| Qwen no-think | 0.7 | 0.8 | 20 | presence 1.5 | same (2B text: 1.0 / 1.0 / 20, presence 2.0) |
| Ornith-1.0-35B | think 1.0 / nothink 0.7 | 0.95 / 0.8 | 20 | presence 1.5 | Qwen-family defaults (card: 0.6/0.95/20 examples, no penalty guidance) |
| Ornith-1.0-9B | 0.6 | 0.95 | 20 | - | official card quickstart |
| Agents-A1-4B | 0.85 | 0.95 | 20 | presence 1.1 | official card |
| Ministral 3 8B/14B | 0.07 | 1.0 | off | - | card: "temperature below 0.1" |
| GLM-4.7-Flash | 1.0 | 0.95 | off | - | z.ai card (no top_k published) |
| LFM2.5-8B-A1B | 0.2 | 1.0 | 80 | repetition 1.05 | card: temp 0.2, top_k 80, rep 1.05 |
| Mellum2-12B | 0.6 | 0.95 | 20 | - | card quickstart |
| Granite 4.1-8b | 0.7 | 0.95 | 64 | - | no card preset -- neutral defaults (unverified) |
| OLMo 3.1 32B Instruct | 0.6 | 0.95 | off | - | official `generation_config.json` |

Notes:
- **presence_penalty / repetition_penalty** are Qwen's and LFM2.5's documented anti-loop
  knobs (Qwen up to 2.0; LFM2.5 1.05; `repetition_penalty` is sent as llama.cpp
  `repeat_penalty`). They were hypothesized to cut think-mode timeouts, but a controlled
  rerun showed negligible effect: the timeouts are bound by decode speed, not looping.
  The knobs stay because they are vendor-recommended, not because they fixed the artifact.
- **Gemma 4 has a thinking toggle** (`enable_thinking`, unlike Gemma 3), so it runs a
  think/nothink pair like Qwen; thinking is worth +3..+9 for it (at 10-25x time, no timeouts).
  `enable_thinking` is sent on every request; toggle-less models ignore it. GLM's hybrid
  thinking uses a different
  switch (`thinking:{type}`) and defaults to enabled, so GLM runs thinking-on throughout.

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

Per-model context overrides (memory headroom on the ~25 GB working set):

- The ~18-20 GB models (Qwen 3.6 27B, GLM-4.7-Flash, Gemma 4 31B, OLMo 3.1 32B):
  `-c 8192` to keep f16 KV comfortably within the working set.
- Everything smaller: default `-c 16384`.

Multi-token prediction: every Qwen `-mtp-*` run has its MTP head embedded in the `-MTP`
GGUF; every Gemma run uses a separate `mtp-*.gguf` draft file that `_start_server`
auto-attaches via `--model-draft`. Both enable it with `--spec-type draft-mtp
--spec-draft-n-max 2 -np 1`. It is lossless (verified byte-identical output) and runs
1.2-2.2x faster. `-np > 1` is not yet supported with MTP, so MTP runs are single-stream.

## Findings

Key dated verdicts are recorded here because `results/` is local and gitignored. Full
current numbers live in `results/COMPARISON.md`, regenerated after each run:

- **Current speed/accuracy leader: Mellum2-12B-A2.5B.** The 2026-07-29 full run gave it
  36/36 in 156 seconds. Small Gemma thinking configs also reached the accuracy ceiling,
  while Gemma 26B-A4B no-think was the fastest near-perfect direct configuration.
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

See `results/COMPARISON.md` for the full table and per-model breakdown.

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
