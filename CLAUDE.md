# small-llm-testing

Benchmark small LLMs locally via llama.cpp on Apple Silicon M4 16GB.

## How to run

```bash
# Install dependencies
uv sync

# Generate test chart for vision prompts
uv run python generate_test_image.py

# Run benchmark (starts/stops llama-server automatically)
uv run python benchmark.py
```

Default llama-server port: **8080**.

## Scripts

- `maintain.sh` -- uv sync + ruff check/fix + format + pyright
- `benchmark.py` -- main benchmark (9 prompts, 2 models)
- `generate_test_image.py` -- creates `assets/test_chart.png` for vision test

## Configuration

- Models and sampling parameters are configured in `MODELS` list in `benchmark.py`
- Each model has its own `temperature`, `top_p`, `top_k` (vendor-recommended defaults)
- llama-server binary: `/opt/homebrew/bin/llama-server`

## Output

- `results/benchmark.json` -- raw results with full responses
- `results/RESULTS.md` -- formatted summary table
