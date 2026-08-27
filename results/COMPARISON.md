# Benchmark comparison

Generated from `benchmark.json` (2026-08-26T23:16:11.853204+00:00). Apple M5, 32 GB, f16 KV.
Test set: discriminating text core plus agent-scenario categories, n=3 per prompt. Every config scores out of `/66`.

Caveats: (1) fails split `wrong/timeout/empty/truncated` -- only `wrong` is a model
verdict; the other three mean the harness stopped the attempt. (2) `tok/s` from this
long suite is thermally throttled toward the end; use `llama-bench` on a cool machine
for peak decode speed.

## All configs

| Model | Passes | Fails w/t/e/x | Total time | tok/s |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 65/66 | 1/0/0/0 | 405s | 61.0 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 64/66 | 2/0/0/0 | 66s | 26.6 |
| mellum2-12b-a2.5b-think-Q4_K_M | 66/66 | 0/0/0/0 | 527s | 45.2 |
| granite-4.2-8b-Q8_0-low-effort | 62/66 | 4/0/0/0 | 240s | 10.9 |

## Thinking vs no-thinking

| Config | think | nothink | think fails w/t/e/x |
|---|---|---|---|
