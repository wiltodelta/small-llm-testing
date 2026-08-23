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
  Since 2026-08-23 the harness also probes the port once before any model runs and exits
  with status 2 naming the holder, so an occupied port fails in a second instead of
  burning `SERVER_STARTUP_TIMEOUT` per config. That is what it used to cost: a sweep on a
  port held by another project skipped four models in 20 minutes before anyone looked.
- OLMo 3.1 32B needs `--jinja` and a current llama.cpp. Build 9590 failed on its
  `tojson` filter; build 10090 loads the original template and serves valid completions.
- Ling-3.0-tiny needs llama.cpp PR #26608 (BailingMoE3, build 10544+). PATH
  `llama-server` is `llama-cpp-bundled` 10380 and fails to load it. A Homebrew
  `llama.cpp` HEAD-6503355 binary exists under Cellar but is not linked, because
  it conflicts with `llama-cpp-bundled`. Do not `brew link --overwrite` that
  without choosing which formula owns `/opt/homebrew/bin/llama-server`.
- Muse Glimmer needed llama.cpp PR #26841. It is retired from reruns; the note
  remains only for historical snapshots.
- Nemotron 3.5 Lightning GGUFs need llama.cpp 10362+. The local `Q3_K_M` is a
  memory-safe quant (`Q4_K_M` is 25.48 GB). The old 300s `REQUEST_TIMEOUT` could not
  finish the then-fixed 4,096-token long-context cap at ~5 tok/s; those fails are
  budget artifacts, not wrong
  answers. HTTP API errors now store status and body in `fail_reason`.
- Do not run a benchmark concurrently with large model downloads. A ~17 GB model in the
  GPU working set plus a multi-GB download piling on memory pressure gets llama-server
  killed by macOS jetsam mid-run (the log cuts off with no traceback). Finish downloads
  first, then start the run.
