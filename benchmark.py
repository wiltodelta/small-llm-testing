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

# Recheck after a broken 2026-08-18 run: Qwen thinking never produced a token
# (HTTPError, body not recorded), and Nemotron's fails were 300s request timeouts
# on thinking, not wrong answers. Sampling matches the official cards. Use
# --full-sweep to add North Mini Code, or --model to select one config directly.
CHALLENGERS: list[ModelConfig] = [
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
    # Optional per-prompt generation cap, lower than the mode default (16384 think /
    # 4096 direct). Long-context prompts set it so a ~3k-token article plus the answer
    # fits the smallest server context in the fleet (North Mini Code at -c 8192).
    max_completion_tokens: int | None = None


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
    strings compare case-insensitively after stripping; lists of strings compare
    as case-insensitive, order-insensitive sets of the same length (a members list
    reported in a different order is not a wrong answer). Tests structured-output /
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
            elif isinstance(want, list):
                if not isinstance(got, list):
                    return False, f"{key}={got!r}, want {want!r}"
                want_list = cast("list[object]", want)
                got_list = cast("list[object]", got)
                if len(got_list) != len(want_list):
                    return False, f"{key}={got!r}, want {want!r}"
                norm_got = sorted(str(item).strip().lower() for item in got_list)
                norm_want = sorted(str(item).strip().lower() for item in want_list)
                if norm_got != norm_want:
                    return False, f"{key}={got!r}, want {want!r}"
            elif got != want:
                return False, f"{key}={got!r}, want {want!r}"
        return True, ""

    return check


def _user(text: str) -> list[dict[str, object]]:
    return [{"role": "user", "content": text}]


# ---------------------------------------------------------------------------
# Long-context scenario material
# ---------------------------------------------------------------------------

# One fictional encyclopedia article, ~2.5-3k tokens, hand-written so every fact
# cross-checks (dates, counts, and honours are internally consistent). The two
# variants are byte-identical except for the Legacy birth year: 1887 matches the
# lead and Early life sections; 1891 is the single planted contradiction. Fictional
# entities keep world knowledge out of the answer: only the given text can decide.
# Length is bounded (tests pin 9000-14000 chars) so article + capped answer fits the
# smallest server context in the fleet (North Mini Code at -c 8192).
# Wrapped to keep lint happy; _reflow rejoins the lines so the prompt text is
# single-line prose paragraphs regardless of source formatting.
_FERREL_TEMPLATE_RAW = """Augustin Ferrel

Augustin Ferrel (3 March 1887 - 21 June 1961) was a Veranian composer, conductor, and music teacher.
He wrote five operas, four symphonies, seven string quartets, and more than sixty songs, and taught
composition at the Halmer Conservatory from 1920 to 1952. His music joins late romantic melody to an
austere northern harmonic idiom that critics of the 1930s labelled "coastal modernism", a tag Ferrel
pretended to dislike.

== Early life ==

Augustin Ferrel was born on 3 March 1887 in Kolvik, a fishing port on Verania's northern coast, the
third of four children of Edvard Ferrel, the town's Lutheran organist, and his wife Linnea, nee
Hallas, who taught piano to the children of skippers and cannery clerks. The family flat stood above
the music shop run by his paternal uncle, and Ferrel liked to say that the shop's crates of
scratched second-hand records had been his first library.

He began piano lessons with his mother at six and was composing small piano pieces by eleven,
several of which were played at the Kolvik parish hall. In 1898 the family moved to Halmer, the
capital, after his father took the organist's post at the Ostmars Church. At the Halmer Gymnasium a
mathematics teacher, Gunnar Sede, fed the boy's growing obsession with counterpoint, telling him
that a fugue was simply a proof set in sound.

Ferrel dismissed almost all of his juvenilia in later life. The one exception was a wedding song for
his sister, "The Tide Clock", written in 1903, which he kept in his concert programmes to the end.

== Education ==

Ferrel entered the Halmer Conservatory in 1905, studying piano with Klara Menn and composition with
Ernst Valling, whose punishing exercises in modal counterpoint Ferrel credited, decades later, as
the spine of his technique. He paid his way by playing rehearsals at a suburban theatre and, from
1907, as the regular accompanist of the Halmer Choral Society.

He graduated in 1909 with the composition diploma. His graduation piece, "Night on the Outer Pier",
was conducted by Valling at the conservatory's summer concert and was published the following year
as his official opus 1. A small scholarship paid for a summer in Brenau in 1910, where the repertory
of the northern opera houses made a deeper impression on him than any of his formal lessons.
Valling's seminar on paleo-Veranian organum, which Ferrel sat in on without credit for two winters,
later surfaced whole in the modal writing of the Second Symphony.

== Career ==

Ferrel's professional career began in 1912 with the post of second kapellmeister at the Brenau
Stadttheater. Seven seasons in the pit gave his music an unsentimental, practical command of voices
and orchestra. He conducted operetta through the war years on shrinking budgets, and the theatre's
director, Otto Kelb, staged Ferrel's one-act comedy "The Lighthouse Ledger" in 1917 as a fill-in for
a cancelled visiting production.

In 1920 Ferrel returned to Halmer as professor of composition at the conservatory. Teaching claimed
the afternoons, so the sequence of major works that followed was composed, almost without exception,
before lunch, a habit he recommended to every student he ever had. He served as rector for the
academic year 1936-1937, steering the conservatory through a ministry review of modernist syllabuses
with what his biographer called "the most Ferrel of all his performances".

Guest engagements kept him on the road through the late 1920s and 1930s. He preferred conducting his
own music to administering it, and turned down the music-directorship of the Brenau Stadttheater in
1929, telling the intendant that he had already given the pit its orders for seven years. A 1931
broadcast concert with the Brenau Philharmonic, pairing the Second Symphony with the Net Menders
intermezzo, was issued on shellac and is the earliest recorded document of his conducting.

Ferrel retired from teaching in 1952 and kept composing until 1958, when his sight began to fail.
His last years went into preparing a complete critical edition of his songs. He died at home in
Halmer on 21 June 1961.

== Operas ==

Ferrel completed five operas.

The Salt Garden, a fishing-village tragedy in three acts to a libretto by Ade Ronn, was first
performed at the Brenau Stadttheater on 14 October 1928. Its story of a family that hides a
shipwreck survivor's identity for a generation made it the most performed Veranian opera of its
decade, and the intermezzo, "The Net Menders", took on an independent life in concert programmes.

The Winter Lock (first performed 1933) compresses a canal accident into a single winter night.
Ferrel and Ronn cut the libretto to under ninety minutes of music at the composer's insistence, and
the score's stark choral writing for the lock-keepers' wives is often singled out as the purest
example of his coastal idiom.

North of Halmen (1940) is a radio opera commissioned by the Veranian Broadcasting Service. Written
for microphones rather than a stage, its broadcast reached the largest audience any Ferrel work
would have in his lifetime, and the composer, who listened at home, described the experience as
"hearing my own house on the sea".

The Cartographer's Daughter (1949) returned to the theatre as a full-evening lyric drama. Its long
opening scene for soprano and chorus, set in a survey office during a storm, closes on a tonic pedal
more than twenty minutes in, a passage conductors either revere or quietly cut.

The Lantern Procession (1955), the warmest and least typical of the five, is a comedy of village
misunderstandings written after the deaths of both Ronn and Menn. Critics heard a farewell in its
final procession; Ferrel, typically, denied any such intention.

== Symphonies ==

Ferrel's four symphonies anchor the orchestral catalogue. The First (1915) is still broadly romantic
and remains the least played. The Second, "Northern" (1921), a half-hour passacaglia-finale work,
fixed his public reputation at home. The Third (1934) was his most controversial premiere, whistled
in Halmer and applauded in Brenau in the same month. The Fourth (1948), his most performed concert
work, ends with a set of variations on a Kolvik herring-counting song that he had first noted down
as a teenager. He also left a handful of tone poems, of which "The Ice Pilot" (1926) is the most
played.

== Chamber and piano music ==

The seven string quartets trace Ferrel's whole career with unusual candour. No. 1 (1911) and No. 2
(1916) still lean on Brahms. No. 3 (1922) introduces the bare parallel fifths that became his
fingerprint. No. 4 (1927) packs a four-movement scheme into eleven minutes. No. 5 (1935) is a single
long arch. No. 6 (1943), written for amateurs during the wartime coal shortages, is meant to work in
a cold hall with tired fingers. No. 7 (1950) reconciles the arch of the Fifth with the brevity of
the Fourth and is generally ranked with the finest quartets of its decade.

The two piano sonatas (1913 and 1925) are recital staples in Verania, and the "Harbour Notebook"
(1938), short pieces each named for a boat in the Kolvik fleet, is the set teachers reach for. The
Violin Sonata (1919) and the Cello Sonata (1932) complete the main chamber list.

== Songs ==

Ferrel published more than sixty songs. Four cycles anchor them: "Sailor's Almanac" (1917), "White
Fields" (1929), "The Long Shore" (1944), and the final "Late Windows" (1958), his last completed
work. He insisted the songs be sung in Veranian, and refused commissions for translations in his
lifetime. Heard chiefly at home for most of his career, the songs began travelling after the late-
century recordings drew ensembles back to the rest of his catalogue.

== Personal life ==

In 1916 Ferrel married the violinist Dagny Holm, whom he had first accompanied at a conservatory
exam. Their daughter Liv, later a painter, was born in 1918, and their son Jonas, later the
conservatory's librarian, in 1921. The marriage was close and, by design, uneventful; colleagues
joked that the storms in Ferrel's music were all exported. The family spent every summer from 1923
onward in a house on the Kolvik shore road.

== Honours ==

Ferrel received the Kalmar Prize in 1938, the Grand Medal of the Halmer Music Society in 1946, and
honorary membership of the Veranian Composers' League in 1951. He twice declined the Order of the
Coast, informing the ministry that a composer's state honours were his pupils. In 1959 the
conservatory named its new rehearsal hall after him, an irony he is recorded as enjoying.

== Legacy ==

Ferrel, born in <LEGACY-BIRTH-YEAR> in the port town of Kolvik, belonged to a generation of Veranian
composers who stayed provincial on purpose, and his reputation has kept their whole milieu in view.
The Ferrel Chamber Prize was founded in 1969 for young ensembles from the northern provinces. The
Augustin Ferrel Museum opened in Kolvik in 1983 in the former music shop beneath his childhood flat.
A festival of his music has been held in Kolvik every second summer since 1974, and the shore-road
house is marked with a plaque quoting the Tide Clock song. Complete recordings of the quartets
followed in 1998, and a full opera cycle between 2004 and 2011, which revived his early operas in
particular on European stages. Ferrel's working maxim, quoted in every study of his music, was that
a composer's job is to write music that can be played twice by people who are cold."""


def _reflow(template: str) -> str:
    """Join hard-wrapped source lines inside each paragraph."""
    return "\n\n".join(" ".join(paragraph.split()) for paragraph in template.split("\n\n"))


_FERREL_TEMPLATE = _reflow(_FERREL_TEMPLATE_RAW)


def _ferrel_article(legacy_birth_year: int) -> str:
    """Instantiate the article template with the Legacy-section birth year."""
    return _FERREL_TEMPLATE.replace("<LEGACY-BIRTH-YEAR>", str(legacy_birth_year))


# Internally consistent reference (Legacy repeats the lead's 1887).
FERREL_ARTICLE = _ferrel_article(1887)
# Same article with exactly one planted contradiction (Legacy says 1891).
FERREL_ARTICLE_BAD = _ferrel_article(1891)

# Uniform suffix for consistency pairs: judge textually, answer first-token yes/no.
_CONSISTENCY_SUFFIX = (
    "\n\nDo these two statements contradict each other? Judge using only the "
    "information given in the two statements. Answer with one word: yes or no."
)

# Long-context consistency check, shared by both article variants.
_LONGCTX_CHECK_PREFIX = "You are checking an encyclopedia article for internal consistency.\n\n"
_LONGCTX_CHECK_SUFFIX = (
    "\n\nQuestion: Does this article contain an internal inconsistency, that is, two "
    "statements that cannot both be true? Answer with one word: yes or no."
)


# Tighter answers + verifiable correctness. Each prompt is sampled DEFAULT_N_RUNS times
# at temperature > 0; we report passes/N. A 'pass' must contain the right answer,
# not just plausibly mention it.

# 22 prompts across five dimensions: math (3), reasoning (4), coding (3, executed),
# structured (3), consistency (6), longcontext (3). The first four are the original
# discriminating text core; consistency and longcontext model the background
# data-auditing agent scenario (does a model notice that two wiki statements cannot
# both be true, over a statement pair or a full article). Trivial prompts that every
# model passed were dropped from the original 16 (see docs/benchmark-design.md).
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
    Prompt(
        name="json_fields",
        category="structured",
        messages=_user(
            "From the text below, extract a JSON object with exactly the keys "
            '"artist" (string), "formed" (integer), "members" (array of strings, one per '
            'member), and "award_winner" (boolean): '
            "'Night Harbor was formed in 1993 by singer Ro Aldis, guitarist Petal Vun, "
            "and drummer Sena Marn. The trio still performs, and it has never won a major "
            "award.' Reply with only the JSON object."
        ),
        # The never-won trap checks a false boolean and a list value in one object --
        # the report shape a background auditing agent emits per finding.
        verify=v_json(
            {
                "artist": "Night Harbor",
                "formed": 1993,
                "members": ["Ro Aldis", "Petal Vun", "Sena Marn"],
                "award_winner": False,
            }
        ),
    ),
    # ---- consistency (statement pairs, wiki-edit patterns, fictional entities) ----
    # Real wiki inconsistency patterns on invented entities, so world knowledge cannot
    # substitute for reading the two statements. Half contradict, half do not, so an
    # always-yes or always-no bias scores 50%.
    Prompt(
        name="cons_date_shift",
        category="consistency",
        messages=_user(
            "Statement A: Elsa Marquard (1902-1988) was a German lithographer and printmaker.\n"
            "Statement B: Marquand died in 1986, shortly before a major retrospective of "
            "her work opened." + _CONSISTENCY_SUFFIX
        ),
        # Infobox range end (1988) vs prose death year (1986) -- classic date drift.
        verify=v_yes_no(want_yes=True),
    ),
    Prompt(
        name="cons_digit_swap",
        category="consistency",
        messages=_user(
            "Statement A: Lake Vess covers an area of 62 square kilometers.\n"
            "Statement B: With an area of 26 square kilometers, Lake Vess is the largest "
            "lake in the region." + _CONSISTENCY_SUFFIX
        ),
        # 62 vs 26: transposed digits, the most common wiki numeric typo.
        verify=v_yes_no(want_yes=True),
    ),
    Prompt(
        name="cons_dead_action",
        category="consistency",
        messages=_user(
            "Statement A: The composer Anton Rebek retired in 1930 and died in 1932 in Torlan.\n"
            "Statement B: In 1935 Rebek completed and conducted the premiere of his seventh "
            "symphony." + _CONSISTENCY_SUFFIX
        ),
        # An action after the stated death year requires temporal reasoning, not string match.
        verify=v_yes_no(want_yes=True),
    ),
    Prompt(
        name="cons_unit_equivalent",
        category="consistency",
        messages=_user(
            "Statement A: The Sorvik radio tower is 450 meters tall.\n"
            "Statement B: The Sorvik radio tower reaches a height of 0.45 kilometers." + _CONSISTENCY_SUFFIX
        ),
        # Equal value in different units: no contradiction. Catches unit-blind matchers.
        verify=v_yes_no(want_yes=False),
    ),
    Prompt(
        name="cons_complementary",
        category="consistency",
        messages=_user(
            "Statement A: The novel The Glass Ferry was published in 1977.\n"
            "Statement B: The Glass Ferry won the Vendla Prize in 1979." + _CONSISTENCY_SUFFIX
        ),
        # Publication and a later prize are complementary facts, not a contradiction.
        verify=v_yes_no(want_yes=False),
    ),
    Prompt(
        name="cons_relative_rank",
        category="consistency",
        messages=_user(
            "Statement A: Mount Kerrek is the second-highest mountain in Tarvonia.\n"
            "Statement B: No mountain in Tarvonia is higher than Mount Sarva." + _CONSISTENCY_SUFFIX
        ),
        # Sarva highest + Kerrek second-highest is consistent; requires relational reasoning.
        verify=v_yes_no(want_yes=False),
    ),
    # ---- longcontext (article-length input, the background agent's working unit) ----
    Prompt(
        name="longctx_inconsistent",
        category="longcontext",
        messages=_user(_LONGCTX_CHECK_PREFIX + FERREL_ARTICLE_BAD + _LONGCTX_CHECK_SUFFIX),
        # The planted birth-year contradiction (lead/Early life 1887 vs Legacy 1891) sits
        # thousands of tokens apart; finding it is the wiki-audit task at article scale.
        verify=v_yes_no(want_yes=True),
        max_completion_tokens=4096,
    ),
    Prompt(
        name="longctx_consistent",
        category="longcontext",
        messages=_user(_LONGCTX_CHECK_PREFIX + FERREL_ARTICLE + _LONGCTX_CHECK_SUFFIX),
        # Same length and shape, no contradiction: measures the false-positive rate,
        # which for an unattended agent is as damaging as a miss.
        verify=v_yes_no(want_yes=False),
        max_completion_tokens=4096,
    ),
    Prompt(
        name="longctx_needle",
        category="longcontext",
        messages=_user(
            "Read the encyclopedia article below, then answer the question.\n\n"
            + FERREL_ARTICLE
            + "\n\nQuestion: In which year was the opera The Salt Garden first performed? "
            "Reply with only the number."
        ),
        # One dated fact buried mid-list among distractor years; stated exactly once.
        verify=v_number(1928),
        max_completion_tokens=4096,
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


def _chat(
    messages: list[dict[str, object]],
    model_cfg: ModelConfig,
    port: int,
    *,
    thinking: bool,
    max_tokens_cap: int | None = None,
) -> tuple[str, int]:
    """Send a chat completion request. Returns (response_text, token_count).

    `thinking` is the effective per-request decision (see `_thinks` for the per-category
    gate), not necessarily `model_cfg.thinking`. `max_tokens_cap` optionally lowers the
    mode default so a long prompt plus its answer fits the server context.
    """
    api_url = API_URL.format(port=port)
    # Thinking mode needs more headroom than direct answers. 16k covers the short
    # benchmark prompts without truncation. Long-context prompts cap below the mode
    # default so a ~3k-token article + answer fits the smallest fleet context (8192).
    max_tokens = 16384 if thinking else 4096
    if max_tokens_cap is not None:
        max_tokens = min(max_tokens, max_tokens_cap)
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
# categories; everything else runs direct. `consistency` and `longcontext` join the gate:
# contradiction-finding is reasoning, and a background agent is latency-insensitive.
# The `structured` category stays deliberately excluded -- thinking on JSON/strict-format
# tasks wastes tokens and can break the format.
THINKING_CATEGORIES: frozenset[str] = frozenset({"math", "reasoning", "coding", "consistency", "longcontext"})


def _thinks(model_cfg: ModelConfig, prompt: Prompt) -> bool:
    """Effective thinking for this (model, prompt): the config must enable it AND the
    prompt's category must be one where thinking pays off."""
    return model_cfg.thinking and prompt.category in THINKING_CATEGORIES


def _api_fail_reason(exc: BaseException) -> str:
    """Keep HTTP status and body so a 400 is not stored as a bare HTTPError."""
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", "replace").strip()
        except Exception:
            body = ""
        detail = body[:500] if body else str(exc.reason or "")
        return f"api error: HTTPError {exc.code} {detail}".rstrip()
    name = type(exc).__name__
    msg = str(exc).strip()
    if not msg or msg == name:
        return f"api error: {name}"
    return f"api error: {name}: {msg}"


def _run_one_attempt(prompt: Prompt, model_cfg: ModelConfig, port: int) -> Attempt:
    start = time.monotonic()
    try:
        text, tokens = _chat(
            prompt.messages,
            model_cfg,
            port,
            thinking=_thinks(model_cfg, prompt),
            max_tokens_cap=prompt.max_completion_tokens,
        )
    except Exception as e:
        elapsed = time.monotonic() - start
        reason = _api_fail_reason(e)
        log.warning("    api error on %s/%s: %s", model_cfg.name, prompt.name, reason)
        return Attempt(
            tokens=0,
            time_s=round(elapsed, 2),
            response="",
            ok=False,
            fail_reason=reason,
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
    prompts: list[Prompt] | None = None,
    save_aggregate_progress: bool = True,
    snapshot_tag: str | None = None,
) -> list[ModelResult]:
    """Run the prompt suite against the selected models, sampling each prompt `n` times.

    `prompts` defaults to the full suite; a filtered subset (see `--category`) must pass
    `snapshot_tag` so per-model snapshots land in a distinct file instead of overwriting
    the full-suite snapshot. `save_aggregate_progress` must stay off for filtered runs --
    a partial prompt set must never replace the canonical benchmark.json/RESULTS.md.
    """
    if models is None:
        models = MODELS
    if prompts is None:
        prompts = PROMPTS
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
            for prompt in prompts:
                pr = _run_prompt(prompt, model, port, n)
                mr.prompts.append(pr)
            results.append(mr)
            # Routine runs publish aggregate progress immediately. A full sweep disables
            # this so a failed overnight run cannot replace the canonical complete data.
            if save_aggregate_progress:
                _save_json(results)
                _save_markdown(results)
            suffix = f".{snapshot_tag}" if snapshot_tag else ""
            per_model_path = RESULTS_DIR / f"benchmark.{model.name}{suffix}.json"
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


def _filter_prompts(prompts: list[Prompt], categories: Iterable[str]) -> list[Prompt]:
    """Select prompts whose category is in `categories` (case-insensitive).

    Raises ValueError on an unknown category so a typo cannot silently select an
    empty or wrong subset -- that filtered run would otherwise look like results.
    """
    wanted = {category.strip().lower() for category in categories}
    unknown = wanted - {prompt.category for prompt in prompts}
    if unknown:
        msg = f"unknown categories: {', '.join(sorted(unknown))}"
        raise ValueError(msg)
    return [prompt for prompt in prompts if prompt.category in wanted]


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
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Comma-separated prompt categories to run (e.g. structured,consistency); "
        "filtered runs save tagged per-model snapshots and never publish canonical results",
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
    try:
        selected_prompts = _filter_prompts(PROMPTS, args.category.split(",")) if args.category else PROMPTS
    except ValueError as e:
        log.error("%s", e)
        raise SystemExit(2) from e
    # A run over the complete prompt set may publish canonical results; a filtered
    # run writes tagged snapshots only, whatever its scope flags are.
    complete_prompt_set = len(selected_prompts) == len(PROMPTS)
    snapshot_tag = None
    if not complete_prompt_set:
        snapshot_tag = "-".join(sorted({prompt.category for prompt in selected_prompts}))
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
        prompts=selected_prompts,
        save_aggregate_progress=not args.full_sweep and complete_prompt_set,
        snapshot_tag=snapshot_tag,
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

    for r in results:
        log.info(
            "%s: %d/%d pass in %.1fs, %.1f tok/s",
            r.model_name,
            r.passes,
            r.attempts_total,
            r.total_time_s,
            r.gen_tok_per_s,
        )
    if snapshot_tag is not None:
        log.info(
            "Category-filtered run (%s): tagged per-model snapshots only; canonical results unchanged",
            snapshot_tag,
        )
        return
    _save_json(results)
    _save_markdown(results)


if __name__ == "__main__":
    main()
