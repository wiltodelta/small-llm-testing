# Configuration

`MODELS` in `benchmark.py` is the curated routine set, not an inventory of every model
ever measured. A regression test pins its literal names so a broad experimental sweep
cannot silently become the default again. Historical results and the retirement policy
are documented in the README.

`CHALLENGERS` is Qwen3.8-27B (think and direct) and Nemotron 3.5 Lightning.
The 2026-08-18 agent-scenario snapshots are not quality verdicts: Qwen thinking
recorded a bare `HTTPError` with no response body, and Nemotron's fails were
300-second request timeouts on thinking prompts. `--include-challengers` runs
`MODELS + CHALLENGERS`. `AGENTIC_TEXT_MODELS` contains North Mini Code.
`--full-sweep` runs all 10 current text configurations, and an explicit `--model` filter
searches those collections. Historical dominated models are intentionally not selectable.
Fara remains outside them because its evaluation requires screenshots and browser actions.

Each `ModelConfig` defines:

- `revision`, an optional immutable Hugging Face commit used to resolve the exact
  cached artifact.
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
-ngl 99 -fa on -ub 1024
```

The context window is not in that tuple. It comes from `ModelConfig.n_ctx` (default
`DEFAULT_N_CTX`, 16,384) so one model's memory bound cannot silently size the whole
fleet's answer budget, which is what `-c 8192` on North Mini Code did until 2026-08-21.
Raise a model's `n_ctx` only from a measured server start on this machine. `_start_server`
rejects a `-c` passed through `server_args`, so `n_ctx` stays the single source of truth, and
`ModelConfig.article_cap` derives the article answer budget from it.

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
for direct requests, with one exception: prompts marked `article_sized` derive their cap
per model as `n_ctx - ARTICLE_PROMPT_RESERVE` (12,288 at the default context), so the
budget follows the serving context instead of a literal. Those are suite limits, not
claims about each model's maximum.
All rows use `min_p=0`; omitted presence and repetition penalties are neutral `0` and
`1`. A neutral `top_p=1` or `top_k=0` means that sampler is disabled.

| Model family | Suite sampling | Thinking and scenarios | Context / official output guidance | Primary source |
|---|---|---|---|---|
| Gemma 4 E2B and 26B-A4B | `temp=1`, `top_p=.95`, `top_k=64` | Separate think/direct configs; thinking for math, reasoning, coding, consistency, and longcontext | 131K context; official examples use 512-1,024 output tokens, not a stated maximum | [official Gemma 4 card](https://huggingface.co/google/gemma-4-e2b-it) |
| LFM2.5-8B-A1B | `.2/1/80`, repetition `1.05` | No thinking toggle; general chat and tool use share the native template | 128K context; official example uses 8,192 output tokens, not a stated maximum | [official card](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) |
| Mellum2-12B-A2.5B | `.6/.95/20` | Native thinking, no direct toggle; intended for coding and reasoning | 131K context; official usage example allows 81,920 output tokens | [official card](https://huggingface.co/JetBrains/Mellum2-12B-A2.5B-Thinking) |
| Qwen3.8-27B | Think `1/.95/20`; direct `.7/.8/20`, presence `1.5` | Separate think/direct configs; think mode uses `xhigh` effort | 262K native context; official thinking output guidance is 262,144 tokens, the suite keeps 16K/4K caps | [official card](https://huggingface.co/Qwen/Qwen3.8-27B) |
| Nemotron 3.5 Lightning 30B-A3B | `1/.95/0` | `enable_thinking` follows the suite category gate; embedded MTP | Up to 1M context; the suite uses 16K and does not claim local 1M feasibility | [official card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) |
| North Mini Code 1.0 | `1/.95/0` | Interleaved thinking should remain enabled and carried between agent turns; JSON-schema tools | 256K context, 64K maximum output; official simple generation example uses 1,024 | [official card](https://huggingface.co/CohereLabs/North-Mini-Code-1.0) |

Retired challenger presets (LFM2.5-2.6B, Nanbeige4.2-3B, Muse Glimmer) are specified
below so a future rerun does not rediscover them. Qwen3.8-27B and Nemotron stay in
`CHALLENGERS` until a rerun on the corrected budget (derived article cap plus
`REQUEST_TIMEOUT` 1800s). Fara1.5-4B is also below, but it is rerun separately
from the text sweep.

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
- Local Q8_0 verdict: accurate on the agent-scenario suite but dominated by Gemma 4
  E2B thinking (same or better accuracy, much less wall time). The card also
  discourages knowledge-heavy workloads. Retired from reruns.

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
- Local Q8_0 verdict: thinking timed out on the agent-scenario long-context and
  consistency prompts; direct mode missed most contradiction pairs. Retired from
  reruns, including the agentic track.

### Qwen3.8-27B

- Official thinking sampling: `temperature=1`, `top_p=.95`, `top_k=20`,
  `reasoning_effort=xhigh`. Direct mode: `.7/.8/20` with presence penalty `1.5`.
  The think config applied the direct sampler on non-thinking categories.
- Text-only Unsloth `Q4_K_M` (17.1 GB) at revision
  `fdd03b8bbd279c1694563650e79d85a2373d9934`; vision projector omitted.
- Source: [official card](https://huggingface.co/Qwen/Qwen3.8-27B).
- Official `reasoning_effort` levels are `xhigh` (default), `medium`, and `low`.
  The suite sends `xhigh` as a top-level request field for thinking prompts.
- 2026-08-18 snapshot is not a quality verdict. Thinking: 0/66, first request
  58s then `api error: HTTPError`, later requests 0.01-0.11s, no response body
  stored. Direct: 53/66 real wrong answers, 1.8 tok/s. Recheck with HTTP body
  logging before judging the model.
- Cold llama-bench 2026-08-22 (build 10380, idle machine): tg128 1.46 tok/s, 1.19 at
  depth 3072, pp512 40.21. The suite's 2.6 tok/s was therefore real, not contention.
  At that speed a 12,288-token article answer needs over two hours, so this config
  cannot finish the agent scenario within any sane unattended budget on this machine.
  Resolved 2026-08-23: it is the model AND the build. Qwen3.6-27B on the same stock
  binary does 5.17 tok/s, and Qwen3.8-27B on a newer master does 3.31. Even so, no
  dense 27B on this machine is fast enough for the agent scenario; see
  [`hardware-notes.md`](hardware-notes.md).

### Nemotron 3.5 Lightning 30B-A3B

- Official sampling: `temperature=1`, `top_p=.95`, no `top_k` (suite used `top_k=0`).
- Local GGUF was Bartowski `Q3_K_M` (19.82 GB) because `Q4_K_M` is 25.48 GB and
  exceeds the 24.96 GB Metal working-set ceiling. MTP is embedded.
- Source: [official card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16).
- 2026-08-18 snapshot is not a quality verdict. 59/66, and every fail was a
  300-second `TimeoutError` on thinking prompts. At 5.4 tok/s the then-fixed
  4,096-token long-context cap needed ~760s, so `REQUEST_TIMEOUT=300` stopped the
  request before an answer. The 2026-08-21 rerun hit the other half of the same
  defect: six `empty` results, each exactly 4,096 tokens cut mid-thought. Both are
  budget artifacts, not quality. Recheck on the corrected budget, still on `Q3_K_M`.

### Muse Glimmer 30B

- Official sampling: `temp=1`, `top_p=.95`, `top_k=64`. Named reasoning strength
  `high` for thinking categories and `low` for direct prompts. Unsloth `UD-Q4_K_XL`
  plus `dflash-kquant.gguf`.
- Source: [official card](https://huggingface.co/meta-models/Muse-Glimmer-30B).
- Local verdict: ceiling on the 12-prompt core at several times the Gemma 26B
  think wall time. The 22-prompt rerun never finished. Retired from text reruns.

### Ling-3.0-tiny

- Official sampling: `temperature=1.0`, `top_p=0.95`, `top_k=20`. Thinking is on
  by default; disable with `chat_template_kwargs.enable_thinking=false`. Context
  262,144. No `min_p`, presence penalty, or repetition penalty on the card; the
  suite would use neutrals `0` / `0` / `1`.
- 7.9B total, 1.3B active hybrid-linear MoE. Community Q8_0 GGUF is 8.41 GB at
  `bloomer010/Ling-3.0-tiny-GGUF` revision `76d03bfc93a2b0ec84aac5f187cdf3793541e2a7`.
  There is no official GGUF.
- Sources: [official card](https://huggingface.co/inclusionAI/Ling-3.0-tiny) and
  llama.cpp [PR #26608](https://github.com/ggml-org/llama.cpp/pull/26608) (BailingMoE3,
  merged 2026-08-17).
- Local smoke, 2026-08-20: llama.cpp build 10544 loaded the Q8_0 at `-c 2048` and
  returned `pong` with thinking off. `/opt/homebrew/bin/llama-server` is still
  `llama-cpp-bundled` 10380, which predates that merge and cannot load the
  architecture. Do not add to `CHALLENGERS` until the project binary includes it.

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
