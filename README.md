# small-llm-testing

Benchmark small LLMs locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) on Apple Silicon.

## Models

| Model | Parameters | Quant | Release | Announcement |
|-------|-----------|-------|---------|--------------|
| [Gemma 4 E2B](https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF) | 2B effective | Q8_0 | March 2025 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Gemma 4 E4B](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF) | 4B effective | Q4_K_M | March 2025 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Qwen3.5-0.8B](https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF) | 0.8B | Q8_0 | March 2026 | [Qwen3.5 release](https://qwenlm.github.io/blog/qwen3/) |
| [Qwen3.5-2B](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF) | 2B | Q8_0 | March 2026 | same |
| [Qwen3.5-4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF) | 4B | Q8_0 | March 2026 | same |
| [Qwen3.5-9B](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF) | 9B | Q8_0 | March 2026 | same |

Each Qwen3.5 model is benchmarked twice: with thinking mode on (`-think`, slower
but better on reasoning) and off (`-nothink`, fast direct answers).

### Models that don't work on 16 GB

| Model | Issue |
|-------|-------|
| Gemma 4 26B-A4B | OOM -- needs 24+ GB RAM |
| Qwen 3.6 27B (Q2_K_XL) | Kernel panic during load -- recommendedMaxWorkingSetSize is only 12.7 GB on M4 base |
| Qwen 3.6 35B-A3B (any quant) | Same memory class as 27B; total file size 12+ GB even at Q2 |
| Phi-4-Reasoning 15B | Too slow (7.9 tok/s), most prompts timeout |

Qwen3.5-9B fits with `-c 8192 --cache-type-k q8_0 --cache-type-v q8_0` (we set
this per-model). Without those overrides the default 256K context overflows GPU memory.

## Hardware

- MacBook Air (M4, 2025), 10-core CPU, 10-core GPU, 16 GB unified memory, macOS Tahoe
- Apple GPU `recommendedMaxWorkingSetSize` is ~12.7 GB on this machine.

## Prerequisites

```bash
brew install llama.cpp
```

## Download models first

Models are large (1--10 GB each). Pre-download with `huggingface_hub` to avoid
the bench timing out during cold-start:

```bash
uv run --with huggingface_hub python -c "
from huggingface_hub import hf_hub_download
for repo, files in [
    ('ggml-org/gemma-4-E2B-it-GGUF', ['gemma-4-e2b-it-Q8_0.gguf', 'mmproj-gemma-4-e2b-it-f16.gguf']),
    ('ggml-org/gemma-4-E4B-it-GGUF', ['gemma-4-e4b-it-Q4_K_M.gguf', 'mmproj-gemma-4-e4b-it-f16.gguf']),
    ('unsloth/Qwen3.5-0.8B-GGUF', ['Qwen3.5-0.8B-Q8_0.gguf', 'mmproj-F16.gguf']),
    ('unsloth/Qwen3.5-2B-GGUF',   ['Qwen3.5-2B-Q8_0.gguf',   'mmproj-F16.gguf']),
    ('unsloth/Qwen3.5-4B-GGUF',   ['Qwen3.5-4B-Q8_0.gguf',   'mmproj-F16.gguf']),
    ('unsloth/Qwen3.5-9B-GGUF',   ['Qwen3.5-9B-Q8_0.gguf',   'mmproj-F16.gguf']),
]:
    for f in files:
        hf_hub_download(repo, f)
"
```

llama-server's built-in `-hf` resolver hangs on some Qwen repos even when files
are cached, so the bench loads via local `-m` paths it discovers under
`~/.cache/huggingface/hub/`.

## Usage

```bash
# Install project dependencies
uv sync

# Generate test chart for vision prompts
uv run python generate_test_image.py

# Run full benchmark (n=3 samples per prompt, ~1-2 hours total)
uv run python benchmark.py

# Run only one model variant (substring match)
uv run python benchmark.py --model gemma-4-e2b

# Run all thinking variants only
uv run python benchmark.py --model Q8_0-think

# Smaller sample size for a quick smoke test
uv run python benchmark.py -n 1
```

### Avoiding sleep mid-run

Long thinking-mode runs can take 30-60 minutes per model. Wrap with
`caffeinate -dimu` and `nohup` so a closed lid doesn't kill the process:

```bash
nohup caffeinate -dimu uv run python benchmark.py > /tmp/bench.log 2>&1 &
disown
```

After each model the bench writes `results/benchmark.<model>.json` so a crash
mid-run does not lose prior results.

## Test set (16 prompts, 7 categories)

Each prompt is sampled `n=3` times at temperature > 0; we report passes/n.
Verifiers go beyond substring matching:

| Category | Prompts | Verifier type |
|----------|---------|---------------|
| math | math_mul (23x17), math_div (144/12), math_percent (15% of 80) | numeric with tolerance |
| reasoning | word_speed (multi-step), word_age (algebra), 3 syllogisms | numeric / yes-no first-token |
| coding | code_total (sum), code_fizzbuzz | **executes the code** against test cases via subprocess |
| language | summarize (must include 'language model') | regex |
| translation | translate_fr_hello, translate_es_thanks | regex covering valid alternatives |
| vision | vision_max, vision_min, vision_diff (bar chart Q1-Q4) | numeric with tolerance |

## Sampling parameters

Each model uses vendor-recommended parameters; see `MODELS` in `benchmark.py`:

| Model family | Temperature | top_p | top_k | Source |
|--------------|-------------|-------|-------|--------|
| Gemma 4 | 1.0 | 0.95 | 64 | [Google AI docs](https://ai.google.dev/gemma/docs/core) |
| Qwen3.5 thinking on | 0.6 | 0.95 | 20 | [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/) |
| Qwen3.5 thinking off | 0.7 | 0.8 | 20 | same |

`min_p=0` is pinned explicitly on every Qwen request (server default may clip the tail).

## Server flags applied to all models

```
-ngl 99 -fa on -ub 1024 -c 16384 --cache-type-k q8_0 --cache-type-v q8_0
```

For Qwen vision: additional `--image-min-tokens 1024` (forces enough visual tokens for
chart/OCR reading -- Gemma's mmproj rejects this flag and gets it omitted).

For Qwen3.5-9B: `-c 8192` overrides default to leave KV cache headroom.

## Results

See `results/COMPARISON.md` for the full table and per-model breakdown.

### Summary on M4 16GB, n=3 (April 2026 benchmark)

| Model | Score | % | Wall time | tok/s (gen) |
|---|---|---|---|---|
| **Gemma 4 E2B Q8** | **48/48** | **100%** | 456s | 31.5 |
| Gemma 4 E4B Q4_K_M | 44/48 | 92% | 341s | 22.1 |
| Qwen3.5-0.8B nothink | 35/48 | 73% | 25s | 48.1 |
| Qwen3.5-0.8B think | 28/48 | 58% | 305s | 56.5 |
| Qwen3.5-2B nothink | 39/48 | 81% | 34s | 35.8 |
| Qwen3.5-2B think | 44/48 | 92% | 800s | 35.7 |
| Qwen3.5-4B nothink | 40/48 | 83% | 56s | 17.6 |
| **Qwen3.5-4B think** | **47/48** | **98%** | 1172s | 17.5 |

`tok/s (gen)` excludes attempts that emit fewer than 50 tokens (warmup-dominated).
`Wall time` is sum of all 48 attempt elapsed times for that model.

### Pareto frontier

- **Speed for accuracy**: Qwen3.5-2B nothink (39/48, 81% in 34s) -- best $ per pass
- **Best accuracy small**: Gemma 4 E2B (48/48, 100% in 456s)
- **Highest accuracy overall**: Qwen3.5-4B think (47/48, 98% in 1172s) -- 20x slower than nothink

### Observations

- Qwen3.5 thinking on `<= 2B` is a net loss -- the model loops on translation prompts
  and times out, costing 90% of wall time on three failed translations per model.
- Qwen3.5-4B think is the only Qwen variant that beats both Gemma E4B and its own
  no-think counterpart (96% vs 83%).
- 9B nothink (43/48, 90%) is no better than 2B nothink and 3x slower; 9B think
  was not run to completion.
- The penguin syllogism (`logic_syllogism_no`) trips bigger Qwen models -- they
  override the formal "yes follows from premises" with real-world knowledge.
