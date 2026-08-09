# Benchmark comparison

Generated from `benchmark.json` (2026-07-30T06:17:44.676564+00:00). Apple M5, 32 GB, f16 KV.
Test set: 12-prompt text discriminating core, n=3. Every config scores out of `/36`.

Caveats: (1) fails split `wrong/timeout/empty` -- a timeout is too-slow-to-finish,
not a wrong answer. (2) `tok/s` from this long suite is thermally throttled toward
the end; use `llama-bench` on a cool machine for peak decode speed.

## All configs

| Model | Passes | Fails w/t/e | Total time | tok/s |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 166s | 66.7 |
| gemma-4-e2b-Q8_0-nothink | 25/36 | 11/0/0 | 35s | 71.2 |
| gemma-4-e4b-Q4_K_M-think | 36/36 | 0/0/0 | 190s | 34.4 |
| gemma-4-e4b-Q4_K_M-nothink | 26/36 | 10/0/0 | 44s | 36.2 |
| gemma-4-12b-Q4_K_M-think | 36/36 | 0/0/0 | 657s | 15.1 |
| gemma-4-12b-Q4_K_M-nothink | 28/36 | 8/0/0 | 69s | 14.7 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 303s | 33.5 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 35/36 | 1/0/0 | 28s | 34.5 |
| gemma-4-31b-qat-Q4_K_XL-think | 36/36 | 0/0/0 | 1016s | 7.8 |
| gemma-4-31b-qat-Q4_K_XL-nothink | 35/36 | 1/0/0 | 112s | 7.8 |
| qwen3.5-2b-Q8_0-mtp-think | 34/36 | 2/0/0 | 1189s | 40.7 |
| qwen3.5-2b-Q8_0-mtp-nothink | 20/36 | 16/0/0 | 26s | 46.1 |
| qwen3.5-4b-Q8_0-mtp-think | 35/36 | 1/0/0 | 877s | 24.8 |
| qwen3.5-4b-Q8_0-mtp-nothink | 20/36 | 16/0/0 | 27s | 28.3 |
| qwen3.5-9b-Q8_0-mtp-think | 36/36 | 0/0/0 | 1419s | 15.1 |
| qwen3.5-9b-Q8_0-mtp-nothink | 26/36 | 10/0/0 | 44s | 17.2 |
| qwen3.6-27b-Q4_K_M-mtp-think | 30/36 | 0/6/0 | 4005s | 5.5 |
| qwen3.6-27b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 140s | 5.4 |
| qwen3.6-35b-a3b-Q4_K_M-mtp-think | 35/36 | 0/1/0 | 1387s | 20.9 |
| qwen3.6-35b-a3b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 42s | 22.5 |
| ornith-1.0-35b-Q4_K_M-mtp-think | 35/36 | 0/1/0 | 1602s | 24.0 |
| ornith-1.0-35b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 29s | 25.8 |
| ornith-1.0-9b-think-Q8_0 | 36/36 | 0/0/0 | 1383s | 9.3 |
| agents-a1-4b-think-Q8_0 | 36/36 | 0/0/0 | 1323s | 12.7 |
| ministral-3-8b-Q8_0 | 19/36 | 17/0/0 | 114s | 5.8 |
| ministral-3-14b-Q4_K_M | 21/36 | 15/0/0 | 119s | 6.0 |
| glm-4.7-flash-Q4_K_M | 36/36 | 0/0/0 | 935s | 16.7 |
| lfm2.5-8b-a1b-Q8_0 | 35/36 | 1/0/0 | 192s | 30.2 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 156s | 31.3 |
| granite-4.1-8b-Q8_0 | 30/36 | 6/0/0 | 225s | 6.6 |
| olmo-3.1-32b-instruct-Q4_K_M | 27/36 | 9/0/0 | 253s | 2.4 |

## Thinking vs no-thinking

| Config | think | nothink | think fails w/t/e |
|---|---|---|---|
| gemma-4-12b-Q4_K_M | 36/36 | 28/36 | 0/0/0 |
| gemma-4-26b-a4b-Q4_K_M | 36/36 | 35/36 | 0/0/0 |
| gemma-4-31b-qat-Q4_K_XL | 36/36 | 35/36 | 0/0/0 |
| gemma-4-e2b-Q8_0 | 36/36 | 25/36 | 0/0/0 |
| gemma-4-e4b-Q4_K_M | 36/36 | 26/36 | 0/0/0 |
| ornith-1.0-35b-Q4_K_M-mtp | 35/36 | 30/36 | 0/1/0 |
| qwen3.5-2b-Q8_0-mtp | 34/36 | 20/36 | 2/0/0 |
| qwen3.5-4b-Q8_0-mtp | 35/36 | 20/36 | 1/0/0 |
| qwen3.5-9b-Q8_0-mtp | 36/36 | 26/36 | 0/0/0 |
| qwen3.6-27b-Q4_K_M-mtp | 30/36 | 30/36 | 0/6/0 |
| qwen3.6-35b-a3b-Q4_K_M-mtp | 35/36 | 30/36 | 0/1/0 |
