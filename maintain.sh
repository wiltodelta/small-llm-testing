#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

uv sync
uv run uv-outdated
uv run uv-secure --ignore-unfixed
uv run ruff check --fix
uv run ruff format
uv run pyright
uv run pytest -n auto
