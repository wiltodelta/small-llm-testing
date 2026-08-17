# Benchmark comparison

Generated from `benchmark.json` (2026-08-17T04:55:26.829248+00:00). Apple M5, 32 GB, f16 KV.
Test set: 12-prompt text discriminating core, n=3. Every config scores out of `/36`.

Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,
not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward
the end; use `llama-bench` on a cool machine for peak decode speed.

## All configs

| Model | Passes | Fails w/t/e | Total time | tok/s |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 267s | 45.0 |
| gemma-4-e2b-Q8_0-nothink | 27/36 | 9/0/0 | 57s | 44.8 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 489s | 20.4 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 35/36 | 1/0/0 | 44s | 21.3 |
| lfm2.5-8b-a1b-Q8_0 | 36/36 | 0/0/0 | 195s | 29.8 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 208s | 26.9 |
| lfm2.5-2.6b-Q8_0 | 36/36 | 0/0/0 | 632s | 17.6 |
| nanbeige4.2-3b-Q8_0-think | 36/36 | 0/0/0 | 1779s | 9.8 |
| nanbeige4.2-3b-Q8_0-nothink | 28/36 | 8/0/0 | 192s | 10.1 |
| qwen3.8-27b-Q4_K_M-think | 36/36 | 0/0/0 | 968s | 3.4 |
| qwen3.8-27b-Q4_K_M-nothink | 30/36 | 6/0/0 | 217s | 2.9 |
| nemotron-3.5-lightning-30b-a3b-Q3_K_M | 36/36 | 0/0/0 | 498s | 24.4 |
| muse-glimmer-30b-high-Q4_K_XL | 36/36 | 0/0/0 | 2068s | 3.7 |
| north-mini-code-1.0-Q4_K_M | 36/36 | 0/0/0 | 301s | 16.2 |

## Thinking vs no-thinking

| Config | think | nothink | think fails w/t/e |
|---|---|---|---|
| gemma-4-26b-a4b-Q4_K_M | 36/36 | 35/36 | 0/0/0 |
| gemma-4-e2b-Q8_0 | 36/36 | 27/36 | 0/0/0 |
| nanbeige4.2-3b-Q8_0 | 36/36 | 28/36 | 0/0/0 |
| qwen3.8-27b-Q4_K_M | 36/36 | 30/36 | 0/0/0 |
