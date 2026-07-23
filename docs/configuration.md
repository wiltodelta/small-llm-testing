# Configuration

- `MODELS` list in `benchmark.py` defines all configs. Each `ModelConfig` has:
  - `temperature`, `top_p`, `top_k` (vendor-recommended, verified per model card)
  - `presence_penalty` (default 0.0) and `repetition_penalty` (default 1.0, sent as llama.cpp
    `repeat_penalty`) -- vendor anti-repetition knobs. Qwen sets presence_penalty 1.5 (0.0 on
    the 27B thinking); LFM2.5 sets repetition_penalty 1.05. Both target thinking-mode looping.
    Qwen presets are per-card, not per-family: the 27B and 35B-A3B cards disagree on thinking
    presence_penalty (0.0 vs 1.5), and the 2B's text non-thinking preset (1.0/1.0/pp=2.0)
    differs from the other sizes (0.7/0.8/pp=1.5). Verify each new card; do not extrapolate.
  - `thinking: bool` -- gates whether this config thinks on `THINKING_CATEGORIES`. `_chat`
    sends `chat_template_kwargs={"enable_thinking": <thinking>}` on EVERY request: models with
    a toggle (Qwen3, Gemma 4) honor it; GLM (its toggle is `thinking:{type}`, not enable_thinking)
    and toggle-less models (Ministral/LFM/Mellum) ignore the kwarg and run at their default.
  - `server_args` -- per-model llama-server overrides (e.g. `-c 8192` for the ~17-22 GB
    models). MTP speculative decoding: all Qwen (and Ornith) use the `-MTP` GGUF (head embedded) with
    `--spec-type draft-mtp` in server_args; all Gemma load from Unsloth GGUFs that carry a
    separate `mtp-*.gguf` draft -- `_start_server` auto-detects it and adds
    `--model-draft <path> --spec-type draft-mtp --spec-draft-n-max 2 -np 1`. MTP is lossless
    (byte-identical output) and ~1.2-2.2x faster. The non-MTP Qwen A/B variant was dropped.
- A model whose server fails to start (unsupported arch, OOM, bad file) is logged and
  skipped by `run_benchmark`, not allowed to crash the whole run. Pass `--port 8081` (etc.)
  if 8080 is taken by another dev server.
- Laguna-XS-2.1 was measured and dropped: arch works (llama.cpp >= 10090, PR #25165) but
  the Metal f16 overflow in its MoE down-projection returns empty output for most prompts
  (21/36 empty think, 6/36 nothink on 2026-07-23). Re-add when upstream PR #25442 lands.
- `DEFAULT_SERVER_ARGS` in `benchmark.py` applies to every server start:
  `-ngl 99 -fa on -ub 1024 -c 16384`. KV cache stays at the f16 default (NOT q8_0):
  on 32 GB everything fits, and f16 KV is ~1.7x faster decode than q8_0 on this M5
  (llama-bench Qwen3.6-27B: 6.32 vs 3.72 tg t/s). Quantized K on Metal is costly.
  q8_0 KV was a 16 GB-machine memory hack -- do not re-add it.
- llama-server binary: `/opt/homebrew/bin/llama-server`
- `REQUEST_TIMEOUT = 300` -- raised from 120: think-mode coding on slow dense models
  (27B, ~5 tok/s) was timing out on decode speed, not on loops; 300s still fails real hangs.
- `DEFAULT_N_RUNS = 3` -- each prompt sampled this many times to average out temperature
