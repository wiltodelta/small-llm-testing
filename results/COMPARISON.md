# Benchmark comparison

Generated from `benchmark.json` (2026-08-21T08:05:03.508696+00:00). Apple M5, 32 GB, f16 KV.
Test set: discriminating text core plus agent-scenario categories, n=3 per prompt. Every config scores out of `/66`.

Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,
not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward
the end; use `llama-bench` on a cool machine for peak decode speed.

## All configs

| Model | Passes | Fails w/t/e | Total time | tok/s |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 65/66 | 1/0/0 | 765s | 29.9 |
| gemma-4-e2b-Q8_0-nothink | 47/66 | 19/0/0 | 103s | 30.1 |
| gemma-4-26b-a4b-Q4_K_M-think | 63/66 | 0/0/3 | 1758s | 17.5 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 64/66 | 2/0/0 | 88s | 19.7 |
| lfm2.5-8b-a1b-Q8_0 | 63/66 | 3/0/0 | 706s | 29.9 |
| mellum2-12b-a2.5b-think-Q4_K_M | 66/66 | 0/0/0 | 473s | 26.8 |
| qwen3.8-27b-Q4_K_M-think | 61/66 | 0/5/0 | 3826s | 2.6 |
| qwen3.8-27b-Q4_K_M-nothink | 52/66 | 14/0/0 | 506s | 2.8 |
| nemotron-3.5-lightning-30b-a3b-Q3_K_M | 60/66 | 0/0/6 | 2347s | 21.3 |
| north-mini-code-1.0-Q4_K_M | 62/66 | 0/0/4 | 1645s | 15.4 |

## Thinking vs no-thinking

| Config | think | nothink | think fails w/t/e |
|---|---|---|---|
| gemma-4-26b-a4b-Q4_K_M | 63/66 | 64/66 | 0/0/3 |
| gemma-4-e2b-Q8_0 | 65/66 | 47/66 | 1/0/0 |
| qwen3.8-27b-Q4_K_M | 61/66 | 52/66 | 0/5/0 |
