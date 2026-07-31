# Configuration

`MODELS` in `benchmark.py` is the curated routine set, not an inventory of every model
ever measured. A regression test pins its literal names so a broad experimental sweep
cannot silently become the default again. Historical results and the retirement policy
are documented in the README.

Each `ModelConfig` defines:

- `temperature`, `top_p`, and `top_k`, verified against the model's official card.
- `presence_penalty` and `repetition_penalty`, defaulting to no-ops.
  `repetition_penalty` is sent to llama.cpp as `repeat_penalty`; LFM2.5 uses its
  documented value.
- `thinking`, which gates thinking on `THINKING_CATEGORIES`. `_chat` sends
  `chat_template_kwargs={"enable_thinking": <thinking>}` on every request. Gemma 4
  honors it, while toggle-less models such as LFM2.5 and Mellum2 ignore it and retain
  their template default.
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
