# small-llm-testing

Benchmark small LLMs locally via [llama.cpp](https://github.com/ggml-org/llama.cpp) on Apple Silicon.

## Models

| Model | Parameters | Quant | Release | Announcement |
|-------|-----------|-------|---------|--------------|
| [Gemma 4 E2B](https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF) | 2B | Q8_0 | March 2025 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |
| [Gemma 4 E4B](https://huggingface.co/ggml-org/gemma-4-E4B-it-GGUF) | 4B | Q8_0 | March 2025 | [Gemma 4: Byte for byte, the most capable open models](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/) |

### Models that don't work on 16 GB

| Model | Issue |
|-------|-------|
| Gemma 4 26B-A4B | OOM -- needs 24+ GB RAM |
| Qwen 3.5 9B | OOM -- hybrid SSM+Attention architecture requires ~12 GB KV cache even with IQ2_M quant |
| Phi-4-Reasoning 15B | Too slow (7.9 tok/s), most prompts timeout |
| MLX backend (all models) | `mlx-lm` does not support `gemma4` architecture as of April 2026 |

## Hardware

- MacBook Air (M4, 2025)
- Apple M4 (10-core CPU, 10-core GPU)
- 16 GB unified memory
- macOS Tahoe

## Prerequisites

```bash
brew install llama.cpp
```

## Download models first

Models are large (5--10 GB each). Download them before running the benchmark to avoid timeouts.

```bash
# Run one at a time, wait for "server is listening", then Ctrl-C
llama-server -hf ggml-org/gemma-4-E2B-it-GGUF:gemma-4-e2b-it-Q8_0.gguf --port 8080
llama-server -hf ggml-org/gemma-4-E4B-it-GGUF:gemma-4-e4b-it-Q8_0.gguf --port 8080
```

Models are cached in `~/.cache/huggingface/hub/` and reused across runs.

## Usage

```bash
# Install project dependencies
uv sync

# Generate test chart for vision prompts
uv run python generate_test_image.py

# Run full benchmark
uv run python benchmark.py

# Run a specific model
uv run python benchmark.py --model gemma-4-e2b

# Custom port (default: 8080)
uv run python benchmark.py --port 8081
```

## Prompts

9 prompts across 5 categories:

| Category | Prompts |
|----------|---------|
| Reasoning | reasoning_math, reasoning_logic, analysis |
| Coding | coding_python, coding_rust |
| Language | summarization, multilingual |
| Creative | creative_writing |
| Vision | vision_chart (bar chart reading) |

## Sampling parameters

Each model uses vendor-recommended parameters:

| Model | Temperature | top_p | top_k | Source |
|-------|-------------|-------|-------|--------|
| Gemma 4 | 1.0 | 0.95 | 64 | [Google AI docs](https://ai.google.dev/gemma/docs/core) |

## Results

Results are saved to `results/benchmark.json` (raw) and `results/RESULTS.md` (formatted table).

### Gemma 4 on M4 16GB (llama.cpp)

| Model | Avg tok/s | Passed |
|-------|-----------|--------|
| gemma-4-e2b-Q8_0 | ~34 | 9/9 |
| gemma-4-e4b-Q8_0 | ~25 | 9/9 |

- E2B is ~35% faster, E4B produces higher quality answers (especially vision and math)
- Both models handle all 9 prompts including vision
- Gemma 4 26B-A4B does not fit in 16 GB RAM
