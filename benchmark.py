"""Benchmark small LLMs via llama.cpp server on Apple Silicon."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import re
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
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

SERVER_STARTUP_TIMEOUT = 300  # seconds -- 27B models take longer to mmap
REQUEST_TIMEOUT = 120  # cap per request -- thinking-mode loops on translation prompts; fail fast
DEFAULT_PORT = 8080
DEFAULT_N_RUNS = 3  # each prompt sampled this many times to smooth out temperature noise
PYEXEC_TIMEOUT = 5  # seconds budget per coding test execution


@dataclass
class ModelConfig:
    name: str
    hf: str
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 64
    supports_vision: bool = True
    server_args: tuple[str, ...] = ()
    # Qwen3 family ships thinking mode on by default; set False to disable via
    # chat_template_kwargs={"enable_thinking": False} on each request.
    thinking: bool = True
    # Qwen3 mmproj responds well to a higher floor on visual tokens (better OCR);
    # Gemma 4 mmproj caps image pixels lower and rejects this flag. Opt-in.
    image_min_tokens: int = 0


# MTP speculative-decoding flags (build 9380). The MTP head is embedded in the -MTP
# GGUF; --mmproj is unsupported with MTP, so MTP runs are vision-off and single-stream.
_MTP_ARGS: tuple[str, ...] = ("-np", "1", "--spec-type", "draft-mtp", "--spec-draft-n-max", "2")


def _qwen_matrix(
    label: str,
    base_repo: str,
    mtp_repo: str,
    gguf: str,
    extra_args: tuple[str, ...] = (),
) -> list[ModelConfig]:
    """Full {think, nothink} x {non-MTP, MTP} matrix for one Qwen model.

    Sampling per Qwen team: thinking on -> temp=0.6/top_p=0.95; off -> 0.7/0.8 (top_k=20).
    Non-MTP keeps vision on (image_min_tokens=1024); MTP is vision-off + draft-mtp flags.
    `extra_args` (e.g. ("-c", "8192") for the 27B) applies to both.
    """

    def make(thinking: bool, mtp: bool) -> ModelConfig:
        suffix = "think" if thinking else "nothink"
        temp, top_p = (0.6, 0.95) if thinking else (0.7, 0.8)
        return ModelConfig(
            name=f"{label}-mtp-{suffix}" if mtp else f"{label}-{suffix}",
            hf=f"{mtp_repo if mtp else base_repo}:{gguf}",
            temperature=temp,
            top_p=top_p,
            top_k=20,
            thinking=thinking,
            supports_vision=not mtp,  # --mmproj is unsupported with MTP
            image_min_tokens=0 if mtp else 1024,
            server_args=extra_args + _MTP_ARGS if mtp else extra_args,
        )

    return [make(thinking, mtp) for thinking in (True, False) for mtp in (False, True)]


MODELS: list[ModelConfig] = [
    # Gemma 4 (Google) -- no thinking mode, no MTP head: a single config each.
    # temp=1.0, top_p=0.95, top_k=64 (Gemma defaults on ModelConfig).
    ModelConfig(
        name="gemma-4-e2b-Q8_0",
        hf="ggml-org/gemma-4-E2B-it-GGUF:gemma-4-E2B-it-Q8_0.gguf",
    ),
    ModelConfig(
        name="gemma-4-e4b-Q4_K_M",
        hf="ggml-org/gemma-4-E4B-it-GGUF:gemma-4-E4B-it-Q4_K_M.gguf",
    ),
    # Gemma 4 26B-A4B MoE -- 26B total / 4B active. Q4_K_M ~16.8 GB + mmproj ~0.8 GB.
    # Was OOM on the old 16 GB machine; fits the 32 GB / ~25 GB working set at default ctx.
    ModelConfig(
        name="gemma-4-26b-a4b-Q4_K_M",
        hf="ggml-org/gemma-4-26B-A4B-it-GGUF:gemma-4-26B-A4B-it-Q4_K_M.gguf",
    ),
    # Qwen full matrix: {think, nothink} x {non-MTP, MTP}, 4 configs each.
    # Qwen3.5 small (Q8_0) fits at default ctx; Qwen 3.6 27B (Q4_K_M ~16.8 GB) uses -c 8192.
    # 0.8B dropped: too small to think productively (loops/timeouts, net loss). The MTP
    # heads ship in the -MTP repos for the whole Qwen 3.5/3.6 line.
    *_qwen_matrix("qwen3.5-2b-Q8_0", "unsloth/Qwen3.5-2B-GGUF", "unsloth/Qwen3.5-2B-MTP-GGUF", "Qwen3.5-2B-Q8_0.gguf"),
    *_qwen_matrix("qwen3.5-4b-Q8_0", "unsloth/Qwen3.5-4B-GGUF", "unsloth/Qwen3.5-4B-MTP-GGUF", "Qwen3.5-4B-Q8_0.gguf"),
    *_qwen_matrix("qwen3.5-9b-Q8_0", "unsloth/Qwen3.5-9B-GGUF", "unsloth/Qwen3.5-9B-MTP-GGUF", "Qwen3.5-9B-Q8_0.gguf"),
    *_qwen_matrix(
        "qwen3.6-27b-Q4_K_M",
        "unsloth/Qwen3.6-27B-GGUF",
        "unsloth/Qwen3.6-27B-MTP-GGUF",
        "Qwen3.6-27B-Q4_K_M.gguf",
        extra_args=("-c", "8192"),
    ),
    # Other families -- single instruct config each (no Qwen-style enable_thinking toggle,
    # no MTP head). Sampling from each model card where given, else neutral defaults
    # (temp>0 so the n=3 sampling actually varies).
    # Mistral Ministral 3 (Apache-2.0) -- multimodal (Pixtral-style mmproj). Card: temp<0.1
    # for production; top_p/top_k unspecified, left neutral. mmproj is auto-resolved.
    ModelConfig(
        name="ministral-3-8b-Q8_0",
        hf="mistralai/Ministral-3-8B-Instruct-2512-GGUF:Ministral-3-8B-Instruct-2512-Q8_0.gguf",
        temperature=0.15,
        top_p=1.0,
        top_k=0,
    ),
    ModelConfig(
        name="ministral-3-14b-Q4_K_M",
        hf="mistralai/Ministral-3-14B-Instruct-2512-GGUF:Ministral-3-14B-Instruct-2512-Q4_K_M.gguf",
        temperature=0.15,
        top_p=1.0,
        top_k=0,
    ),
    # Microsoft Phi-4-mini-instruct (MIT, text-only, standard instruct -- not reasoning).
    # Card gives no sampling rec; neutral defaults.
    ModelConfig(
        name="phi-4-mini-Q8_0",
        hf="unsloth/Phi-4-mini-instruct-GGUF:Phi-4-mini-instruct.Q8_0.gguf",
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        supports_vision=False,
    ),
    # Zhipu GLM-4.7-Flash (MIT, text-only) -- 30B-A3B MoE (3B active, so fast despite size).
    # Q4_K_M ~18.3 GB; -c 8192 keeps f16 KV in the working set. Card: temp=1.0, top_p=0.95.
    ModelConfig(
        name="glm-4.7-flash-Q4_K_M",
        hf="unsloth/GLM-4.7-Flash-GGUF:GLM-4.7-Flash-Q4_K_M.gguf",
        temperature=1.0,
        top_p=0.95,
        top_k=64,
        supports_vision=False,
        server_args=("-c", "8192"),
    ),
    # Qwen 3.6 35B-A3B MoE (UD-Q4_K_M ~22.1 GB) excluded: too marginal on the ~25 GB
    # working set (88% of it, even tighter with f16 KV). See README "Memory class reference".
]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


# A verifier returns (ok, reason). Reason is a short string explaining a failure.
Verifier = Callable[[str], "tuple[bool, str]"]


@dataclass
class Prompt:
    name: str
    category: str
    messages: list[dict[str, object]]
    verify: Verifier
    vision: bool = False


# ---- verifier helpers --------------------------------------------------------


def _strip_think(text: str) -> str:
    """Strip Qwen3 <think>...</think> blocks before checking the answer.

    Llama-server already strips closed think blocks into a separate field, but if
    the model dumps thinking in content (some templates do) we still want the answer.
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def v_regex(pattern: str, *, flags: int = re.IGNORECASE) -> Verifier:
    """Answer must match the given regex (re.search semantics)."""
    rx = re.compile(pattern, flags)

    def check(text: str) -> tuple[bool, str]:
        ans = _strip_think(text)
        if not ans:
            return False, "empty"
        return (True, "") if rx.search(ans) else (False, f"no regex match: {pattern}")

    return check


def v_number(expected: float, tol: float = 1e-6) -> Verifier:
    """Answer must contain a number equal to `expected` within tolerance."""

    def check(text: str) -> tuple[bool, str]:
        ans = _strip_think(text)
        if not ans:
            return False, "empty"
        # Find all decimal numbers in the answer (handles negatives and decimals).
        for m in re.finditer(r"-?\d+(?:\.\d+)?", ans):
            try:
                val = float(m.group())
            except ValueError:
                continue
            if abs(val - expected) <= tol:
                return True, ""
        return False, f"no number ~={expected}"

    return check


def v_yes_no(want_yes: bool) -> Verifier:
    """Answer's first yes/no token must match. Catches 'yes, but actually no' patterns."""

    def check(text: str) -> tuple[bool, str]:
        ans = _strip_think(text).lower()
        if not ans:
            return False, "empty"
        m = re.search(r"\b(yes|no)\b", ans)
        if not m:
            return False, "no yes/no token"
        first = m.group(1)
        want = "yes" if want_yes else "no"
        return (first == want, "" if first == want else f"first token was '{first}', want '{want}'")

    return check


def v_python_exec(test_cases: list[tuple[str, object]]) -> Verifier:
    """Extract a python code block, run it, then evaluate each test case.

    test_cases: list of (call_expression, expected_value), e.g.
        [("total([1,2,3])", 6), ("total([])", 0)].
    Returns (True, '') only if all cases match. Subprocess timeout = PYEXEC_TIMEOUT.
    """

    def extract_code(text: str) -> str:
        ans = _strip_think(text)
        # Prefer fenced ```python ... ``` blocks; fall back to first ``` block.
        m = re.search(r"```(?:python)?\s*\n(.*?)```", ans, flags=re.DOTALL)
        if m:
            return m.group(1)
        return ans  # raw response, hope it's parseable Python

    def check(text: str) -> tuple[bool, str]:
        code = extract_code(text)
        if not code.strip():
            return False, "empty"
        # Build a runner that imports the user code, evaluates each test, prints OK/MISMATCH.
        prefix = textwrap.dedent("""
            import sys, json
            ns = {}
            exec(compile(_USER_CODE_, '<llm>', 'exec'), ns)
        """).strip()
        # We pass user code via a sentinel substitution to avoid shell quoting issues.
        runner = "_USER_CODE_ = " + json.dumps(code) + "\n" + prefix + "\nresults = []\n"
        for call, want in test_cases:
            runner += (
                f"try:\n"
                f"    got = eval({json.dumps(call)}, ns)\n"
                f"    results.append((got == {json.dumps(want)}, repr(got)))\n"
                f"except Exception as e:\n"
                f"    results.append((False, f'EXC {{type(e).__name__}}: {{e}}'))\n"
            )
        runner += "print(json.dumps(results))\n"
        try:
            proc = subprocess.run(
                [sys.executable, "-c", runner],
                capture_output=True,
                text=True,
                timeout=PYEXEC_TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return False, "exec timeout"
        if proc.returncode != 0:
            err = (proc.stderr or "").strip().splitlines()[-1:] or ["unknown"]
            return False, f"exec error: {err[0][:80]}"
        try:
            results = json.loads(proc.stdout.strip())
        except json.JSONDecodeError:
            return False, "exec produced no JSON output"
        for i, (ok, got) in enumerate(results):
            if not ok:
                call, want = test_cases[i]
                return False, f"{call} -> {got}, want {want!r}"
        return True, ""

    return check


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


# Tighter answers + verifiable correctness. Each prompt is sampled DEFAULT_N_RUNS times
# at temperature > 0; we report passes/N. A 'pass' must contain the right answer,
# not just plausibly mention it.

# Vision prompt placeholders (messages filled in _build_prompts).
_VISION_MAX_PLACEHOLDER: list[dict[str, object]] = []
_VISION_MIN_PLACEHOLDER: list[dict[str, object]] = []
_VISION_DIFF_PLACEHOLDER: list[dict[str, object]] = []


# Discriminating core only. Trivial prompts that every model passes (math_div,
# math_percent, logic_syllogism_yes, code_total, translate_fr/es) and the brittle
# substring-matched summarize were dropped -- they added no signal and inflated
# scores toward the ceiling. What remains actually separates models: non-trivial
# arithmetic, multi-step word problems, a real-world-override logic trap, executed
# code, and chart OCR.
PROMPTS: list[Prompt] = [
    # ---- arithmetic (non-trivial multiplication) ----
    Prompt(
        name="math_mul",
        category="math",
        messages=_user("What is 23 multiplied by 17? Reply with only the number."),
        verify=v_number(391),
    ),
    # ---- word problems (multi-step reasoning) ----
    Prompt(
        name="word_speed",
        category="reasoning",
        messages=_user(
            "A train travels 120 km in 2 hours. Then it speeds up by 20 km/h. "
            "How long (in hours) does it take to travel the next 180 km? "
            "Reply with only the number."
        ),
        verify=v_number(2.25, tol=0.01),
    ),
    Prompt(
        name="word_age",
        category="reasoning",
        messages=_user(
            "Alice is twice as old as Bob. In 5 years, Alice will be 25. "
            "How old is Bob now? Reply with only the number."
        ),
        # Alice now = 20, Bob = 10
        verify=v_number(10),
    ),
    # ---- logic (real-world-knowledge override trap) ----
    Prompt(
        name="logic_syllogism_no",
        category="reasoning",
        messages=_user(
            "All birds can fly. Penguins are birds. From ONLY these two statements, "
            "can we logically conclude that penguins can fly? "
            "Answer with one word: yes or no."
        ),
        # Strict syllogism: yes follows formally. But many models trip on real-world
        # knowledge override. Honest answer per pure logic = yes.
        verify=v_yes_no(want_yes=True),
    ),
    Prompt(
        name="logic_negation",
        category="reasoning",
        messages=_user(
            "Some cars are not red. Therefore, no cars are red. "
            "Is this conclusion logically valid? Answer with one word: yes or no."
        ),
        verify=v_yes_no(want_yes=False),
    ),
    # ---- coding (executed against test cases) ----
    Prompt(
        name="code_fizzbuzz",
        category="coding",
        messages=_user(
            "Write a Python function `fizzbuzz(n: int) -> str` that returns "
            "'Fizz' if n is divisible by 3, 'Buzz' if divisible by 5, "
            "'FizzBuzz' if divisible by both, otherwise the number as a string. "
            "Reply with code only, in a single ```python``` block."
        ),
        verify=v_python_exec(
            [
                ("fizzbuzz(3)", "Fizz"),
                ("fizzbuzz(5)", "Buzz"),
                ("fizzbuzz(15)", "FizzBuzz"),
                ("fizzbuzz(7)", "7"),
                ("fizzbuzz(30)", "FizzBuzz"),
            ]
        ),
    ),
    # ---- vision (3 different questions on same chart) ----
    Prompt(
        name="vision_max",
        category="vision",
        messages=_VISION_MAX_PLACEHOLDER,
        verify=v_number(71),
        vision=True,
    ),
    Prompt(
        name="vision_min",
        category="vision",
        messages=_VISION_MIN_PLACEHOLDER,
        verify=v_number(35),
        vision=True,
    ),
    Prompt(
        name="vision_diff",
        category="vision",
        messages=_VISION_DIFF_PLACEHOLDER,
        verify=v_number(36),
        vision=True,
    ),
]


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class Attempt:
    tokens: int
    time_s: float
    response: str
    ok: bool
    fail_reason: str = ""


@dataclass
class PromptResult:
    prompt_name: str
    category: str
    attempts: list[Attempt] = field(default_factory=list[Attempt])

    @property
    def passes(self) -> int:
        return sum(1 for a in self.attempts if a.ok)

    @property
    def n(self) -> int:
        return len(self.attempts)

    @property
    def pass_rate(self) -> float:
        return (self.passes / self.n) if self.n else 0.0

    @property
    def total_time_s(self) -> float:
        return sum(a.time_s for a in self.attempts)

    @property
    def total_tokens(self) -> int:
        return sum(a.tokens for a in self.attempts)

    @property
    def gen_tok_per_s(self) -> float:
        """tok/s computed only over attempts that produced >=50 tokens (warmup-free)."""
        long_attempts = [a for a in self.attempts if a.tokens >= 50 and a.time_s > 0]
        if not long_attempts:
            return 0.0
        toks = sum(a.tokens for a in long_attempts)
        secs = sum(a.time_s for a in long_attempts)
        return toks / secs if secs > 0 else 0.0


@dataclass
class ModelResult:
    model_name: str
    hf_id: str
    prompts: list[PromptResult] = field(default_factory=list[PromptResult])

    @property
    def passes(self) -> int:
        """Sum of pass-rates across prompts (e.g. 6.67 / 14)."""
        return sum(p.passes for p in self.prompts)

    @property
    def attempts_total(self) -> int:
        return sum(p.n for p in self.prompts)

    @property
    def total_time_s(self) -> float:
        return sum(p.total_time_s for p in self.prompts)

    @property
    def gen_tok_per_s(self) -> float:
        long_attempts = [a for p in self.prompts for a in p.attempts if a.tokens >= 50 and a.time_s > 0]
        if not long_attempts:
            return 0.0
        toks = sum(a.tokens for a in long_attempts)
        secs = sum(a.time_s for a in long_attempts)
        return toks / secs if secs > 0 else 0.0


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------


def _resolve_local_paths(hf_spec: str) -> tuple[Path, Path | None] | None:
    """Resolve cached local paths for an HF model spec 'repo:filename'.

    Returns (model_path, mmproj_path or None) or None if not cached.
    The llama-server '-hf' resolver hangs on some Qwen repos even when files are
    cached, so we always start with '-m' pointing at the local file. Prefers
    mmproj-BF16 (Qwen models train in bf16; better dynamic range than F16).
    """
    hf_repo, _, filename = hf_spec.partition(":")
    if not filename:
        return None
    cache_name = f"models--{hf_repo.replace('/', '--')}"
    snapshots = HF_HUB_DIR / cache_name / "snapshots"
    if not snapshots.exists():
        return None
    # Prefer snapshots that include an mmproj projector (multiple snapshot dirs may
    # exist from interrupted downloads; the first one iterdir() returns may be partial).
    best: tuple[Path, Path | None] | None = None
    for snap in snapshots.iterdir():
        model_path = snap / filename
        if not model_path.exists():
            continue
        mmproj: Path | None = None
        for preferred in ("mmproj-BF16.gguf", "mmproj-F16.gguf", "mmproj-F32.gguf"):
            cand = snap / preferred
            if cand.exists():
                mmproj = cand
                break
        if mmproj is None:
            # Match both leading (mmproj-F16.gguf, Qwen/Gemma) and trailing
            # (Ministral-...-BF16-mmproj.gguf, Mistral) projector names.
            mmproj = next(iter(snap.glob("*mmproj*.gguf")), None)
        if mmproj is not None:
            return model_path, mmproj
        if best is None:
            best = (model_path, None)
    return best


def _is_model_downloaded(model: ModelConfig) -> bool:
    """Check if the model is already cached locally."""
    return _resolve_local_paths(model.hf) is not None


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


# Best-practice defaults for Apple Silicon Metal + Qwen3 family.
# -ngl 99: full GPU offload (no-op safety on Apple). -fa on: flash attention (Metal-supported).
# -ub 1024: larger ubatch speeds up prompt processing for vision/long prompts.
# KV cache is left at the f16 default. On the 32 GB machine all models (incl. 27B at
# -c 8192 and gemma-26b at -c 16384) fit with f16 KV, and f16 is measurably faster than
# the old q8_0 KV: llama-bench on Qwen3.6-27B Q4_K_M (M5, build 9380) gave tg128 6.32 t/s
# (f16/f16) vs 3.72 t/s (q8_0/q8_0) -- 1.7x. Quantized K on Metal is especially costly.
# q8_0 KV was a 16 GB-machine memory hack; drop it here. (fa stays on -- it helps with
# f16 KV too, and is required only IF KV is quantized.)
DEFAULT_SERVER_ARGS: tuple[str, ...] = (
    "-ngl",
    "99",
    "-fa",
    "on",
    "-ub",
    "1024",
    "-c",
    "16384",
)


def _start_server(model: ModelConfig, port: int) -> subprocess.Popen[bytes]:
    """Start llama-server with the given model config (uses local cached file via -m)."""
    paths = _resolve_local_paths(model.hf)
    if paths is None:
        msg = f"Model file not cached: {model.hf}"
        raise FileNotFoundError(msg)
    model_path, mmproj_path = paths
    # Per-model server_args override defaults for the same flag (last value wins in llama-server).
    cmd = [
        LLAMA_SERVER,
        "-m",
        str(model_path),
        "--port",
        str(port),
        *DEFAULT_SERVER_ARGS,
        *model.server_args,
    ]
    if mmproj_path is not None and model.supports_vision:
        cmd.extend(["--mmproj", str(mmproj_path)])
        if model.image_min_tokens > 0:
            # Forces enough visual tokens for OCR / chart reading. Qwen3 mmproj
            # supports up to ~2048; Gemma 4 mmproj rejects this flag.
            cmd.extend(["--image-min-tokens", str(model.image_min_tokens)])
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


def _chat(
    messages: list[dict[str, object]], model_cfg: ModelConfig, port: int, *, thinking: bool
) -> tuple[str, int, float]:
    """Send a chat completion request. Returns (response_text, token_count, elapsed_s).

    `thinking` is the effective per-request decision (see `_thinks` for the per-category
    gate), not necessarily `model_cfg.thinking`.
    """
    api_url = API_URL.format(port=port)
    # Qwen3 thinking mode needs much more headroom: official guidance is up to 32k for
    # general tasks, 80k+ for math/code. 4k overflows even the 0.8B inside <think>.
    max_tokens = 16384 if thinking else 4096
    req_body: dict[str, object] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": model_cfg.temperature,
        "top_p": model_cfg.top_p,
        "top_k": model_cfg.top_k,
        # Qwen team recommendation: explicitly pin min_p=0 (server default may clip the tail).
        "min_p": 0,
    }
    if not thinking:
        req_body["chat_template_kwargs"] = {"enable_thinking": False}
    payload = json.dumps(req_body, ensure_ascii=False).encode()

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


# Thinking only helps on multi-step work; on short-answer categories (vision chart
# reads) it loops and burns the request timeout for no accuracy gain. So even a -think
# config thinks ONLY on these categories; everything else runs direct.
THINKING_CATEGORIES: frozenset[str] = frozenset({"math", "reasoning", "coding"})


def _thinks(model_cfg: ModelConfig, prompt: Prompt) -> bool:
    """Effective thinking for this (model, prompt): the config must enable it AND the
    prompt's category must be one where thinking pays off."""
    return model_cfg.thinking and prompt.category in THINKING_CATEGORIES


def _run_one_attempt(prompt: Prompt, model_cfg: ModelConfig, port: int) -> Attempt:
    try:
        text, tokens, elapsed = _chat(prompt.messages, model_cfg, port, thinking=_thinks(model_cfg, prompt))
    except Exception as e:
        log.warning("    api error: %s", e)
        return Attempt(tokens=0, time_s=0.0, response="", ok=False, fail_reason=f"api error: {type(e).__name__}")
    ok, reason = prompt.verify(text)
    return Attempt(tokens=tokens, time_s=round(elapsed, 2), response=text, ok=ok, fail_reason=reason)


def _run_prompt(prompt: Prompt, model_cfg: ModelConfig, port: int, n: int) -> PromptResult:
    log.info("  Running prompt: %s (n=%d)", prompt.name, n)
    result = PromptResult(prompt_name=prompt.name, category=prompt.category)
    for i in range(n):
        a = _run_one_attempt(prompt, model_cfg, port)
        result.attempts.append(a)
        status = "PASS" if a.ok else f"FAIL ({a.fail_reason})"
        log.info("    [%d/%d] %d tok in %.1fs -- %s", i + 1, n, a.tokens, a.time_s, status)
    log.info("    => %d/%d pass, %.1fs total", result.passes, result.n, result.total_time_s)
    return result


# Per-name vision question text. Test chart shows Q1=$42M, Q2=$58M, Q3=$35M, Q4=$71M.
_VISION_QUESTIONS: dict[str, str] = {
    "vision_max": (
        "Look at this bar chart. What is the value of the tallest bar? Reply with just the number (no units, no $)."
    ),
    "vision_min": (
        "Look at this bar chart. What is the value of the shortest bar? Reply with just the number (no units, no $)."
    ),
    "vision_diff": (
        "Look at this bar chart. Subtract the shortest bar's value from the tallest bar's value. "
        "Reply with just the resulting number (no units, no $)."
    ),
}


def _build_prompts() -> list[Prompt]:
    """Build prompt list. Vision prompts get their messages filled in if the image exists."""
    prompts: list[Prompt] = []
    for p in PROMPTS:
        if p.vision:
            if not TEST_IMAGE.exists():
                log.warning("Skipping vision prompt %s -- test image missing at %s", p.name, TEST_IMAGE)
                continue
            question = _VISION_QUESTIONS.get(p.name)
            if question is None:
                log.warning("No vision question registered for %s -- skipping", p.name)
                continue
            p = Prompt(
                name=p.name,
                category=p.category,
                messages=_vision_user(TEST_IMAGE, question),
                verify=p.verify,
                vision=True,
            )
        prompts.append(p)
    return prompts


def run_benchmark(
    models: list[ModelConfig] | None = None,
    port: int = DEFAULT_PORT,
    n: int = DEFAULT_N_RUNS,
) -> list[ModelResult]:
    """Run all prompts against all models. Each prompt is sampled `n` times."""
    if models is None:
        models = MODELS
    prompts = _build_prompts()
    results: list[ModelResult] = []

    for model in models:
        if not _is_model_downloaded(model):
            log.warning("Skipping %s -- not downloaded. See README for download instructions.", model.name)
            continue
        log.info("=== Model: %s ===", model.name)
        proc = _start_server(model, port)
        try:
            mr = ModelResult(model_name=model.name, hf_id=model.hf)
            for prompt in prompts:
                if prompt.vision and not model.supports_vision:
                    log.info("  Skipping vision prompt for %s", model.name)
                    continue
                pr = _run_prompt(prompt, model, port, n)
                mr.prompts.append(pr)
            results.append(mr)
            # Persist after each model so a crash/sleep does not lose prior results.
            RESULTS_DIR.mkdir(exist_ok=True)
            _save_json(results)
            _save_markdown(results)
            per_model_path = RESULTS_DIR / f"benchmark.{model.name}.json"
            per_model_path.write_text(
                json.dumps(
                    {"timestamp": datetime.now(tz=UTC).isoformat(), "models": [_model_to_dict(mr)]},
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
            log.info("Saved per-model results: %s", per_model_path)
        finally:
            _stop_server(proc)

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _model_to_dict(r: ModelResult) -> dict[str, object]:
    return {
        "model": r.model_name,
        "hf_id": r.hf_id,
        "passes": r.passes,
        "attempts_total": r.attempts_total,
        "total_time_s": round(r.total_time_s, 2),
        "gen_tok_per_s": round(r.gen_tok_per_s, 1),
        "prompts": [
            {
                "name": p.prompt_name,
                "category": p.category,
                "passes": p.passes,
                "n": p.n,
                "pass_rate": round(p.pass_rate, 3),
                "total_tokens": p.total_tokens,
                "total_time_s": round(p.total_time_s, 2),
                "attempts": [
                    {
                        "tokens": a.tokens,
                        "time_s": a.time_s,
                        "ok": a.ok,
                        "fail_reason": a.fail_reason,
                        "response": a.response,
                    }
                    for a in p.attempts
                ],
            }
            for p in r.prompts
        ],
    }


def _save_json(results: list[ModelResult]) -> Path:
    path = RESULTS_DIR / "benchmark.json"
    data = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "models": [_model_to_dict(r) for r in results],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    log.info("JSON results saved to %s", path)
    return path


def fail_kind(reason: str) -> str:
    """Classify a failed attempt so 'too slow' is not conflated with 'wrong answer':
    'timeout' (ran past REQUEST_TIMEOUT), 'empty' (no usable output / api error),
    or 'wrong' (finished but the verifier rejected the answer)."""
    low = reason.lower()
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if reason == "empty" or low.startswith("api error"):
        return "empty"
    return "wrong"


def _save_markdown(results: list[ModelResult]) -> Path:
    path = RESULTS_DIR / "RESULTS.md"
    lines: list[str] = [
        "# Benchmark results",
        "",
        f"Generated: {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Each prompt sampled multiple times; cell shows passes/n.",
        "Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.",
        "Fails split as wrong/timeout/empty -- a timeout is too-slow-to-finish, not a wrong answer.",
        "",
        "## Summary",
        "",
        "| Model | Passes | Fails (wrong/timeout/empty) | Total time | tok/s (gen, long-only) |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        fails = [fail_kind(a.fail_reason) for p in r.prompts for a in p.attempts if not a.ok]
        w, t, e = (fails.count("wrong"), fails.count("timeout"), fails.count("empty"))
        lines.append(
            f"| {r.model_name} | {r.passes}/{r.attempts_total} | {w}/{t}/{e} | "
            f"{r.total_time_s:.1f}s | {r.gen_tok_per_s:.1f} |"
        )
    lines.append("")

    for r in results:
        lines.extend(
            [
                f"## {r.model_name}",
                "",
                "| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |",
                "|---|---|---|---|---|---|",
            ]
        )
        for p in r.prompts:
            first_fail = next((a.fail_reason for a in p.attempts if not a.ok), "")
            lines.append(
                f"| {p.prompt_name} | {p.category} | {p.passes}/{p.n} | "
                f"{p.total_tokens} | {p.total_time_s:.1f} | {first_fail} |"
            )
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
    parser.add_argument(
        "-n",
        "--n-runs",
        type=int,
        default=DEFAULT_N_RUNS,
        help=f"Sample each prompt this many times (default: {DEFAULT_N_RUNS})",
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

    results = run_benchmark(models, port=args.port, n=args.n_runs)
    RESULTS_DIR.mkdir(exist_ok=True)
    _save_json(results)
    _save_markdown(results)

    for r in results:
        log.info(
            "%s: %d/%d pass in %.1fs, %.1f tok/s",
            r.model_name,
            r.passes,
            r.attempts_total,
            r.total_time_s,
            r.gen_tok_per_s,
        )


if __name__ == "__main__":
    main()
