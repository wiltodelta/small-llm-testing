"""Benchmark small LLMs via llama.cpp server on Apple Silicon."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

log = logging.getLogger(__name__)

LLAMA_SERVER = "/opt/homebrew/bin/llama-server"
API_URL = "http://127.0.0.1:{port}/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:{port}/health"
RESULTS_DIR = Path(__file__).parent / "results"
ASSETS_DIR = Path(__file__).parent / "assets"
TEST_IMAGE = ASSETS_DIR / "test_chart.png"
HF_HUB_DIR = Path.home() / ".cache" / "huggingface" / "hub"

SERVER_STARTUP_TIMEOUT = 120  # seconds -- model must be pre-downloaded
REQUEST_TIMEOUT = 300
DEFAULT_PORT = 8080


@dataclass
class ModelConfig:
    name: str
    hf: str
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 64
    supports_vision: bool = True


MODELS: list[ModelConfig] = [
    # Gemma 4 (Google, March 2025) -- recommended: temp=1.0, top_p=0.95, top_k=64
    ModelConfig(
        name="gemma-4-e2b-Q8_0",
        hf="ggml-org/gemma-4-E2B-it-GGUF:gemma-4-e2b-it-Q8_0.gguf",
    ),
    ModelConfig(
        name="gemma-4-e4b-Q8_0",
        hf="ggml-org/gemma-4-E4B-it-GGUF:gemma-4-e4b-it-Q8_0.gguf",
    ),
]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


@dataclass
class Prompt:
    name: str
    category: str
    messages: list[dict[str, object]]
    vision: bool = False


def _user(text: str) -> list[dict[str, object]]:
    return [{"role": "user", "content": text}]


def _vision_user(image_path: Path, text: str) -> list[dict[str, object]]:
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
                {"type": "text", "text": text},
            ],
        },
    ]


PROMPTS: list[Prompt] = [
    Prompt(
        name="reasoning_math",
        category="reasoning",
        messages=_user(
            "Solve step by step: A train travels 120 km in 2 hours. "
            "It then speeds up by 20 km/h. How long does it take to travel the next 180 km?"
        ),
    ),
    Prompt(
        name="coding_python",
        category="coding",
        messages=_user(
            "Write a Python function that takes a list of integers and returns "
            "the longest increasing subsequence. Include type hints."
        ),
    ),
    Prompt(
        name="coding_rust",
        category="coding",
        messages=_user(
            "Write a Rust function that checks whether a given string is a valid IPv4 address. "
            "Do not use external crates."
        ),
    ),
    Prompt(
        name="creative_writing",
        category="creative",
        messages=_user("Write a short story (under 200 words) about a robot who discovers it can dream."),
    ),
    Prompt(
        name="summarization",
        category="language",
        messages=_user(
            "Summarize the following in 2-3 sentences: "
            "Large language models are trained on vast amounts of text data using "
            "self-supervised learning. They predict the next token in a sequence, "
            "which allows them to learn grammar, facts, reasoning abilities, and "
            "even some biases present in the training data. Fine-tuning and RLHF "
            "are then used to align the model with human preferences and make it "
            "more helpful and safe."
        ),
    ),
    Prompt(
        name="reasoning_logic",
        category="reasoning",
        messages=_user(
            "If all roses are flowers, and some flowers fade quickly, "
            "can we conclude that some roses fade quickly? Explain your reasoning."
        ),
    ),
    Prompt(
        name="multilingual",
        category="language",
        messages=_user(
            "Translate the following to French, German, and Japanese: 'The quick brown fox jumps over the lazy dog.'"
        ),
    ),
    Prompt(
        name="analysis",
        category="reasoning",
        messages=_user(
            "Compare and contrast microservices and monolithic architectures. Give 3 pros and 3 cons of each."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class PromptResult:
    prompt_name: str
    category: str
    tokens: int
    time_s: float
    tok_per_s: float
    response: str
    ok: bool


@dataclass
class ModelResult:
    model_name: str
    hf_id: str
    prompts: list[PromptResult]
    avg_tok_s: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for p in self.prompts if p.ok)

    @property
    def total(self) -> int:
        return len(self.prompts)


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------


def _is_model_downloaded(model: ModelConfig) -> bool:
    """Check if the model is already cached locally."""
    hf_repo = model.hf.split(":")[0]
    cache_name = f"models--{hf_repo.replace('/', '--')}"
    snapshots = HF_HUB_DIR / cache_name / "snapshots"
    if not snapshots.exists():
        return False
    return any(snapshots.iterdir())


def _wait_for_server(port: int, timeout: int = SERVER_STARTUP_TIMEOUT) -> None:
    """Poll the health endpoint until the server is ready."""
    health_url = HEALTH_URL.format(port=port)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    log.info("Server is ready on port %d", port)
                    return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(2)
    msg = f"Server did not become ready within {timeout}s on port {port}"
    raise TimeoutError(msg)


def _start_server(hf_model: str, port: int) -> subprocess.Popen[bytes]:
    """Start llama-server with the given HF model."""
    cmd = [LLAMA_SERVER, "-hf", hf_model, "--port", str(port)]
    log.info("Starting server: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _wait_for_server(port)
    return proc


def _stop_server(proc: subprocess.Popen[bytes]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    log.info("Server stopped")


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------


def _chat(messages: list[dict[str, object]], model_cfg: ModelConfig, port: int) -> tuple[str, int, float]:
    """Send a chat completion request. Returns (response_text, token_count, elapsed_s)."""
    api_url = API_URL.format(port=port)
    payload = json.dumps(
        {
            "messages": messages,
            "max_tokens": 4096,
            "temperature": model_cfg.temperature,
            "top_p": model_cfg.top_p,
            "top_k": model_cfg.top_k,
        },
        ensure_ascii=False,
    ).encode()

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        body = json.loads(resp.read().decode())
    elapsed = time.monotonic() - start

    text: str = body["choices"][0]["message"]["content"]
    tokens: int = body["usage"]["completion_tokens"]
    return text, tokens, elapsed


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def _run_prompt(prompt: Prompt, model_cfg: ModelConfig, port: int) -> PromptResult:
    log.info("  Running prompt: %s", prompt.name)
    try:
        text, tokens, elapsed = _chat(prompt.messages, model_cfg, port)
        tok_s = tokens / elapsed if elapsed > 0 else 0.0
        log.info("    %d tokens in %.1fs (%.1f tok/s)", tokens, elapsed, tok_s)
        return PromptResult(
            prompt_name=prompt.name,
            category=prompt.category,
            tokens=tokens,
            time_s=round(elapsed, 2),
            tok_per_s=round(tok_s, 1),
            response=text,
            ok=True,
        )
    except Exception:
        log.exception("    Failed: %s", prompt.name)
        return PromptResult(
            prompt_name=prompt.name,
            category=prompt.category,
            tokens=0,
            time_s=0.0,
            tok_per_s=0.0,
            response="",
            ok=False,
        )


def _build_prompts() -> list[Prompt]:
    """Build prompt list, adding vision prompt only if test image exists."""
    prompts = list(PROMPTS)
    if TEST_IMAGE.exists():
        prompts.append(
            Prompt(
                name="vision_chart",
                category="vision",
                messages=_vision_user(
                    TEST_IMAGE,
                    "Describe this chart. What quarter had the highest revenue? "
                    "What is the approximate difference between the highest and lowest values?",
                ),
                vision=True,
            ),
        )
    else:
        log.warning("Test image not found at %s -- skipping vision prompt", TEST_IMAGE)
    return prompts


def run_benchmark(
    models: list[ModelConfig] | None = None,
    port: int = DEFAULT_PORT,
) -> list[ModelResult]:
    """Run all prompts against all models."""
    if models is None:
        models = MODELS
    prompts = _build_prompts()
    results: list[ModelResult] = []

    for model in models:
        if not _is_model_downloaded(model):
            log.warning("Skipping %s -- not downloaded. See README for download instructions.", model.name)
            continue
        log.info("=== Model: %s ===", model.name)
        proc = _start_server(model.hf, port)
        try:
            mr = ModelResult(model_name=model.name, hf_id=model.hf, prompts=[])
            for prompt in prompts:
                if prompt.vision and not model.supports_vision:
                    log.info("  Skipping vision prompt for %s", model.name)
                    continue
                pr = _run_prompt(prompt, model, port)
                mr.prompts.append(pr)
            ok_results = [p for p in mr.prompts if p.ok]
            if ok_results:
                mr.avg_tok_s = round(sum(p.tok_per_s for p in ok_results) / len(ok_results), 1)
            results.append(mr)
        finally:
            _stop_server(proc)

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _save_json(results: list[ModelResult]) -> Path:
    path = RESULTS_DIR / "benchmark.json"
    data = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "models": [
            {
                "model": r.model_name,
                "hf_id": r.hf_id,
                "avg_tok_s": r.avg_tok_s,
                "prompts": [
                    {
                        "name": p.prompt_name,
                        "category": p.category,
                        "tokens": p.tokens,
                        "time_s": p.time_s,
                        "tok_per_s": p.tok_per_s,
                        "ok": p.ok,
                        "response": p.response,
                    }
                    for p in r.prompts
                ],
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    log.info("JSON results saved to %s", path)
    return path


def _save_markdown(results: list[ModelResult]) -> Path:
    path = RESULTS_DIR / "RESULTS.md"
    lines: list[str] = [
        "# Benchmark results",
        "",
        f"Generated: {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    lines.extend(
        [
            "## Summary",
            "",
            "| Model | Avg tok/s | Passed |",
            "|-------|-----------|--------|",
        ]
    )
    for r in results:
        lines.append(f"| {r.model_name} | {r.avg_tok_s} | {r.passed}/{r.total} |")
    lines.append("")

    for r in results:
        lines.extend(
            [
                f"## {r.model_name}",
                "",
                "| Prompt | Category | Tokens | Time (s) | tok/s | OK |",
                "|--------|----------|--------|----------|-------|----|",
            ]
        )
        for p in r.prompts:
            ok_str = "yes" if p.ok else "no"
            lines.append(f"| {p.prompt_name} | {p.category} | {p.tokens} | {p.time_s} | {p.tok_per_s} | {ok_str} |")
        lines.append("")

    path.write_text("\n".join(lines))
    log.info("Markdown results saved to %s", path)
    return path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark small LLMs on Apple Silicon")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Run only the model with this name (substring match)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    args = _parse_args()
    models = list(MODELS)

    if args.model:
        models = [m for m in models if args.model in m.name]
        if not models:
            log.error("No model matching '%s' found", args.model)
            return

    results = run_benchmark(models, port=args.port)
    RESULTS_DIR.mkdir(exist_ok=True)
    _save_json(results)
    _save_markdown(results)

    for r in results:
        log.info(
            "%s: avg %.1f tok/s, %d/%d passed",
            r.model_name,
            r.avg_tok_s,
            r.passed,
            r.total,
        )


if __name__ == "__main__":
    main()
