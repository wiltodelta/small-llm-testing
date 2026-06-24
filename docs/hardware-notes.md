# Hardware notes

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
