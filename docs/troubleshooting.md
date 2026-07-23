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
  (e.g. a `veedma-landing` Flask `--debug` on 8080). Check `lsof -i :8080`; if it is not
  ours, do NOT kill it -- run the benchmark on the next free port: `benchmark.py --port 8081`.
- OLMo 3.1 32B fails to start: chat-template error `Unknown filter 'tojson'` (llama.cpp
  could not parse its Jinja template; observed on build 9590, not retested since). Would
  need `--no-jinja --chat-template <fmt>` with
  the right format; left out. Other models with exotic chat templates may hit the same.
- Do not run a benchmark concurrently with large model downloads. A ~17 GB model in the
  GPU working set plus a multi-GB download piling on memory pressure gets llama-server
  killed by macOS jetsam mid-run (the log cuts off with no traceback). Finish downloads
  first, then start the run.
