# Configuration

`MODELS` in `benchmark.py` is the curated routine set, not an inventory of every model
ever measured. A regression test pins its literal names so a broad experimental sweep
cannot silently become the default again. Historical results and the retirement policy
are documented in the README.

`CHALLENGERS` contains the current non-default text configs. `--include-challengers`
runs `MODELS + CHALLENGERS`, while `AGENTIC_TEXT_MODELS` contains North Mini Code.
`--full-sweep` runs all 14 current text configurations, and an explicit `--model` filter
searches those collections. Historical dominated models are intentionally not selectable.
Fara remains outside them because its evaluation requires screenshots and browser actions.

Each `ModelConfig` defines:

- `revision`, an optional immutable Hugging Face commit used to resolve the exact
  cached artifact. Qwen3.8-27B is pinned to `fdd03b8bbd279c1694563650e79d85a2373d9934`.
- `temperature`, `top_p`, and `top_k`, verified against the model's official card.
- `presence_penalty` and `repetition_penalty`, defaulting to no-ops.
  `repetition_penalty` is sent to llama.cpp as `repeat_penalty`; LFM2.5 uses its
  documented value.
- `thinking`, which gates thinking on `THINKING_CATEGORIES`. `_chat` sends
  `chat_template_kwargs={"enable_thinking": <thinking>}` on every request. Gemma 4
  honors it, while toggle-less models such as LFM2.5 and Mellum2 ignore it and retain
  their template default.
- `reasoning_strength`, used by Muse Glimmer. The requested strength applies to
  `THINKING_CATEGORIES`; direct prompts explicitly use `low`.
- `direct_sampling`, used when a hybrid model documents a different sampler for direct
  requests. Qwen3.8-27B's thinking config uses it on the suite's non-thinking categories.
- `reasoning_effort`, sent as an OpenAI-compatible top-level request field for thinking
  requests. llama.cpp maps it into the chat-template kwargs.
- `server_args`, for model-specific llama-server overrides.

Gemma models use the Unsloth GGUFs with a separate `mtp-*.gguf` draft. `_start_server`
detects that file and adds `--model-draft`, `--spec-type draft-mtp`,
`--spec-draft-n-max 2`, and `-np 1`. The measured output is byte-identical to normal
decode and materially faster.

A model whose server fails to start is logged and skipped rather than crashing the
whole run. Pass `--port 8081` or another free port when the default port is occupied.

`DEFAULT_SERVER_ARGS` applies:

```text
-ngl 99 -fa on -ub 1024 -c 16384
```

KV remains at llama.cpp's f16 default. On this machine it fits the curated set and
decodes faster than the previous q8_0 KV configuration. Quantized K was a smaller-memory
workaround and should not be reintroduced without a new measurement.

Other fixed settings:

- llama-server binary: `/opt/homebrew/bin/llama-server`
- request timeout: `REQUEST_TIMEOUT` in `benchmark.py`
- sample count: `DEFAULT_N_RUNS` in `benchmark.py`

Historical model dispositions live in the README's Future benchmark policy. Runtime
symptoms and workarounds live in `docs/troubleshooting.md`.

Before recommending, downloading, or benchmarking any model, record:

- temperature, `top_p`, `top_k`, `min_p`, and repetition or presence penalties;
- thinking mode and chat-template controls;
- recommended context and maximum output;
- separate presets for chat, reasoning, coding, and tool use;
- the official model card or generation config used as the source.

If a parameter is absent from the official configuration, explicitly document the
neutral value used by the benchmark instead of silently inheriting project defaults.

## Full-sweep presets

The benchmark caps generated output at 16,384 tokens for thinking requests and 4,096
for direct requests. Those are suite limits, not claims about each model's maximum.
All rows use `min_p=0`; omitted presence and repetition penalties are neutral `0` and
`1`. A neutral `top_p=1` or `top_k=0` means that sampler is disabled.

| Model family | Suite sampling | Thinking and scenarios | Context / official output guidance | Primary source |
|---|---|---|---|---|
| Gemma 4 E2B and 26B-A4B | `temp=1`, `top_p=.95`, `top_k=64` | Separate think/direct configs; thinking only for reasoning, math, and code | 131K context; official examples use 512-1,024 output tokens, not a stated maximum | [official Gemma 4 card](https://huggingface.co/google/gemma-4-e2b-it) |
| LFM2.5-8B-A1B | `.2/1/80`, repetition `1.05` | No thinking toggle; general chat and tool use share the native template | 128K context; official example uses 8,192 output tokens, not a stated maximum | [official card](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) |
| Mellum2-12B-A2.5B | `.6/.95/20` | Native thinking, no direct toggle; intended for coding and reasoning | 131K context; official usage example allows 81,920 output tokens | [official card](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking) |
| Qwen3.8-27B | Think `1/.95/20`; direct `.7/.8/20`, presence `1.5` | Separate think/direct configs; think mode uses `xhigh` effort, while direct prompts disable thinking | 262K native context, extensible to 1M; the suite retains its own 16K/4K output caps | [official card](https://huggingface.co/Qwen/Qwen3.8-27B) |
| Nemotron 3.5 Lightning 30B-A3B | `1/.95/0` | `enable_thinking` follows the suite category gate; agentic model with embedded MTP | Up to 1M context; the suite uses 16K and does not claim local 1M feasibility | [official card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) |
| Muse Glimmer 30B | `1/.95/64` | `high` reasoning for math, reasoning, and code; `low` for direct prompts | 131K+ context; the suite retains its own 16K/4K output caps | [official card](https://huggingface.co/meta-models/Muse-Glimmer-30B) |
| North Mini Code 1.0 | `1/.95/0` | Interleaved thinking should remain enabled and carried between agent turns; JSON-schema tools | 256K context, 64K maximum output; official simple generation example uses 1,024 | [official card](https://huggingface.co/CohereLabs/North-Mini-Code-1.0) |

LFM2.5-2.6B and Nanbeige4.2-3B are specified below because they were researched as
challengers. Fara1.5-4B is also below, but it is rerun separately from the text sweep.

Qwen3.8-27B uses Unsloth's 17.1 GB `Q4_K_M` GGUF at immutable repository revision
`fdd03b8bbd279c1694563650e79d85a2373d9934` for the text-only suite. The optional
roughly 0.93 GB vision projector is intentionally omitted. The official card recommends
thinking sampling `temperature=1`, `top_p=.95`, `top_k=20`, neutral penalties, and
`reasoning_effort=xhigh`; direct mode uses `.7/.8/20` with presence penalty `1.5`.
The think config applies the direct sampler whenever the category gate disables thinking,
so strict-format prompts do not accidentally use the reasoning sampler. The preset and
immutable cache target are prepared, but model loading and inference remain unverified
until the benchmark is explicitly authorized.

Muse Glimmer uses Unsloth's 15.9 GB `UD-Q4_K_XL` GGUF plus the 1.6 GB quantized
DFlash drafter. The harness auto-attaches the drafter with a 15-token draft window;
the optional perception encoder is omitted because this suite is text-only. The model
card recommends `high` or `xhigh` for complex problem solving, coding, and agentic
tasks. The benchmark uses `high` for its thinking categories and `low` for short direct
and strict-format prompts so the requested effort is explicit on every call.

Nemotron uses Bartowski's 19.82 GB `Q3_K_M` GGUF. The usual `Q4_K_M` is 25.48 GB,
which exceeds this Mac's 24.96 GB Metal working-set ceiling before KV cache and compute
buffers. This makes the local result a deliberately memory-safe but more aggressively
quantized comparison. The current GGUF embeds its MTP layers, so the harness enables
`draft-mtp` without downloading a separate draft file. NVIDIA specifies
`temperature=1`, `top_p=.95`, and no `top_k`; the benchmark uses neutral `top_k=0`.

## Researched challenger presets

These models are not in the default routine set, but their verified presets and dated
local verdicts are retained so a future rerun does not have to rediscover them.

### LFM2.5-2.6B

- Official sampling: `temperature=0.1`, `top_k=50`, repetition penalty `1.1`.
  The card does not specify `top_p` or `min_p`; the benchmark used neutral `top_p=1`
  and its fixed `min_p=0`. Presence penalty remained neutral at `0`.
- The card documents a 131,072-token context and uses `max_new_tokens=512` in its
  inference example. It provides one agentic preset rather than separate chat,
  reasoning, or coding presets, and explicitly discourages agentic coding and
  knowledge-heavy workloads.
- The ChatML-like template supports native tool calls between
  `<|tool_call_start|>` and `<|tool_call_end|>`. No thinking toggle is documented;
  the benchmark's `thinking=False` therefore requests no extra control and leaves the
  native template behavior unchanged.
- Source: [official model card](https://huggingface.co/LiquidAI/LFM2.5-2.6B).
- Local Q8_0 verdict: accurate but too verbose and slow to add a useful routine Pareto
  point. Exact dated measurements live in the [generated comparison](../results/COMPARISON.md).

### Nanbeige4.2-3B

- Reasoning and chat: `temperature=0.6`, `top_p=0.95`, `top_k=20`, up to 131,072
  new tokens. Agentic and tool use: `temperature=1.0`, up to 65,536 new tokens; the
  official generation configuration supplies `top_p=0.95` and `top_k=20`.
- The model context is 262,144 tokens. No `min_p`, presence penalty, or repetition
  penalty is specified; the text benchmark used neutral `min_p=0`, presence penalty
  `0`, and repetition penalty `1`.
- `enable_thinking` controls the current response. Use `preserve_thinking=False` for
  general chat and QA, and `True` for multi-turn tool use, office tasks, and code-agent
  workflows. Pass tools through the template and prefer `tool_call_format="xml"`.
- Sources: [official model card](https://huggingface.co/Nanbeige/Nanbeige4.2-3B),
  [generation config](https://huggingface.co/Nanbeige/Nanbeige4.2-3B/blob/main/generation_config.json),
  and upstream [llama.cpp PR #25994](https://github.com/ggml-org/llama.cpp/pull/25994).
- Local Q8_0 verdict: thinking is accurate but impractically slow, while direct mode
  loses too much accuracy. Keep for agentic evaluation only; exact dated measurements
  live in the [generated comparison](../results/COMPARISON.md).

### Fara1.5-4B

- Official generation: deterministic `temperature=0`, `max_tokens=2048`, a 262,144-
  token model context, and no separate chat, reasoning, or coding preset. The local
  smoke used `-c 16384`, which was sufficient for its roughly 3K-token single-step
  prompts but is not the model maximum.
- The official card does not specify `top_p`, `top_k`, `min_p`, presence penalty, or
  repetition penalty. The smoke did not send those fields; with `temperature=0`, token
  choice was deterministic, while llama.cpp retained its sampler defaults.
- Use the official system prompt and `computer_use` XML tool-call schema verbatim, a
  1440x900 browser viewport, and no more than the latest three screenshots in history.
  The model emits coordinates in the Fara harness's 1000x1000 space, which the harness
  scales back to the viewport.
- Sources: [official model card](https://huggingface.co/microsoft/Fara1.5-4B) and
  [official Fara harness](https://github.com/microsoft/fara). The checked-out harness's
  identity text incorrectly says Qwen3.5-9B for this size; the model card identifies the
  4B checkpoint as Qwen3.5-4B, so do not derive the base size from that prompt string.
- Local Q8_0 + BF16 `mmproj` smoke, 2026-08-09: upstream llama.cpp build 10280 loaded
  the model; two 1440x900 synthetic-form actions completed in 15.0 and 16.6 seconds at
  12.45 and 13.34 decode tok/s. Both grounded `Save draft` correctly, and the explicit
  do-not-submit scenario avoided the irreversible submit action. This is a smoke test,
  not an end-to-end success rate.
