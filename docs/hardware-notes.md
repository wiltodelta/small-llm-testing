# Hardware notes

## Memory class (M5, ~24.96 GB working set)

Measure the real GPU working set (the ceiling for weights + KV + compute buffers) with
a one-line Swift Metal query (do not guess it):
`echo 'import Metal; print(MTLCreateSystemDefaultDevice()!.recommendedMaxWorkingSetSize)' | swift -`

- Gemma 4 26B-A4B Q4_K_M (~16.8 GB) and Qwen 3.6 27B Q4_K_M (~16.8 GB) fit
  comfortably (these were OOM / kernel-panic on the old 16 GB machine).
- Qwen 3.6 35B-A3B UD-Q4_K_M (~21 GB) now INCLUDED: at `-c 8192` it loads fine
  (verified by a server-start smoke). Previously excluded as too marginal; the smaller
  ctx leaves enough headroom. Its MoE (3B active) beats the 27B dense on accuracy AND speed.
- OLMo 3.1 32B Instruct -- excluded: chat-template `tojson` filter unparseable by
  llama.cpp 9590 (would need `--no-jinja` + a guessed template). Memory was fine (~19.5 GB).
- Phi-4-Reasoning 15B -- excluded for speed (7.9 tok/s), not memory.
- Zyphra ZAYA1-8B -- excluded: hybrid-Mamba MoE, no working llama.cpp path
  (official deploy is a custom vLLM fork), text-only.
