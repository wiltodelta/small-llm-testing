# Benchmark comparison

Generated from `benchmark.json` (2026-08-09T22:48:51.961914+00:00). Apple M5, 32 GB, f16 KV.
Test set: 12-prompt text discriminating core, n=3. Every config scores out of `/36`.

Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,
not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward
the end; use `llama-bench` on a cool machine for peak decode speed.

## All configs

| Model | Passes | Fails w/t/e | Total time | tok/s |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 317s | 38.2 |
| gemma-4-e2b-Q8_0-nothink | 26/36 | 10/0/0 | 62s | 38.8 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 658s | 15.9 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 34/36 | 2/0/0 | 53s | 16.7 |
| lfm2.5-8b-a1b-Q8_0 | 35/36 | 1/0/0 | 227s | 24.7 |
| lfm2.5-2.6b-Q8_0 | 36/36 | 0/0/0 | 631s | 17.6 |
| nanbeige4.2-3b-Q8_0-think | 36/36 | 0/0/0 | 2236s | 8.5 |
| nanbeige4.2-3b-Q8_0-nothink | 28/36 | 8/0/0 | 223s | 9.3 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 163s | 30.7 |

## Thinking vs no-thinking

| Config | think | nothink | think fails w/t/e |
|---|---|---|---|
| gemma-4-26b-a4b-Q4_K_M | 36/36 | 34/36 | 0/0/0 |
| gemma-4-e2b-Q8_0 | 36/36 | 26/36 | 0/0/0 |
| nanbeige4.2-3b-Q8_0 | 36/36 | 28/36 | 0/0/0 |
