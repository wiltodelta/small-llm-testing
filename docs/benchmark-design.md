# Benchmark design

## Target scenario

The suite screens small local models for a background data-auditing agent: an
unattended process that slowly reads reference material (wiki-scale articles),
compares statements, and emits structured findings. The suite measures the
model-level capabilities that role needs at the single-call level; the
orchestration around the model (tool loops, multi-turn state) is deliberately out
of scope -- a text core that discriminates models is the input to any harness.

## Test set

22 text prompts across 6 categories: math (3), reasoning (4), coding (3, executed),
structured (3), consistency (6), longcontext (3). Every config is scored on the same
prompts (`/66` at n=3). The first four categories are the trimmed discriminating core:
trivial prompts that every model passed (math_div, math_percent, logic_syllogism_yes,
code_total, translate_fr/es) and the brittle substring `summarize` were dropped (no
signal, ceiling). Vision (3 chart-OCR prompts) was removed too: it was supported
unevenly across the historical model set, and the mmproj path was a recurring source
of server-start failures. The `structured` category (JSON extraction + strict-format
output) probes instruction-following / function-calling, a dimension that the
reasoning core alone misses. Verifiers (no LLM judge -- all mechanical):

- `v_number(expected, tol)` -- finds any decimal in answer matching expected within tolerance
- `v_yes_no(want_yes)` -- first yes/no token must match (catches "yes, but actually no")
- `v_regex(pattern)` -- regex search (used by `format_primes` for strict comma-list output)
- `v_python_exec(test_cases)` -- extracts Python from a ```python``` block, runs it
  in a subprocess, asserts each `(call_expr, expected_value)` returns expected. Expected
  values are embedded via `repr()` (NOT `json.dumps`, which turns `True`->`true` -> NameError)
- `v_json(expected)` -- parses the first `{...}` span (tolerates a ```json fence or
  prose), checks each key; numbers compare by value, strings case-insensitively, and
  lists of strings case- and order-insensitively (a members list reported in a different
  order is not a wrong answer)

`_strip_think(text)` removes `<think>...</think>` blocks before verification.

## Agent-scenario categories

### consistency (6 prompts)

Two short statements, wiki-edit shaped (infobox range vs prose death year, transposed
digits, an action after a stated death, unit-equal values, complementary facts,
relative ranks), and the question "do these two statements contradict each other?".
All entities are fictional, so world knowledge cannot substitute for reading the
statements -- the exact failure the `logic_syllogism_no` trap documented in real
models. The set is balanced 3 contradictions / 3 non-contradictions, so an
always-yes or always-no bias scores 50%.

### longcontext (3 prompts)

One deterministic fictional encyclopedia article (~9.4k chars, ~2.5k tokens,
hand-written so every date, count, and honour cross-checks; `tests/test_prompts.py`
pins the invariants). Three prompts over it:

- `longctx_inconsistent` -- a variant with exactly one planted contradiction (Legacy
  birth year 1891 vs lead/Early-life 1887, thousands of tokens apart). The core
  wiki-audit task at article scale.
- `longctx_consistent` -- byte-identical length and shape, no contradiction: the
  false-positive rate, which for an unattended agent is as damaging as a miss.
- `longctx_needle` -- one dated fact (The Salt Garden premiere, 1928) buried mid-list
  among distractor years, stated exactly once.

Article length is bounded (tests pin 9k-14k chars). These prompts are marked
`article_sized`, and their generation cap is derived per model as
`ModelConfig.n_ctx - ARTICLE_PROMPT_RESERVE` rather than pinned to a literal. That is a
harness constraint, not a claim that 2.5k tokens is a long article for a 262k-context
model.

**Why the cap is derived (2026-08-21).** It used to be a flat 4096, copied from the
smallest server context in the fleet. Every `empty` result in the 2026-08-21 sweep was
exactly 4096 completion tokens, decoded at the config's normal speed: Nemotron 6/6,
North Mini 3/3, Gemma 26B think 3/3. None of them failed to answer; all of them were cut
mid-thought. Since the other four categories sit at ceiling for seven of ten configs,
that single literal decided most of the published ranking. One model's memory bound must
never become the whole fleet's answer budget.

**What the wider budget then measured (2026-08-21, single attempt).** North Mini Code at
`-c 16384` was re-run on `longctx_consistent` with the derived 12,288-token cap. It hit
that cap too: `finish_reason: "length"`, 12,288 completion tokens, 968s, and nothing left
after `_strip_think`. So the wider budget does not rescue it -- it converts an
uninterpretable `empty` into a measured refusal to terminate on the article that contains
nothing to find. That is the point of the change: at 4,096 tokens truncation and inability
were indistinguishable, and now they are not. Note the same attempt would have been a
`timeout` under the old 300s `REQUEST_TIMEOUT`, which is why the timeout and the cap move
together.

### structured (3 prompts)

`json_person` and `format_primes` are unchanged; `json_fields` (added 2026-08-17)
extracts an object with string, integer, boolean-false, and array-of-strings values
from prose containing a distractor year -- the report shape a background auditing
agent emits per finding.

## Per-category thinking

`_thinks(cfg, prompt)` gates thinking to `THINKING_CATEGORIES`
(math/reasoning/coding/consistency/longcontext). `structured` is deliberately
excluded -- thinking on JSON/strict-format tasks wastes tokens and can break the
format -- so the gate is meaningful: `-think` configs run the structured prompts
direct. `consistency` and `longcontext` join the gate because contradiction-finding
is reasoning and a background agent is latency-insensitive.

## Fail classification

`fail_kind` splits failures into `wrong` / `timeout` / `empty` / `truncated` so the
summary table never conflates a harness limit with a wrong answer. Only `wrong` is a
model verdict: the attempt finished on its own and the verifier rejected it. `truncated`
means llama.cpp reported `finish_reason: "length"`, so the generation cap stopped the
model mid-answer and the verifier judged a fragment. Failed API attempts retain
their measured wall time; a request timeout therefore contributes the full timeout
duration to prompt and model totals.
Speed (tok/s) from a long suite run is thermally throttled -- use `llama-bench` on a
cool machine for true peak decode speed; the suite's tok/s is for relative A/Bs.

**`REQUEST_TIMEOUT` and the generation cap are one setting.** An attempt can only reach
its cap if `REQUEST_TIMEOUT >= cap / decode tok/s`. When it cannot, every long prompt on
that config records `timeout` and the category measures the harness. Check the arithmetic
against the slowest config in the run before trusting a long-context column.

**Evaluating accuracy-affecting toggles (think/no-think, sampling): run both variants and
read per-category, never judge from the aggregate.** The curated Gemma configurations
retain a think/nothink pair for exactly this reason. A previous aggregate suggested that
thinking only added latency, while the comparable per-category run showed that it rescued
math and reasoning cases on smaller Gemma models. The aggregate hid the effect because
`structured` was at ceiling and diluted the signal.

## Reliability rechecks at higher n

The routine suite runs n=3 per prompt. For a shortlisted model, the agent scenario
wants a sharper estimate of the report-format and contradiction-detection rates, so
rerun the relevant categories at high n:

```bash
uv run python benchmark.py --model gemma-4-e2b --category structured,consistency -n 20
```

Category-filtered runs never publish canonical results: they write per-model
snapshots as `results/benchmark.<model>.<categories>.json` and leave
`benchmark.json`/`RESULTS.md` untouched. An unknown category name aborts with exit
code 2 rather than silently selecting a wrong subset.
