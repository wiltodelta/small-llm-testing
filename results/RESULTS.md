# Benchmark results

Generated: 2026-08-26 23:16 UTC

Each prompt sampled multiple times; cell shows passes/n.
Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.
Fails split as wrong/timeout/empty/truncated -- only `wrong` is a model verdict; the other
three mean the harness stopped the attempt (request timeout, API error, generation cap).

## Summary

| Model | Passes | Fails (wrong/timeout/empty/truncated) | Total time | tok/s (gen, long-only) |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 65/66 | 1/0/0/0 | 405.4s | 61.0 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 64/66 | 2/0/0/0 | 66.0s | 26.6 |
| mellum2-12b-a2.5b-think-Q4_K_M | 66/66 | 0/0/0/0 | 527.1s | 45.2 |
| granite-4.2-8b-Q8_0-low-effort | 62/66 | 4/0/0/0 | 239.9s | 10.9 |

## gemma-4-e2b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 521 | 6.9 |  |
| math_multistep | math | 3/3 | 521 | 6.7 |  |
| math_modular | math | 3/3 | 600 | 8.1 |  |
| word_speed | reasoning | 3/3 | 1519 | 26.1 |  |
| word_age | reasoning | 3/3 | 804 | 14.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 1039 | 19.7 |  |
| logic_negation | reasoning | 3/3 | 1096 | 17.9 |  |
| code_fizzbuzz | coding | 3/3 | 2085 | 30.8 |  |
| code_palindrome | coding | 3/3 | 2132 | 31.3 |  |
| code_reverse_words | coding | 3/3 | 2575 | 40.2 |  |
| json_person | structured | 3/3 | 75 | 1.2 |  |
| format_primes | structured | 3/3 | 33 | 0.7 |  |
| json_fields | structured | 3/3 | 204 | 2.8 |  |
| cons_date_shift | consistency | 3/3 | 705 | 10.8 |  |
| cons_digit_swap | consistency | 3/3 | 789 | 12.1 |  |
| cons_dead_action | consistency | 2/3 | 934 | 14.8 | first token was 'no', want 'yes' |
| cons_unit_equivalent | consistency | 3/3 | 842 | 12.0 |  |
| cons_complementary | consistency | 3/3 | 606 | 9.8 |  |
| cons_relative_rank | consistency | 3/3 | 1355 | 21.2 |  |
| longctx_inconsistent | longcontext | 3/3 | 2473 | 46.7 |  |
| longctx_consistent | longcontext | 3/3 | 2964 | 54.3 |  |
| longctx_needle | longcontext | 3/3 | 850 | 16.5 |  |

## gemma-4-26b-a4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.9 |  |
| math_multistep | math | 3/3 | 12 | 1.0 |  |
| math_modular | math | 3/3 | 9 | 0.9 |  |
| word_speed | reasoning | 1/3 | 9 | 1.0 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 0.9 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.0 |  |
| logic_negation | reasoning | 3/3 | 6 | 0.9 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 9.4 |  |
| code_palindrome | coding | 3/3 | 268 | 10.6 |  |
| code_reverse_words | coding | 3/3 | 96 | 3.9 |  |
| json_person | structured | 3/3 | 75 | 3.0 |  |
| format_primes | structured | 3/3 | 45 | 2.1 |  |
| json_fields | structured | 3/3 | 204 | 7.6 |  |
| cons_date_shift | consistency | 3/3 | 6 | 1.1 |  |
| cons_digit_swap | consistency | 3/3 | 6 | 1.1 |  |
| cons_dead_action | consistency | 3/3 | 6 | 1.0 |  |
| cons_unit_equivalent | consistency | 3/3 | 6 | 1.0 |  |
| cons_complementary | consistency | 3/3 | 6 | 0.9 |  |
| cons_relative_rank | consistency | 3/3 | 6 | 1.0 |  |
| longctx_inconsistent | longcontext | 3/3 | 6 | 7.1 |  |
| longctx_consistent | longcontext | 3/3 | 6 | 1.4 |  |
| longctx_needle | longcontext | 3/3 | 15 | 8.0 |  |

## mellum2-12b-a2.5b-think-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 191 | 3.2 |  |
| math_multistep | math | 3/3 | 682 | 12.4 |  |
| math_modular | math | 3/3 | 282 | 5.7 |  |
| word_speed | reasoning | 3/3 | 733 | 14.4 |  |
| word_age | reasoning | 3/3 | 464 | 9.2 |  |
| logic_syllogism_no | reasoning | 3/3 | 363 | 7.3 |  |
| logic_negation | reasoning | 3/3 | 471 | 9.3 |  |
| code_fizzbuzz | coding | 3/3 | 359 | 7.4 |  |
| code_palindrome | coding | 3/3 | 439 | 8.7 |  |
| code_reverse_words | coding | 3/3 | 631 | 11.7 |  |
| json_person | structured | 3/3 | 60 | 1.5 |  |
| format_primes | structured | 3/3 | 33 | 1.0 |  |
| json_fields | structured | 3/3 | 172 | 3.6 |  |
| cons_date_shift | consistency | 3/3 | 365 | 7.5 |  |
| cons_digit_swap | consistency | 3/3 | 253 | 5.4 |  |
| cons_dead_action | consistency | 3/3 | 279 | 6.0 |  |
| cons_unit_equivalent | consistency | 3/3 | 256 | 5.3 |  |
| cons_complementary | consistency | 3/3 | 196 | 3.8 |  |
| cons_relative_rank | consistency | 3/3 | 494 | 9.3 |  |
| longctx_inconsistent | longcontext | 3/3 | 1365 | 30.3 |  |
| longctx_consistent | longcontext | 3/3 | 15356 | 350.1 |  |
| longctx_needle | longcontext | 3/3 | 374 | 14.0 |  |

## granite-4.2-8b-Q8_0-low-effort

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 33 | 3.0 |  |
| math_multistep | math | 3/3 | 72 | 6.3 |  |
| math_modular | math | 3/3 | 58 | 6.1 |  |
| word_speed | reasoning | 3/3 | 162 | 13.9 |  |
| word_age | reasoning | 3/3 | 70 | 6.0 |  |
| logic_syllogism_no | reasoning | 0/3 | 27 | 2.4 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 27 | 2.5 |  |
| code_fizzbuzz | coding | 3/3 | 350 | 29.6 |  |
| code_palindrome | coding | 3/3 | 221 | 20.0 |  |
| code_reverse_words | coding | 3/3 | 168 | 15.1 |  |
| json_person | structured | 3/3 | 39 | 3.7 |  |
| format_primes | structured | 3/3 | 42 | 4.0 |  |
| json_fields | structured | 3/3 | 166 | 16.1 |  |
| cons_date_shift | consistency | 3/3 | 138 | 13.4 |  |
| cons_digit_swap | consistency | 2/3 | 107 | 10.4 | first token was 'no', want 'yes' |
| cons_dead_action | consistency | 3/3 | 160 | 15.9 |  |
| cons_unit_equivalent | consistency | 3/3 | 56 | 5.5 |  |
| cons_complementary | consistency | 3/3 | 39 | 4.0 |  |
| cons_relative_rank | consistency | 3/3 | 185 | 18.3 |  |
| longctx_inconsistent | longcontext | 3/3 | 112 | 21.6 |  |
| longctx_consistent | longcontext | 3/3 | 90 | 9.9 |  |
| longctx_needle | longcontext | 3/3 | 33 | 12.2 |  |
