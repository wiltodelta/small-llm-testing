# Troubleshooting

## Known issues

- llama-server's `-hf` resolver hangs on some Qwen repos even when files are cached.
  We always start with `-m <local_path>` discovered under `~/.cache/huggingface/hub/`.
- Mellum2 needs a recent llama.cpp: the `mellum` architecture landed in PR #23966
  (merged 2026-06-02, build ~9580+). Older builds fail to start its server with
  `unknown model architecture: 'mellum'`. `brew upgrade llama.cpp` if you hit this.
- Qwen3 thinking-mode loops on trivial prompts (translations, "reply with one word")
  and overflows max_tokens or hits REQUEST_TIMEOUT. Fix: use no-think mode for short
  factual queries; thinking only helps on math/word-problems/code.
- Port 8080 may be held by a stale llama-server OR by another project's dev server
  (e.g. a Flask `--debug` process). Check `lsof -i :8080`; if it is not ours, do NOT
  kill it -- run the benchmark on the next free port: `benchmark.py --port 8081`.
  A server that times out during startup is terminated before the harness moves to the
  next config, so it cannot retain the port and cascade the failure through a full sweep.
- OLMo 3.1 32B needs `--jinja` and a current llama.cpp. Build 9590 failed on its
  `tojson` filter; build 10090 loads the original template and serves valid completions.
- Muse Glimmer requires llama.cpp PR #26841. Homebrew stable build 10330 predates the
  merge and fails with `unknown model architecture: 'muse-glimmer'`; HEAD build 10358
  loads the `UD-Q4_K_XL` model and quantized DFlash drafter successfully.
- Nemotron 3.5 Lightning GGUFs were produced with llama.cpp build 10362 and require
  that build or newer. The local preset uses the 19.82 GB `Q3_K_M`; `Q4_K_M` alone is
  25.48 GB and exceeds this Mac's 24.96 GB Metal working-set ceiling before caches.
- Do not run a benchmark concurrently with large model downloads. A ~17 GB model in the
  GPU working set plus a multi-GB download piling on memory pressure gets llama-server
  killed by macOS jetsam mid-run (the log cuts off with no traceback). Finish downloads
  first, then start the run.
