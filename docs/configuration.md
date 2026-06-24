# Configuration

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
- `REQUEST_TIMEOUT = 120` -- think-mode can run long / loop; fail fast instead of hanging
- `DEFAULT_N_RUNS = 3` -- each prompt sampled this many times to average out temperature
