# Benchmark design

## Test set

12 text prompts (discriminating core) across 4 categories: math (3), reasoning (4),
coding (3, executed), structured (2). Every config is scored on the same prompts
(`/36` at n=3). Trimmed from the original 16 -- trivial prompts that every model passed
(math_div, math_percent, logic_syllogism_yes, code_total, both translations) and the
brittle substring `summarize` were dropped (no signal, ceiling). Vision (3 chart-OCR
prompts) was removed too: it was supported unevenly across the model set (text-only for
Qwen-MTP / GLM / LFM / Mellum, and the Gemma 4 12B QAT mmproj fails to load), and
the mmproj path was a recurring source of server-start failures. The `structured`
category (JSON extraction + strict-format output) probes instruction-following /
function-calling -- the strength of agentic models (Ministral / GLM / Qwen3.6) that the
reasoning core alone misses. Verifiers (no LLM judge -- all mechanical):

- `v_number(expected, tol)` -- finds any decimal in answer matching expected within tolerance
- `v_yes_no(want_yes)` -- first yes/no token must match (catches "yes, but actually no")
- `v_regex(pattern)` -- regex search (used by `format_primes` for strict comma-list output)
- `v_python_exec(test_cases)` -- extracts Python from `\`\`\`python\`\`\`` block, runs it
  in a subprocess, asserts each `(call_expr, expected_value)` returns expected. Expected
  values are embedded via `repr()` (NOT `json.dumps`, which turns `True`->`true` -> NameError)
- `v_json(expected)` -- parses the first `{...}` span (tolerates a ```\`\`\`json``` fence or
  prose), checks each key; numbers compare by value, strings case-insensitively

`_strip_think(text)` removes `<think>...</think>` blocks before verification.

**Per-category thinking:** `_thinks(cfg, prompt)` gates thinking to
`THINKING_CATEGORIES` (math/reasoning/coding). `structured` is deliberately excluded --
thinking on JSON/strict-format tasks wastes tokens and can break the format -- so the
gate is meaningful: `-think` configs run the structured prompts direct.

**Fail classification:** `fail_kind` splits failures into `wrong` / `timeout` /
`empty` so the summary table never conflates "too slow to finish" with "wrong answer".
Failed API attempts retain their measured wall time; a request timeout therefore
contributes the full timeout duration to prompt and model totals.
Speed (tok/s) from a long suite run is thermally throttled -- use `llama-bench` on a
cool machine for true peak decode speed; the suite's tok/s is for relative A/Bs.

**Evaluating accuracy-affecting toggles (think/no-think, sampling): run BOTH variants and
read per-category, never judge from the aggregate.** Both Gemma 4 and Qwen run a
think/nothink pair for exactly this reason. A mistake made here: "Gemma thinking only
slows it, no accuracy gain" was concluded from an aggregate (35 vs 36) compared against a
non-comparable older prompt set; the per-category data actually showed thinking is worth
+6..+9 on dense small/mid Gemma (it rescues math_modular/multistep and reasoning). The
aggregate hid it because `structured` is at ceiling for everyone and dilutes the signal.
