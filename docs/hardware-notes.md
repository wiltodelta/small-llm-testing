# Hardware notes

## Memory class (M5, ~24.96 GB working set)

Measure the real GPU working set (the ceiling for weights + KV + compute buffers) with
a one-line Swift Metal query (do not guess it):
`echo 'import Metal; print(MTLCreateSystemDefaultDevice()!.recommendedMaxWorkingSetSize)' | swift -`

- Gemma 4 26B-A4B Q4_K_M (~16.8 GB) and Qwen 3.6 27B Q4_K_M (~16.8 GB) fit
  comfortably (these were OOM / kernel-panic on the old 16 GB machine).
- North Mini Code 1.0 UD-Q4_K_M (~19.2 GB) loaded at `-c 8192` with full Metal
  offload on llama.cpp build 10090 and completed the text suite without a memory error.
- Qwen 3.6 35B-A3B UD-Q4_K_M (~21 GB) loaded at `-c 8192` during the broad sweep.
- OLMo 3.1 32B Instruct Q4_K_M (~19.5 GB) loaded at `-c 8192`. The original
  Jinja template and a chat completion were smoke-tested successfully on llama.cpp
  build 10090; the `tojson` parser failure from build 9590 no longer reproduced.
- Phi-4-Reasoning 15B -- excluded for speed (7.9 tok/s), not memory.
- Zyphra ZAYA1-8B -- excluded: hybrid-Mamba MoE, no working llama.cpp path
  (official deploy is a custom vLLM fork), text-only.
- Laguna S 2.1 -- excluded from this memory class: its official Q4_K_M GGUF is 96 GB.
- MiMo V2.5 -- excluded from this memory class: the official model is 310B total with
  15B active parameters and is documented for multi-GPU serving.
