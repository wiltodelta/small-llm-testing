# Hardware notes

## Memory class (M5, ~24.96 GB working set)

Measure the real GPU working set (the ceiling for weights + KV + compute buffers) with
a one-line Swift Metal query (do not guess it):
`echo 'import Metal; print(MTLCreateSystemDefaultDevice()!.recommendedMaxWorkingSetSize)' | swift -`

- Gemma 4 26B-A4B Q4_K_M (~16.8 GB) and Qwen 3.6 27B Q4_K_M (~16.8 GB) fit
  comfortably (these were OOM / kernel-panic on the old 16 GB machine).
- Qwen3.8-27B Q4_K_M (17.1 GB) loaded for the direct config. The thinking config's
  0/66 HTTPError is not a working-set result; recheck with HTTP body logging.
- Ling-3.0-tiny Q8_0 (8.41 GB) loaded at `-c 2048` on llama.cpp build 10544.
  The PATH `llama-server` (`llama-cpp-bundled` 10380) cannot load BailingMoE3.
- North Mini Code 1.0 UD-Q4_K_M (~19.2 GB) loaded at `-c 8192` with full Metal
  offload on llama.cpp build 10090 and completed the text suite without a memory error.
  Rechecked 2026-08-21 on build 10380: it also loads and serves at `-c 16384`, which is
  now its `n_ctx`. The old 8192 was a carried-over guess, and it was sizing the article
  answer budget for every other model in the fleet.
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

## Cold llama-bench, 2026-08-22 (build 10380, M5, f16 KV)

Suite flags (`-ngl 99 -fa on -ub 1024`), `-r 3`, idle machine (1-minute load 2.79 at
start). `d3072` is KV depth, roughly the Ferrel article. Run because the 2026-08-21 sweep
reported 2.6 tok/s for Qwen3.8-27B and that could not be told apart from contention.

| Config | pp512 | tg128 | pp512 @ d3072 | tg128 @ d3072 |
|---|---:|---:|---:|---:|
| Qwen3.8-27B Q4_K_M (dense) | 40.21 | 1.46 | 38.64 | 1.19 |
| North Mini Code 1.0 UD-Q4_K_M (MoE 30B.A3B) | 137.36 | see below | 132.67 | 15.37 |
| Mellum2-12B-A2.5B Thinking Q4_K_M | 430.77 | 30.06 | 499.69 | 33.28 |

**The suite's Qwen number was not contention.** Cold decode is 1.46 tok/s, and a repeat
at a busier moment (load 7.08) gave 2.29. The suite's 2.6 sits at the top of that range,
so if anything the long run over-reported. Prefill is equally odd: 40 tok/s for a 27B
dense, against 137 for a larger MoE and 431 for Mellum2.

**That does NOT establish anything about dense models.** The only comparator is this
repo's own llama-bench on Qwen3.6-27B Q4_K_M, 6.32 tok/s tg128 -- but that was
build 9380, and this is 10380. Model and build both differ, so the honest reading is
"Qwen3.8-27B is unusable here at this build", not "dense 27B is unusable here".
**Settled the next day, and the answer is both** -- see "Model or build? Both" below.

**Never quote the first tg reading after a model loads.** North Mini's first tg128 in the
matrix read 3.56 tok/s. Three identical repeats afterwards gave 14.04 (+/- 5.07), then
17.17 (+/- 0.18) and 17.46 (+/- 0.11): the first is warm-up with a standard deviation
three times any other, and steady state is ~17.3. The suite's 15.4 for this model is
consistent with that once thermal throttling is allowed for.

**Depth is not what costs the MoEs.** At d3072 North Mini holds 15.37 and Mellum2 gains
to 33.28, so serving the article does not by itself slow decode, and North Mini's raise
from `-c 8192` to `n_ctx=16384` has no measured decode cost.

## Model or build? Both. And MLX is not the rescue (2026-08-23)

The 2026-08-22 note left open whether Qwen3.8-27B's 1.46 tok/s was the model or llama.cpp
build 10380, because the only comparator (6.32 on Qwen3.6-27B) came from build 9380. Three
runs settle it. All are `llama-bench`, suite flags, `-r 3`, same M5.

| Run | Build | pp512 | tg128 |
|---|---|---:|---:|
| Qwen3.6-27B Q4_K_M | 10380 (stock) | 106.46 | **5.17 +/- 0.11** |
| Qwen3.8-27B Q4_K_M | 10380 (stock) | 40.21 | **1.46 +/- 0.18** |
| Qwen3.8-27B Q4_K_M | PR-27342 (`1deefcc`, newer master) | 72.11 | **3.31 +/- 0.08** |

Qwen3.6 at d3072: pp 62.63, tg 3.26 +/- 0.03.

**Both factors are real.** Same build, different model: 5.17 against 1.46, so Qwen3.8 is
roughly 3.5x slower than its predecessor here. Same model, newer build: 1.46 against 3.31,
so master has since more than doubled it. Neither alone explains the gap, and the earlier
one-line reading ("dense 27B is a bad overnight worker") was wrong twice over: it blamed
an architecture class for what is a model and a build.

**What it does not change: the class is still too slow for this job.** The best dense-27B
number on this machine is 5.17 tok/s, so a 12,288-token article answer needs about 40
minutes per attempt, times three samples, times the prompt count.

**MLX is not faster.** `mlx-community/Qwen3.6-27B-4bit` generated 256 tokens at 3.687
tok/s with a 15.4 GB peak, against llama.cpp's 5.17 on the same model at Q4_K_M. So the
bottleneck is not llama.cpp's Metal path. Caveats: single run, no repeats, and MLX 4-bit
is not bit-identical to Q4_K_M, so read it as "same order, not faster", not as a ratio.

**DFlash2: it runs, its throughput here is not yet measured.** PR #27342 is open, not
merged, so it needs a source build (`cmake -DGGML_METAL=ON`, then `--model-draft`,
`--spec-type draft-dflash`, `-ngld 99`). The draft loads and drafts: acceptance came out
at 0.365-0.454 with a mean accepted run of 3.5-4.2 tokens, against the 5.39 acceptance
length the model card reports on GSM8K. Passing the draft without `-ngld 99` measurably
hurts. The throughput A/B is **inconclusive and must be redone on a quiet machine**: two
identical no-draft runs minutes apart gave 5.16 and 2.94 tok/s, a spread wider than the
effect being tested. Per the Ling-3.0-tiny precedent, do not add DFlash2 to `CHALLENGERS`
until the project binary carries the merged PR.
