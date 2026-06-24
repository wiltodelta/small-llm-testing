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
REQUEST_TIMEOUT = 120  # cap per request -- think-mode can run long / loop; fail fast instead of hanging
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
    # Vendor anti-repetition knobs (defaults are no-ops). presence_penalty: OpenAI-style,
    # Qwen recommends up to 2.0 to stop endless thinking-mode generation. repetition_penalty
    # maps to llama.cpp `repeat_penalty` (1.0 = off); LFM2.5 recommends 1.05.
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.0
    server_args: tuple[str, ...] = ()
    # Qwen3 / Gemma 4 / GLM ship thinking mode; `thinking` gates whether this config thinks
    # on the THINKING_CATEGORIES. Enforced per request via chat_template_kwargs.
    thinking: bool = True


# MTP speculative-decoding flags (build 9380). The MTP head is embedded in the -MTP
# GGUF; MTP runs single-stream (-np 1).
_MTP_ARGS: tuple[str, ...] = ("-np", "1", "--spec-type", "draft-mtp", "--spec-draft-n-max", "2")


def _qwen_matrix(
    label: str,
    mtp_repo: str,
    gguf: str,
    extra_args: tuple[str, ...] = (),
    think_presence_penalty: float = 1.5,
) -> list[ModelConfig]:
    """think + nothink configs for one Qwen, both with MTP speculative decoding.

    Sampling per Qwen team: thinking on -> temp=0.6/top_p=0.95; off -> 0.7/0.8 (top_k=20).
    presence_penalty per the Qwen cards: 1.5 for non-thinking, and for thinking 1.5 on the
    small models (3.5 2B/4B/9B) but 0.0 on the 27B (pass `think_presence_penalty=0.0`).
    It is the vendor's documented fix for endless thinking-mode generation -- exactly the
    looping that drives our think-mode timeouts.
    All Qwen runs use the -MTP GGUF: in the A/B, MTP strictly dominated plain decode --
    1.2-1.65x faster with the same accuracy, and the extra speed rescues think-mode coding
    from the 120s timeout. `extra_args` (e.g. ("-c", "8192") for the 27B) applies to both.
    """

    def make(thinking: bool) -> ModelConfig:
        suffix = "think" if thinking else "nothink"
        temp, top_p = (0.6, 0.95) if thinking else (0.7, 0.8)
        return ModelConfig(
            name=f"{label}-mtp-{suffix}",
            hf=f"{mtp_repo}:{gguf}",
            temperature=temp,
            top_p=top_p,
            top_k=20,
            presence_penalty=think_presence_penalty if thinking else 1.5,
            thinking=thinking,
            server_args=extra_args + _MTP_ARGS,
        )

    return [make(thinking) for thinking in (True, False)]


def _gemma_pair(label: str, hf: str, extra_args: tuple[str, ...] = ()) -> list[ModelConfig]:
    """think + nothink configs for one Gemma 4 model (Gemma sampling defaults).

    Gemma 4 (unlike Gemma 3) has an enable_thinking toggle. We run both modes: measured
    per-category, thinking is worth +3..+9 (math_modular/multistep, reasoning) on every size
    except 26b-a4b (ceiling either way), at 10-25x wall time but no timeouts. Keeping both
    makes that tradeoff explicit, the same way the Qwen think/nothink pairs do.
    """
    return [
        ModelConfig(name=f"{label}-think", hf=hf, thinking=True, server_args=extra_args),
        ModelConfig(name=f"{label}-nothink", hf=hf, thinking=False, server_args=extra_args),
    ]


MODELS: list[ModelConfig] = [
    # Gemma 4 (Google) -- no MTP head; each runs a think + nothink pair (see _gemma_pair).
    # temp=1.0, top_p=0.95, top_k=64 (Gemma cards, all use cases). e2b/e4b are Q8_0/Q4_K_M;
    # 12b/31b are official QAT q4_0; 26b-a4b is a 26B/4B-active MoE. The 31B uses -c 8192 to
    # keep f16 KV within the working set; the rest fit at default ctx.
    *_gemma_pair("gemma-4-e2b-Q8_0", "ggml-org/gemma-4-E2B-it-GGUF:gemma-4-E2B-it-Q8_0.gguf"),
    *_gemma_pair("gemma-4-e4b-Q4_K_M", "ggml-org/gemma-4-E4B-it-GGUF:gemma-4-E4B-it-Q4_K_M.gguf"),
    *_gemma_pair("gemma-4-12b-qat-q4_0", "google/gemma-4-12B-it-qat-q4_0-gguf:gemma-4-12b-it-qat-q4_0.gguf"),
    *_gemma_pair("gemma-4-26b-a4b-Q4_K_M", "ggml-org/gemma-4-26B-A4B-it-GGUF:gemma-4-26B-A4B-it-Q4_K_M.gguf"),
    *_gemma_pair(
        "gemma-4-31b-qat-q4_0",
        "google/gemma-4-31B-it-qat-q4_0-gguf:gemma-4-31B_q4_0-it.gguf",
        extra_args=("-c", "8192"),
    ),
    # Qwen: {think, nothink}, both MTP (non-MTP dropped -- MTP strictly dominated the A/B).
    # Qwen3.5 small (Q8_0) fits at default ctx; Qwen 3.6 27B (Q4_K_M ~16.8 GB) uses -c 8192.
    # 0.8B dropped: too small to think productively (loops/timeouts, net loss).
    *_qwen_matrix("qwen3.5-2b-Q8_0", "unsloth/Qwen3.5-2B-MTP-GGUF", "Qwen3.5-2B-Q8_0.gguf"),
    *_qwen_matrix("qwen3.5-4b-Q8_0", "unsloth/Qwen3.5-4B-MTP-GGUF", "Qwen3.5-4B-Q8_0.gguf"),
    *_qwen_matrix("qwen3.5-9b-Q8_0", "unsloth/Qwen3.5-9B-MTP-GGUF", "Qwen3.5-9B-Q8_0.gguf"),
    *_qwen_matrix(
        "qwen3.6-27b-Q4_K_M",
        "unsloth/Qwen3.6-27B-MTP-GGUF",
        "Qwen3.6-27B-Q4_K_M.gguf",
        extra_args=("-c", "8192"),
        think_presence_penalty=0.0,  # 27B card: presence_penalty 0.0 for thinking (vs 1.5 on the small 3.5)
    ),
    # Other families -- single instruct config each, no MTP head. Sampling from each model
    # card; values verified against the official cards (see per-model notes).
    # Mistral Ministral 3 (Apache-2.0). Card: temp BELOW 0.1 for production (we use 0.07);
    # top_p/top_k/penalties unspecified, left neutral. Instruct (not the Reasoning SKU).
    ModelConfig(
        name="ministral-3-8b-Q8_0",
        hf="mistralai/Ministral-3-8B-Instruct-2512-GGUF:Ministral-3-8B-Instruct-2512-Q8_0.gguf",
        temperature=0.07,
        top_p=1.0,
        top_k=0,
    ),
    ModelConfig(
        name="ministral-3-14b-Q4_K_M",
        hf="mistralai/Ministral-3-14B-Instruct-2512-GGUF:Ministral-3-14B-Instruct-2512-Q4_K_M.gguf",
        temperature=0.07,
        top_p=1.0,
        top_k=0,
    ),
    # Microsoft Phi-4-mini-instruct (MIT, text-only, standard instruct -- not reasoning).
    # Card publishes no sampling preset; its only shown setting is greedy (temperature=0.0,
    # do_sample=False), which is also the most reproducible for a benchmark. At temp 0 the
    # n=3 samples are identical -- acceptable (deterministic pass/fail).
    ModelConfig(
        name="phi-4-mini-Q8_0",
        hf="unsloth/Phi-4-mini-instruct-GGUF:Phi-4-mini-instruct.Q8_0.gguf",
        temperature=0.0,
        top_p=1.0,
        top_k=0,
    ),
    # Zhipu GLM-4.7-Flash (MIT, text-only) -- 30B-A3B MoE (3B active, so fast despite size).
    # Q4_K_M ~18.3 GB; -c 8192 keeps f16 KV in the working set. Card: temp=1.0, top_p=0.95
    # (no top_k published -> top_k=0). Thinking is hybrid and defaults to ENABLED; its toggle
    # is z.ai's `thinking:{type}` object, NOT enable_thinking, so our kwarg is a no-op for GLM
    # -- it runs thinking on (the documented default) across all categories.
    ModelConfig(
        name="glm-4.7-flash-Q4_K_M",
        hf="unsloth/GLM-4.7-Flash-GGUF:GLM-4.7-Flash-Q4_K_M.gguf",
        temperature=1.0,
        top_p=0.95,
        top_k=0,
        server_args=("-c", "8192"),
    ),
    # Liquid AI LFM2.5-8B-A1B (lfm1.0 license, text-only) -- edge MoE, 8B total / 1.5B
    # active, so decode is fast despite size. Q8_0 ~9.0 GB. Card: temp=0.2, top_k=80,
    # repetition_penalty=1.05 (their documented anti-repetition knob; top_p left neutral).
    ModelConfig(
        name="lfm2.5-8b-a1b-Q8_0",
        hf="LiquidAI/LFM2.5-8B-A1B-GGUF:LFM2.5-8B-A1B-Q8_0.gguf",
        temperature=0.2,
        top_p=1.0,
        top_k=80,
        repetition_penalty=1.05,
    ),
    # JetBrains Mellum2-12B-A2.5B-Thinking (Apache-2.0, text/coding) -- coding MoE, 12B
    # total / 2.5B active, emits native <think> blocks (stripped before verify). Q4_K_M
    # ~8.1 GB. Card: temp=0.6, top_p=0.95, top_k=20 (exact match). Always thinks; the
    # enable_thinking kwarg we send is ignored (no toggle), thinking stays on.
    ModelConfig(
        name="mellum2-12b-a2.5b-think-Q4_K_M",
        hf="JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M:Mellum2-12B-A2.5B-Thinking-Q4_K_M.gguf",
        temperature=0.6,
        top_p=0.95,
        top_k=20,
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
# The structured dimension probes instruction-following / function-calling, the strength
# of agentic models (Ministral / GLM / Qwen3.6) that the reasoning core alone misses.
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


def _resolve_local_path(hf_spec: str) -> Path | None:
    """Resolve the cached local model file for an HF spec 'repo:filename'.

    Returns the model path, or None if not cached. The llama-server '-hf' resolver
    hangs on some Qwen repos even when files are cached, so we always start with '-m'
    pointing at the local file.
    """
    hf_repo, _, filename = hf_spec.partition(":")
    if not filename:
        return None
    cache_name = f"models--{hf_repo.replace('/', '--')}"
    snapshots = HF_HUB_DIR / cache_name / "snapshots"
    if not snapshots.exists():
        return None
    # Multiple snapshot dirs may exist from interrupted downloads; return the first
    # that actually contains the requested file.
    for snap in snapshots.iterdir():
        model_path = snap / filename
        if model_path.exists():
            return model_path
    return None


def _is_model_downloaded(model: ModelConfig) -> bool:
    """Check if the model is already cached locally."""
    return _resolve_local_path(model.hf) is not None


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
# -ub 1024: larger ubatch speeds up prompt processing for long prompts.
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
    model_path = _resolve_local_path(model.hf)
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
    # general tasks, 80k+ for math/code. 4k overflows even small models inside <think>.
    max_tokens = 16384 if thinking else 4096
    req_body: dict[str, object] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": model_cfg.temperature,
        "top_p": model_cfg.top_p,
        "top_k": model_cfg.top_k,
        # Qwen team recommendation: explicitly pin min_p=0 (server default may clip the tail).
        "min_p": 0,
        "presence_penalty": model_cfg.presence_penalty,
        # llama.cpp's native name for repetition_penalty (1.0 = off).
        "repeat_penalty": model_cfg.repetition_penalty,
        # Send enable_thinking explicitly both ways: models with a thinking toggle
        # (Qwen3, Gemma 4) honor it; models without one (Ministral, Phi, LFM, Mellum)
        # ignore the unknown kwarg. Leaving it unset would run them at template default.
        "chat_template_kwargs": {"enable_thinking": thinking},
    }
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
    try:
        text, tokens, elapsed = _chat(prompt.messages, model_cfg, port, thinking=_thinks(model_cfg, prompt))
    except Exception as e:
        log.warning("    api error on %s/%s: %s", model_cfg.name, prompt.name, e)
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


def run_benchmark(
    models: list[ModelConfig] | None = None,
    port: int = DEFAULT_PORT,
    n: int = DEFAULT_N_RUNS,
) -> list[ModelResult]:
    """Run all prompts against all models. Each prompt is sampled `n` times."""
    if models is None:
        models = MODELS
    results: list[ModelResult] = []

    for model in models:
        if not _is_model_downloaded(model):
            log.warning("Skipping %s -- not downloaded. See README for download instructions.", model.name)
            continue
        log.info("=== Model: %s ===", model.name)
        proc = _start_server(model, port)
        try:
            mr = ModelResult(model_name=model.name, hf_id=model.hf)
            for prompt in PROMPTS:
                pr = _run_prompt(prompt, model, port, n)
                mr.prompts.append(pr)
            results.append(mr)
            # Persist after each model so a crash/sleep does not lose prior results.
            RESULTS_DIR.mkdir(exist_ok=True)
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
