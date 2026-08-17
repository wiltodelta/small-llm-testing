"""Benchmark small LLMs via llama.cpp server on Apple Silicon."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

log = logging.getLogger(__name__)

LLAMA_SERVER = "/opt/homebrew/bin/llama-server"
API_URL = "http://127.0.0.1:{port}/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:{port}/health"
RESULTS_DIR = Path(__file__).parent / "results"
HF_HUB_DIR = Path.home() / ".cache" / "huggingface" / "hub"

SERVER_STARTUP_TIMEOUT = 300  # seconds -- 27B models take longer to mmap
REQUEST_TIMEOUT = 300  # cap per request. Was 120: on slow dense models (27B at ~5 tok/s)
# think-mode coding drowned in timeouts rather than wrong answers -- the root cause was
# decode speed, not loops (presence_penalty verified, did not help). 300s covers
# think-mode coding at the slowest decode we benchmark while still failing real hangs.
DEFAULT_PORT = 8080
DEFAULT_N_RUNS = 3  # each prompt sampled this many times to smooth out temperature noise
PYEXEC_TIMEOUT = 5  # seconds budget per coding test execution


@dataclass(frozen=True)
class SamplingPreset:
    """Per-request sampler values for a model's alternate generation mode."""

    temperature: float
    top_p: float
    top_k: int
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.0


@dataclass
class ModelConfig:
    name: str
    hf: str
    # Optional immutable Hugging Face commit for reproducible cache resolution.
    revision: str | None = None
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 64
    # Vendor anti-repetition knobs (defaults are no-ops). presence_penalty is OpenAI-style;
    # repetition_penalty maps to llama.cpp `repeat_penalty` (1.0 = off).
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.0
    server_args: tuple[str, ...] = ()
    # `thinking` gates whether this config thinks on THINKING_CATEGORIES. It is enforced
    # per request via chat_template_kwargs when the model's template supports the toggle.
    thinking: bool = True
    # Muse Glimmer uses a named reasoning strength instead of enable_thinking. When set,
    # _chat requests this strength for thinking categories and `low` for direct prompts.
    reasoning_strength: str | None = None
    # Some hybrid models publish different samplers for thinking and direct modes.
    # When set, direct prompts use this preset instead of the fields above.
    direct_sampling: SamplingPreset | None = None
    # OpenAI-compatible reasoning effort for models trained on named effort levels.
    reasoning_effort: str | None = None


def _gemma_pair(label: str, hf: str, extra_args: tuple[str, ...] = ()) -> list[ModelConfig]:
    """Return think and no-think configs for one Gemma 4 model."""
    return [
        ModelConfig(name=f"{label}-think", hf=hf, thinking=True, server_args=extra_args),
        ModelConfig(name=f"{label}-nothink", hf=hf, thinking=False, server_args=extra_args),
    ]


MODELS: list[ModelConfig] = [
    # Curated routine core from the 2026-07-29 full run. Gemma E2B is the compact
    # speed/accuracy reference; 26B-A4B is the fast interactive MoE reference. Each runs
    # a think + nothink pair so the mode tradeoff remains visible. Unsloth's separate
    # `mtp-*.gguf` draft heads are auto-attached by _start_server for lossless MTP.
    *_gemma_pair("gemma-4-e2b-Q8_0", "unsloth/gemma-4-E2B-it-GGUF:gemma-4-E2B-it-Q8_0.gguf"),
    *_gemma_pair("gemma-4-26b-a4b-Q4_K_M", "unsloth/gemma-4-26B-A4B-it-GGUF:gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"),
    # Compact MoE alternatives: LFM is the 1.5B-active edge reference; Mellum2 is the
    # coding/reasoning leader from the full run.
    ModelConfig(
        name="lfm2.5-8b-a1b-Q8_0",
        hf="LiquidAI/LFM2.5-8B-A1B-GGUF:LFM2.5-8B-A1B-Q8_0.gguf",
        temperature=0.2,
        top_p=1.0,
        top_k=80,
        repetition_penalty=1.05,
    ),
    ModelConfig(
        name="mellum2-12b-a2.5b-think-Q4_K_M",
        hf="JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M:Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf",
        temperature=0.6,
        top_p=0.95,
        top_k=20,
    ),
]

# Dated challengers remain outside the default routine so a normal benchmark does not
# silently grow. Use --include-challengers for the routine plus current challengers,
# --full-sweep to add North Mini Code, or --model to select one config directly.
CHALLENGERS: list[ModelConfig] = [
    ModelConfig(
        name="lfm2.5-2.6b-Q8_0",
        hf="LiquidAI/LFM2.5-2.6B-GGUF:LFM2.5-2.6B-Q8_0.gguf",
        temperature=0.1,
        top_p=1.0,
        top_k=50,
        repetition_penalty=1.1,
        thinking=False,
    ),
    ModelConfig(
        name="nanbeige4.2-3b-Q8_0-think",
        hf="mradermacher/Nanbeige4.2-3B-GGUF:Nanbeige4.2-3B.Q8_0.gguf",
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        thinking=True,
    ),
    ModelConfig(
        name="nanbeige4.2-3b-Q8_0-nothink",
        hf="mradermacher/Nanbeige4.2-3B-GGUF:Nanbeige4.2-3B.Q8_0.gguf",
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        thinking=False,
    ),
    ModelConfig(
        name="qwen3.8-27b-Q4_K_M-think",
        hf="unsloth/Qwen3.8-27B-GGUF:Qwen3.8-27B-Q4_K_M.gguf",
        revision="fdd03b8bbd279c1694563650e79d85a2373d9934",
        temperature=1.0,
        top_p=0.95,
        top_k=20,
        thinking=True,
        direct_sampling=SamplingPreset(
            temperature=0.7,
            top_p=0.8,
            top_k=20,
            presence_penalty=1.5,
        ),
        reasoning_effort="xhigh",
    ),
    ModelConfig(
        name="qwen3.8-27b-Q4_K_M-nothink",
        hf="unsloth/Qwen3.8-27B-GGUF:Qwen3.8-27B-Q4_K_M.gguf",
        revision="fdd03b8bbd279c1694563650e79d85a2373d9934",
        temperature=0.7,
        top_p=0.8,
        top_k=20,
        presence_penalty=1.5,
        thinking=False,
    ),
    ModelConfig(
        name="nemotron-3.5-lightning-30b-a3b-Q3_K_M",
        hf=("bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF:NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Q3_K_M.gguf"),
        temperature=1.0,
        top_p=0.95,
        top_k=0,
        server_args=("--spec-type", "draft-mtp"),
    ),
    ModelConfig(
        name="muse-glimmer-30b-high-Q4_K_XL",
        hf="unsloth/Muse-Glimmer-30B-GGUF:Muse-Glimmer-30B-UD-Q4_K_XL.gguf",
        temperature=1.0,
        top_p=0.95,
        top_k=64,
        reasoning_strength="high",
    ),
]

AGENTIC_TEXT_MODELS: list[ModelConfig] = [
    ModelConfig(
        name="north-mini-code-1.0-Q4_K_M",
        hf="unsloth/North-Mini-Code-1.0-GGUF:North-Mini-Code-1.0-UD-Q4_K_M.gguf",
        temperature=1.0,
        top_p=0.95,
        top_k=0,
        server_args=("-c", "8192"),
    )
]

CURRENT_TEXT_MODELS: tuple[ModelConfig, ...] = (*MODELS, *CHALLENGERS)
FULL_SWEEP_MODELS: tuple[ModelConfig, ...] = (
    *CURRENT_TEXT_MODELS,
    *AGENTIC_TEXT_MODELS,
)


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


# ---- verifier helpers --------------------------------------------------------

# Fixed verifier patterns, compiled once (each runs on every attempt across the suite).
_THINK_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL)
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", flags=re.DOTALL)


def _strip_think(text: str) -> str:
    """Strip Qwen3 <think>...</think> blocks before checking the answer.

    Llama-server already strips closed think blocks into a separate field, but if
    the model dumps thinking in content (some templates do) we still want the answer.
    """
    return _THINK_RE.sub("", text).strip()


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
        for m in _NUMBER_RE.finditer(ans):
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
        m = _CODE_FENCE_RE.search(ans)
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
        runner = f"_USER_CODE_ = {json.dumps(code)}\n{prefix}\nresults = []\n"
        for call, want in test_cases:
            runner += (
                f"try:\n"
                f"    got = eval({json.dumps(call)}, ns)\n"
                # repr() emits a valid Python literal for the expected value; json.dumps
                # would turn True/False/None into true/false/null (a NameError at exec).
                f"    results.append((got == {want!r}, repr(got)))\n"
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


def v_json(expected: dict[str, object]) -> Verifier:
    """Answer must contain a JSON object whose keys match `expected`.

    Tolerates a ```json``` fence or surrounding prose: the span from the first '{'
    to the last '}' is parsed. Numbers compare by value (34 == "34" == 34.0);
    strings compare case-insensitively after stripping. Tests structured-output /
    instruction-following, the strength of agentic / function-calling models.
    """

    def check(text: str) -> tuple[bool, str]:
        ans = _strip_think(text)
        start, end = ans.find("{"), ans.rfind("}")
        if start == -1 or end <= start:
            return False, "no JSON object"
        try:
            parsed: object = json.loads(ans[start : end + 1])
        except json.JSONDecodeError:
            return False, "invalid JSON"
        if not isinstance(parsed, dict):
            return False, "JSON is not an object"
        obj = cast("dict[str, object]", parsed)
        for key, want in expected.items():
            if key not in obj:
                return False, f"missing key '{key}'"
            got: object = obj[key]
            if isinstance(want, bool):
                if got != want:
                    return False, f"{key}={got!r}, want {want!r}"
            elif isinstance(want, (int, float)):
                if isinstance(got, bool) or not isinstance(got, (int, float, str)):
                    return False, f"{key}={got!r} not numeric"
                try:
                    if abs(float(got) - float(want)) > 1e-6:
                        return False, f"{key}={got!r}, want {want!r}"
                except ValueError:
                    return False, f"{key}={got!r} not numeric"
            elif isinstance(want, str):
                if str(got).strip().lower() != want.strip().lower():
                    return False, f"{key}={got!r}, want {want!r}"
            elif got != want:
                return False, f"{key}={got!r}, want {want!r}"
        return True, ""

    return check


def _user(text: str) -> list[dict[str, object]]:
    return [{"role": "user", "content": text}]


# Tighter answers + verifiable correctness. Each prompt is sampled DEFAULT_N_RUNS times
# at temperature > 0; we report passes/N. A 'pass' must contain the right answer,
# not just plausibly mention it.

# Discriminating, mechanically-verifiable text core across four dimensions: math (3),
# reasoning (4), coding (3, executed), structured output (2, JSON / strict format).
# Trivial prompts that every model passed (math_div, math_percent, logic_syllogism_yes,
# code_total, translate_fr/es) and the brittle substring-matched summarize were dropped.
# The structured dimension probes instruction-following and function-calling behavior.
# No LLM judge: every prompt verifies by number / yes-no / regex / executed code / parsed JSON.
PROMPTS: list[Prompt] = [
    # ---- arithmetic (non-trivial, multi-step) ----
    Prompt(
        name="math_mul",
        category="math",
        messages=_user("What is 23 multiplied by 17? Reply with only the number."),
        verify=v_number(391),
    ),
    Prompt(
        name="math_multistep",
        category="math",
        messages=_user("Compute (45 + 17) * 3 - 28. Reply with only the number."),
        # 62 * 3 = 186; 186 - 28 = 158
        verify=v_number(158),
    ),
    Prompt(
        name="math_modular",
        category="math",
        messages=_user("What is 2 raised to the power of 10, modulo 1000? Reply with only the number."),
        # 1024 mod 1000 = 24 (catches models that drop the mod step and answer 1024)
        verify=v_number(24),
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
    Prompt(
        name="code_palindrome",
        category="coding",
        messages=_user(
            "Write a Python function `is_palindrome(s: str) -> bool` that returns True if `s` "
            "reads the same forwards and backwards, ignoring case and any non-alphanumeric "
            "characters. Reply with code only, in a single ```python``` block."
        ),
        verify=v_python_exec(
            [
                ("is_palindrome('A man, a plan, a canal: Panama')", True),
                ("is_palindrome('hello')", False),
                ("is_palindrome('Was it a car or a cat I saw?')", True),
                ("is_palindrome('')", True),
                ("is_palindrome('No lemon, no melon')", True),
            ]
        ),
    ),
    Prompt(
        name="code_reverse_words",
        category="coding",
        messages=_user(
            "Write a Python function `reverse_words(s: str) -> str` that returns the words of `s` "
            "in reverse order, separated by single spaces, with leading and trailing whitespace "
            "removed. Reply with code only, in a single ```python``` block."
        ),
        verify=v_python_exec(
            [
                ("reverse_words('the sky is blue')", "blue is sky the"),
                ("reverse_words('  hello   world  ')", "world hello"),
                ("reverse_words('a')", "a"),
                ("reverse_words('one two')", "two one"),
            ]
        ),
    ),
    # ---- structured output / instruction-following (JSON, strict format) ----
    Prompt(
        name="json_person",
        category="structured",
        messages=_user(
            "Extract the person's name and age from this sentence into a JSON object with "
            'exactly the keys "name" (string) and "age" (integer): '
            "'Maria is 34 years old and lives in Berlin.' Reply with only the JSON object."
        ),
        verify=v_json({"name": "Maria", "age": 34}),
    ),
    Prompt(
        name="format_primes",
        category="structured",
        messages=_user(
            "List the first five prime numbers in ascending order as a comma-separated list. "
            "Reply with only the list and nothing else."
        ),
        # Strict format: the stripped answer must be exactly "2, 3, 5, 7, 11" (spacing flexible,
        # optional trailing period). Leading prose fails -- that is the instruction-following test.
        verify=v_regex(r"^\s*2\s*,\s*3\s*,\s*5\s*,\s*7\s*,\s*11\s*\.?\s*$"),
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


def _gen_tok_per_s(attempts: Iterable[Attempt]) -> float:
    """tok/s over attempts that produced >=50 tokens (warmup-free); 0.0 if none qualify."""
    long_attempts = [a for a in attempts if a.tokens >= 50 and a.time_s > 0]
    secs = sum(a.time_s for a in long_attempts)
    return sum(a.tokens for a in long_attempts) / secs if secs > 0 else 0.0


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
        return _gen_tok_per_s(self.attempts)


@dataclass
class ModelResult:
    model_name: str
    hf_id: str
    prompts: list[PromptResult] = field(default_factory=list[PromptResult])

    @property
    def passes(self) -> int:
        """Total passing attempts across all prompts (out of attempts_total, e.g. 31 / 36)."""
        return sum(p.passes for p in self.prompts)

    @property
    def attempts_total(self) -> int:
        return sum(p.n for p in self.prompts)

    @property
    def total_time_s(self) -> float:
        return sum(p.total_time_s for p in self.prompts)

    @property
    def gen_tok_per_s(self) -> float:
        return _gen_tok_per_s(a for p in self.prompts for a in p.attempts)


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------


def _resolve_local_path(hf_spec: str, *, revision: str | None = None) -> Path | None:
    """Resolve the cached local model file for an HF spec 'repo:filename'.

    Returns the model path, or None if not cached. The llama-server '-hf' resolver
    has hung on cached repositories, so we always start with '-m' pointing at the
    resolved local file.
    """
    hf_repo, _, filename = hf_spec.partition(":")
    if not filename:
        return None
    cache_name = f"models--{hf_repo.replace('/', '--')}"
    snapshots = HF_HUB_DIR / cache_name / "snapshots"
    if revision is not None:
        model_path = snapshots / revision / filename
        return model_path if model_path.exists() else None
    if not snapshots.exists():
        return None

    # Prefer the repository's current main revision instead of filesystem iteration
    # order when multiple cached snapshots contain the same filename.
    main_ref = HF_HUB_DIR / cache_name / "refs" / "main"
    if main_ref.is_file():
        main_revision = main_ref.read_text().strip()
        model_path = snapshots / main_revision / filename
        if model_path.exists():
            return model_path

    # Fall back for old or partial caches that do not have refs/main.
    for snap in snapshots.iterdir():
        model_path = snap / filename
        if model_path.exists():
            return model_path
    return None


def _resolve_model_path(model: ModelConfig) -> Path | None:
    """Resolve a model file, honoring its optional immutable repository revision."""
    if model.revision is None:
        return _resolve_local_path(model.hf)
    return _resolve_local_path(model.hf, revision=model.revision)


def _is_model_downloaded(model: ModelConfig) -> bool:
    """Check if the model is already cached locally."""
    return _resolve_model_path(model) is not None


def _missing_model_assets(
    models: Iterable[ModelConfig],
    *,
    require_weights: bool = True,
) -> list[str]:
    """Return unique missing GGUFs and required companion draft heads.

    Routine runs may skip configs whose main weights were never downloaded, but a
    downloaded config must never silently run without its configured companion head.
    Full sweeps set ``require_weights`` so every selected config is preflighted.
    """
    missing: list[str] = []
    checked: set[tuple[str, str | None]] = set()
    for model in models:
        asset = (model.hf, model.revision)
        if asset in checked:
            continue
        checked.add(asset)
        model_path = _resolve_model_path(model)
        if model_path is None:
            if require_weights:
                missing.append(model.hf)
            continue
        if "unsloth/gemma-4-" in model.hf and not any(model_path.parent.glob("mtp-*.gguf")):
            repo = model.hf.partition(":")[0]
            missing.append(f"{repo}:mtp-*.gguf")
        if "Muse-Glimmer" in model.hf and not (model_path.parent / "dflash-kquant.gguf").is_file():
            repo = model.hf.partition(":")[0]
            missing.append(f"{repo}:dflash-kquant.gguf")
    return missing


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


# Best-practice defaults for Apple Silicon Metal.
# -ngl 99: full GPU offload (no-op safety on Apple). -fa on: flash attention (Metal-supported).
# -ub 1024: larger ubatch speeds up prompt processing for long prompts.
# KV cache is left at the f16 default. Every model in the broad 2026-07 sweep fit with
# f16 KV, and f16 is measurably faster than the old q8_0 KV: llama-bench on
# Qwen3.6-27B Q4_K_M (M5, build 9380) gave tg128 6.32 t/s
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
    model_path = _resolve_model_path(model)
    if model_path is None:
        msg = f"Model file not cached: {model.hf}"
        raise FileNotFoundError(msg)
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
    # Gemma 4 ships its MTP head as a SEPARATE `mtp-*.gguf` draft file in the snapshot;
    # auto-attach it as a draft model for lossless ~1.4-2.2x speculative decoding.
    if "--spec-type" not in model.server_args:
        draft = next(iter(model_path.parent.glob("mtp-*.gguf")), None)
        if draft is not None:
            cmd += ["--model-draft", str(draft), "--spec-type", "draft-mtp", "--spec-draft-n-max", "2", "-np", "1"]
        dflash = model_path.parent / "dflash-kquant.gguf"
        if "Muse-Glimmer" in model.hf and dflash.is_file():
            cmd += [
                "--spec-draft-model",
                str(dflash),
                "--spec-draft-ngl",
                "all",
                "--spec-type",
                "draft-dflash",
                "--spec-draft-n-max",
                "15",
                "-np",
                "1",
            ]
    log.info("Starting server: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        _wait_for_server(port)
    except BaseException:
        # _start_server has not returned the process to its caller yet, so it owns
        # cleanup for every startup failure, including Ctrl-C during model loading.
        _stop_server(proc)
        raise
    return proc


def _stop_server(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        log.info("Server already stopped")
        return
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


def _chat(messages: list[dict[str, object]], model_cfg: ModelConfig, port: int, *, thinking: bool) -> tuple[str, int]:
    """Send a chat completion request. Returns (response_text, token_count).

    `thinking` is the effective per-request decision (see `_thinks` for the per-category
    gate), not necessarily `model_cfg.thinking`.
    """
    api_url = API_URL.format(port=port)
    # Thinking mode needs more headroom than direct answers. 16k covers these short
    # benchmark prompts without truncation.
    max_tokens = 16384 if thinking else 4096
    template_kwargs: dict[str, object] = {"enable_thinking": thinking}
    if model_cfg.reasoning_strength is not None:
        template_kwargs["reasoning_strength"] = model_cfg.reasoning_strength if thinking else "low"
    sampling = (
        model_cfg.direct_sampling
        if not thinking and model_cfg.direct_sampling is not None
        else SamplingPreset(
            temperature=model_cfg.temperature,
            top_p=model_cfg.top_p,
            top_k=model_cfg.top_k,
            presence_penalty=model_cfg.presence_penalty,
            repetition_penalty=model_cfg.repetition_penalty,
        )
    )
    req_body: dict[str, object] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": sampling.temperature,
        "top_p": sampling.top_p,
        "top_k": sampling.top_k,
        # Explicitly pin min_p=0 so a server default cannot clip the sampling tail.
        "min_p": 0,
        "presence_penalty": sampling.presence_penalty,
        # llama.cpp's native name for repetition_penalty (1.0 = off).
        "repeat_penalty": sampling.repetition_penalty,
        # Send enable_thinking explicitly both ways. Templates with a toggle honor it;
        # models without one ignore the unknown kwarg.
        "chat_template_kwargs": template_kwargs,
    }
    if thinking and model_cfg.reasoning_effort is not None:
        req_body["reasoning_effort"] = model_cfg.reasoning_effort
    payload = json.dumps(req_body, ensure_ascii=False).encode()

    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        body = json.loads(resp.read().decode())

    text: str = body["choices"][0]["message"]["content"]
    tokens: int = body["usage"]["completion_tokens"]
    return text, tokens


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


# Thinking only helps on multi-step work; on short-answer categories it loops and burns
# the request timeout for no accuracy gain. A -think config thinks ONLY on these
# categories; everything else runs direct. The `structured` category is deliberately
# excluded -- thinking on JSON/strict-format tasks wastes tokens and can break the format.
THINKING_CATEGORIES: frozenset[str] = frozenset({"math", "reasoning", "coding"})


def _thinks(model_cfg: ModelConfig, prompt: Prompt) -> bool:
    """Effective thinking for this (model, prompt): the config must enable it AND the
    prompt's category must be one where thinking pays off."""
    return model_cfg.thinking and prompt.category in THINKING_CATEGORIES


def _run_one_attempt(prompt: Prompt, model_cfg: ModelConfig, port: int) -> Attempt:
    start = time.monotonic()
    try:
        text, tokens = _chat(prompt.messages, model_cfg, port, thinking=_thinks(model_cfg, prompt))
    except Exception as e:
        elapsed = time.monotonic() - start
        log.warning("    api error on %s/%s: %s", model_cfg.name, prompt.name, e)
        return Attempt(
            tokens=0,
            time_s=round(elapsed, 2),
            response="",
            ok=False,
            fail_reason=f"api error: {type(e).__name__}",
        )
    elapsed = time.monotonic() - start
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


def run_benchmark(
    models: list[ModelConfig] | None = None,
    port: int = DEFAULT_PORT,
    n: int = DEFAULT_N_RUNS,
    *,
    save_aggregate_progress: bool = True,
) -> list[ModelResult]:
    """Run all prompts against the selected models. Each prompt is sampled `n` times."""
    if models is None:
        models = MODELS
    results: list[ModelResult] = []

    for model in models:
        if not _is_model_downloaded(model):
            log.warning("Skipping %s -- not downloaded. See README for download instructions.", model.name)
            continue
        log.info("=== Model: %s ===", model.name)
        try:
            proc = _start_server(model, port)
        except (TimeoutError, OSError) as e:
            # A model whose server never comes up (unsupported arch, OOM, bad file) must not
            # crash the whole unattended run -- skip it and move on.
            log.warning("Skipping %s -- server failed to start: %s", model.name, e)
            continue
        try:
            mr = ModelResult(model_name=model.name, hf_id=model.hf)
            for prompt in PROMPTS:
                pr = _run_prompt(prompt, model, port, n)
                mr.prompts.append(pr)
            results.append(mr)
            # Routine runs publish aggregate progress immediately. A full sweep disables
            # this so a failed overnight run cannot replace the canonical complete data.
            if save_aggregate_progress:
                _save_json(results)
                _save_markdown(results)
            per_model_path = RESULTS_DIR / f"benchmark.{model.name}.json"
            per_model_data: BenchmarkData = {
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "models": [_model_to_dict(mr)],
            }
            per_model_path.write_text(json.dumps(per_model_data, indent=2, ensure_ascii=False) + "\n")
            log.info("Saved per-model results: %s", per_model_path)
        finally:
            _stop_server(proc)

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


# On-disk schema for benchmark.json / benchmark.<model>.json. Shared with make_comparison.py
# so the producer (_model_to_dict) and the consumer are type-checked against one definition --
# renaming a key here surfaces as a pyright error on the reader, not a silent KeyError at runtime.
class AttemptDict(TypedDict):
    tokens: int
    time_s: float
    ok: bool
    fail_reason: str
    response: str


class PromptDict(TypedDict):
    name: str
    category: str
    passes: int
    n: int
    pass_rate: float
    total_tokens: int
    total_time_s: float
    attempts: list[AttemptDict]


class ModelDict(TypedDict):
    model: str
    hf_id: str
    passes: int
    attempts_total: int
    total_time_s: float
    gen_tok_per_s: float
    prompts: list[PromptDict]


class BenchmarkData(TypedDict):
    timestamp: str
    models: list[ModelDict]


def _model_to_dict(r: ModelResult) -> ModelDict:
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
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "benchmark.json"
    data: BenchmarkData = {
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


def count_fail_kinds(fail_reasons: Iterable[str]) -> tuple[int, int, int]:
    """Count failed-attempt reasons as a (wrong, timeout, empty) tuple via fail_kind."""
    kinds = [fail_kind(r) for r in fail_reasons]
    return kinds.count("wrong"), kinds.count("timeout"), kinds.count("empty")


def _save_markdown(results: list[ModelResult]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
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
        w, t, e = count_fail_kinds(a.fail_reason for p in r.prompts for a in p.attempts if not a.ok)
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
        help="Run any matching supported text configs (substring match)",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--include-challengers",
        action="store_true",
        help="Append the current text challengers to the curated routine set",
    )
    scope.add_argument(
        "--full-sweep",
        action="store_true",
        help="Run all current text configurations, including North Mini Code",
    )
    parser.add_argument(
        "-n",
        "--n-runs",
        type=int,
        default=DEFAULT_N_RUNS,
        help=f"Sample each prompt this many times (default: {DEFAULT_N_RUNS})",
    )
    return parser.parse_args()


def _select_models(
    model_filter: str | None,
    *,
    include_challengers: bool,
    full_sweep: bool = False,
) -> list[ModelConfig]:
    """Select the routine, current, full, or explicitly filtered text set."""
    if model_filter:
        return [model for model in FULL_SWEEP_MODELS if model_filter in model.name]
    if full_sweep:
        return list(FULL_SWEEP_MODELS)
    if include_challengers:
        return list(CURRENT_TEXT_MODELS)
    return list(MODELS)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    args = _parse_args()
    models = _select_models(
        args.model,
        include_challengers=args.include_challengers,
        full_sweep=args.full_sweep,
    )
    if not models:
        log.error("No model matching '%s' found", args.model)
        return
    missing = _missing_model_assets(models, require_weights=args.full_sweep)
    if missing:
        scope = "Full sweep" if args.full_sweep else "Selected models"
        log.error("%s not ready; missing %d required model assets", scope, len(missing))
        for asset in missing:
            log.error("Missing: %s", asset)
        raise SystemExit(2)

    results = run_benchmark(
        models,
        port=args.port,
        n=args.n_runs,
        save_aggregate_progress=not args.full_sweep,
    )
    if not results:
        log.error("No models completed; canonical results unchanged")
        raise SystemExit(3)
    if args.full_sweep and len(results) != len(models):
        log.error(
            "Full sweep incomplete: finished %d of %d configs; canonical results unchanged",
            len(results),
            len(models),
        )
        raise SystemExit(3)
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
