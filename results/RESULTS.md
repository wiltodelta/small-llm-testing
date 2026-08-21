# Benchmark results

Generated: 2026-08-21 08:05 UTC

Each prompt sampled multiple times; cell shows passes/n.
Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.
Fails split as wrong/timeout/empty -- a timeout is too-slow-to-finish, not a wrong answer.

## Summary

| Model | Passes | Fails (wrong/timeout/empty) | Total time | tok/s (gen, long-only) |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 65/66 | 1/0/0 | 764.6s | 29.9 |
| gemma-4-e2b-Q8_0-nothink | 47/66 | 19/0/0 | 103.0s | 30.1 |
| gemma-4-26b-a4b-Q4_K_M-think | 63/66 | 0/0/3 | 1758.2s | 17.5 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 64/66 | 2/0/0 | 88.0s | 19.7 |
| lfm2.5-8b-a1b-Q8_0 | 63/66 | 3/0/0 | 705.8s | 29.9 |
| mellum2-12b-a2.5b-think-Q4_K_M | 66/66 | 0/0/0 | 473.1s | 26.8 |
| qwen3.8-27b-Q4_K_M-think | 61/66 | 0/5/0 | 3826.4s | 2.6 |
| qwen3.8-27b-Q4_K_M-nothink | 52/66 | 14/0/0 | 506.2s | 2.8 |
| nemotron-3.5-lightning-30b-a3b-Q3_K_M | 60/66 | 0/0/6 | 2347.4s | 21.3 |
| north-mini-code-1.0-Q4_K_M | 62/66 | 0/0/4 | 1644.6s | 15.4 |

## gemma-4-e2b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.9 |  |
| math_multistep | math | 3/3 | 619 | 16.2 |  |
| math_modular | math | 3/3 | 658 | 16.6 |  |
| word_speed | reasoning | 3/3 | 1507 | 44.6 |  |
| word_age | reasoning | 3/3 | 783 | 19.7 |  |
| logic_syllogism_no | reasoning | 3/3 | 1116 | 35.7 |  |
| logic_negation | reasoning | 3/3 | 969 | 36.7 |  |
| code_fizzbuzz | coding | 3/3 | 2063 | 71.9 |  |
| code_palindrome | coding | 3/3 | 2017 | 66.8 |  |
| code_reverse_words | coding | 3/3 | 2289 | 76.2 |  |
| json_person | structured | 3/3 | 75 | 2.2 |  |
| format_primes | structured | 3/3 | 33 | 1.6 |  |
| json_fields | structured | 3/3 | 204 | 5.8 |  |
| cons_date_shift | consistency | 3/3 | 796 | 24.1 |  |
| cons_digit_swap | consistency | 3/3 | 715 | 20.7 |  |
| cons_dead_action | consistency | 2/3 | 783 | 26.5 | first token was 'no', want 'yes' |
| cons_unit_equivalent | consistency | 3/3 | 808 | 25.3 |  |
| cons_complementary | consistency | 3/3 | 595 | 25.3 |  |
| cons_relative_rank | consistency | 3/3 | 1266 | 44.2 |  |
| longctx_inconsistent | longcontext | 3/3 | 2251 | 78.1 |  |
| longctx_consistent | longcontext | 3/3 | 2439 | 89.8 |  |
| longctx_needle | longcontext | 3/3 | 805 | 34.7 |  |

## gemma-4-e2b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.9 |  |
| math_multistep | math | 0/3 | 12 | 1.1 | no number ~=158 |
| math_modular | math | 0/3 | 14 | 1.2 | no number ~=24 |
| word_speed | reasoning | 3/3 | 999 | 33.5 |  |
| word_age | reasoning | 2/3 | 9 | 0.9 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.7 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.8 |  |
| code_fizzbuzz | coding | 3/3 | 312 | 10.7 |  |
| code_palindrome | coding | 3/3 | 476 | 16.8 |  |
| code_reverse_words | coding | 3/3 | 346 | 10.7 |  |
| json_person | structured | 3/3 | 75 | 2.4 |  |
| format_primes | structured | 3/3 | 33 | 1.8 |  |
| json_fields | structured | 3/3 | 204 | 6.0 |  |
| cons_date_shift | consistency | 0/3 | 6 | 0.8 | first token was 'no', want 'yes' |
| cons_digit_swap | consistency | 3/3 | 6 | 0.8 |  |
| cons_dead_action | consistency | 0/3 | 6 | 0.7 | first token was 'no', want 'yes' |
| cons_unit_equivalent | consistency | 3/3 | 6 | 0.7 |  |
| cons_complementary | consistency | 3/3 | 6 | 0.8 |  |
| cons_relative_rank | consistency | 3/3 | 6 | 0.6 |  |
| longctx_inconsistent | longcontext | 0/3 | 6 | 4.9 | first token was 'no', want 'yes' |
| longctx_consistent | longcontext | 3/3 | 6 | 0.9 |  |
| longctx_needle | longcontext | 3/3 | 15 | 5.5 |  |

## gemma-4-26b-a4b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 807 | 49.4 |  |
| math_multistep | math | 3/3 | 783 | 38.8 |  |
| math_modular | math | 3/3 | 809 | 37.4 |  |
| word_speed | reasoning | 3/3 | 893 | 42.3 |  |
| word_age | reasoning | 3/3 | 719 | 34.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 829 | 43.5 |  |
| logic_negation | reasoning | 3/3 | 773 | 40.5 |  |
| code_fizzbuzz | coding | 3/3 | 1391 | 65.9 |  |
| code_palindrome | coding | 3/3 | 1470 | 72.5 |  |
| code_reverse_words | coding | 3/3 | 1309 | 69.2 |  |
| json_person | structured | 3/3 | 75 | 4.5 |  |
| format_primes | structured | 3/3 | 45 | 3.0 |  |
| json_fields | structured | 3/3 | 204 | 10.9 |  |
| cons_date_shift | consistency | 3/3 | 880 | 48.9 |  |
| cons_digit_swap | consistency | 3/3 | 471 | 24.4 |  |
| cons_dead_action | consistency | 3/3 | 644 | 35.0 |  |
| cons_unit_equivalent | consistency | 3/3 | 577 | 29.7 |  |
| cons_complementary | consistency | 3/3 | 600 | 35.3 |  |
| cons_relative_rank | consistency | 3/3 | 719 | 39.8 |  |
| longctx_inconsistent | longcontext | 3/3 | 4114 | 267.9 |  |
| longctx_consistent | longcontext | 0/3 | 12288 | 731.9 | empty |
| longctx_needle | longcontext | 3/3 | 422 | 32.5 |  |

## gemma-4-26b-a4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.4 |  |
| math_multistep | math | 3/3 | 12 | 1.7 |  |
| math_modular | math | 3/3 | 9 | 1.1 |  |
| word_speed | reasoning | 1/3 | 9 | 1.7 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 1.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.2 |  |
| logic_negation | reasoning | 3/3 | 6 | 1.5 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 13.2 |  |
| code_palindrome | coding | 3/3 | 242 | 12.6 |  |
| code_reverse_words | coding | 3/3 | 96 | 5.3 |  |
| json_person | structured | 3/3 | 75 | 4.2 |  |
| format_primes | structured | 3/3 | 45 | 2.9 |  |
| json_fields | structured | 3/3 | 204 | 10.2 |  |
| cons_date_shift | consistency | 3/3 | 6 | 1.5 |  |
| cons_digit_swap | consistency | 3/3 | 6 | 1.5 |  |
| cons_dead_action | consistency | 3/3 | 6 | 1.4 |  |
| cons_unit_equivalent | consistency | 3/3 | 6 | 1.2 |  |
| cons_complementary | consistency | 3/3 | 6 | 1.6 |  |
| cons_relative_rank | consistency | 3/3 | 6 | 1.4 |  |
| longctx_inconsistent | longcontext | 3/3 | 6 | 9.4 |  |
| longctx_consistent | longcontext | 3/3 | 6 | 1.9 |  |
| longctx_needle | longcontext | 3/3 | 15 | 9.8 |  |

## lfm2.5-8b-a1b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 331 | 10.8 |  |
| math_multistep | math | 3/3 | 284 | 9.7 |  |
| math_modular | math | 3/3 | 315 | 10.9 |  |
| word_speed | reasoning | 3/3 | 565 | 19.3 |  |
| word_age | reasoning | 3/3 | 498 | 16.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 569 | 18.7 |  |
| logic_negation | reasoning | 3/3 | 454 | 15.2 |  |
| code_fizzbuzz | coding | 3/3 | 822 | 26.9 |  |
| code_palindrome | coding | 3/3 | 618 | 20.2 |  |
| code_reverse_words | coding | 3/3 | 548 | 17.7 |  |
| json_person | structured | 3/3 | 414 | 13.6 |  |
| format_primes | structured | 3/3 | 291 | 9.9 |  |
| json_fields | structured | 3/3 | 1050 | 33.9 |  |
| cons_date_shift | consistency | 3/3 | 922 | 30.9 |  |
| cons_digit_swap | consistency | 3/3 | 520 | 17.9 |  |
| cons_dead_action | consistency | 2/3 | 803 | 28.1 | first token was 'no', want 'yes' |
| cons_unit_equivalent | consistency | 3/3 | 451 | 15.8 |  |
| cons_complementary | consistency | 3/3 | 437 | 15.4 |  |
| cons_relative_rank | consistency | 3/3 | 1002 | 32.9 |  |
| longctx_inconsistent | longcontext | 1/3 | 4611 | 134.5 | first token was 'no', want 'yes' |
| longctx_consistent | longcontext | 3/3 | 5312 | 192.4 |  |
| longctx_needle | longcontext | 3/3 | 312 | 14.5 |  |

## mellum2-12b-a2.5b-think-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 199 | 7.4 |  |
| math_multistep | math | 3/3 | 581 | 21.9 |  |
| math_modular | math | 3/3 | 222 | 8.3 |  |
| word_speed | reasoning | 3/3 | 635 | 22.8 |  |
| word_age | reasoning | 3/3 | 614 | 21.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 262 | 9.1 |  |
| logic_negation | reasoning | 3/3 | 250 | 9.2 |  |
| code_fizzbuzz | coding | 3/3 | 462 | 17.5 |  |
| code_palindrome | coding | 3/3 | 472 | 15.8 |  |
| code_reverse_words | coding | 3/3 | 592 | 20.0 |  |
| json_person | structured | 3/3 | 60 | 2.3 |  |
| format_primes | structured | 3/3 | 37 | 1.7 |  |
| json_fields | structured | 3/3 | 182 | 6.3 |  |
| cons_date_shift | consistency | 3/3 | 334 | 11.1 |  |
| cons_digit_swap | consistency | 3/3 | 384 | 12.7 |  |
| cons_dead_action | consistency | 3/3 | 293 | 9.6 |  |
| cons_unit_equivalent | consistency | 3/3 | 279 | 9.2 |  |
| cons_complementary | consistency | 3/3 | 285 | 9.4 |  |
| cons_relative_rank | consistency | 3/3 | 533 | 18.1 |  |
| longctx_inconsistent | longcontext | 3/3 | 1335 | 56.8 |  |
| longctx_consistent | longcontext | 3/3 | 4250 | 162.7 |  |
| longctx_needle | longcontext | 3/3 | 406 | 20.3 |  |

## qwen3.8-27b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 161 | 58.4 |  |
| math_multistep | math | 3/3 | 162 | 57.0 |  |
| math_modular | math | 3/3 | 221 | 80.8 |  |
| word_speed | reasoning | 3/3 | 252 | 89.7 |  |
| word_age | reasoning | 3/3 | 193 | 77.3 |  |
| logic_syllogism_no | reasoning | 3/3 | 263 | 96.6 |  |
| logic_negation | reasoning | 3/3 | 199 | 73.1 |  |
| code_fizzbuzz | coding | 3/3 | 496 | 183.7 |  |
| code_palindrome | coding | 3/3 | 420 | 163.4 |  |
| code_reverse_words | coding | 3/3 | 391 | 140.6 |  |
| json_person | structured | 3/3 | 60 | 27.2 |  |
| format_primes | structured | 3/3 | 45 | 21.6 |  |
| json_fields | structured | 3/3 | 189 | 75.3 |  |
| cons_date_shift | consistency | 1/3 | 166 | 665.4 | api error: TimeoutError: timed out |
| cons_digit_swap | consistency | 3/3 | 201 | 75.9 |  |
| cons_dead_action | consistency | 3/3 | 309 | 115.4 |  |
| cons_unit_equivalent | consistency | 3/3 | 229 | 86.3 |  |
| cons_complementary | consistency | 3/3 | 217 | 82.7 |  |
| cons_relative_rank | consistency | 3/3 | 1004 | 360.2 |  |
| longctx_inconsistent | longcontext | 3/3 | 588 | 257.5 |  |
| longctx_consistent | longcontext | 0/3 | 0 | 900.0 | api error: TimeoutError: timed out |
| longctx_needle | longcontext | 3/3 | 218 | 138.1 |  |

## qwen3.8-27b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 6.7 |  |
| math_multistep | math | 0/3 | 12 | 7.0 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 6.2 |  |
| word_speed | reasoning | 0/3 | 6 | 5.1 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 6.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 5.0 |  |
| logic_negation | reasoning | 3/3 | 6 | 4.9 |  |
| code_fizzbuzz | coding | 3/3 | 251 | 90.8 |  |
| code_palindrome | coding | 3/3 | 130 | 48.8 |  |
| code_reverse_words | coding | 3/3 | 89 | 33.5 |  |
| json_person | structured | 3/3 | 60 | 23.9 |  |
| format_primes | structured | 3/3 | 45 | 18.3 |  |
| json_fields | structured | 3/3 | 189 | 69.1 |  |
| cons_date_shift | consistency | 0/3 | 6 | 5.1 | first token was 'no', want 'yes' |
| cons_digit_swap | consistency | 3/3 | 6 | 4.9 |  |
| cons_dead_action | consistency | 0/3 | 6 | 4.9 | first token was 'no', want 'yes' |
| cons_unit_equivalent | consistency | 3/3 | 6 | 4.8 |  |
| cons_complementary | consistency | 3/3 | 6 | 4.9 |  |
| cons_relative_rank | consistency | 3/3 | 6 | 4.8 |  |
| longctx_inconsistent | longcontext | 3/3 | 6 | 59.1 |  |
| longctx_consistent | longcontext | 1/3 | 6 | 28.5 | first token was 'yes', want 'no' |
| longctx_needle | longcontext | 3/3 | 15 | 64.0 |  |

## nemotron-3.5-lightning-30b-a3b-Q3_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 743 | 35.9 |  |
| math_multistep | math | 3/3 | 775 | 34.0 |  |
| math_modular | math | 3/3 | 897 | 39.0 |  |
| word_speed | reasoning | 3/3 | 1622 | 76.1 |  |
| word_age | reasoning | 3/3 | 873 | 38.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 2353 | 133.5 |  |
| logic_negation | reasoning | 3/3 | 1009 | 51.5 |  |
| code_fizzbuzz | coding | 3/3 | 1347 | 61.9 |  |
| code_palindrome | coding | 3/3 | 2541 | 126.2 |  |
| code_reverse_words | coding | 3/3 | 1803 | 83.3 |  |
| json_person | structured | 3/3 | 50 | 3.0 |  |
| format_primes | structured | 3/3 | 37 | 2.4 |  |
| json_fields | structured | 3/3 | 159 | 6.8 |  |
| cons_date_shift | consistency | 3/3 | 1488 | 76.5 |  |
| cons_digit_swap | consistency | 3/3 | 1100 | 57.2 |  |
| cons_dead_action | consistency | 3/3 | 1427 | 71.7 |  |
| cons_unit_equivalent | consistency | 3/3 | 1035 | 50.2 |  |
| cons_complementary | consistency | 3/3 | 1042 | 55.8 |  |
| cons_relative_rank | consistency | 3/3 | 4606 | 240.3 |  |
| longctx_inconsistent | longcontext | 0/3 | 12288 | 522.1 | empty |
| longctx_consistent | longcontext | 0/3 | 12288 | 546.8 | empty |
| longctx_needle | longcontext | 3/3 | 571 | 35.2 |  |

## north-mini-code-1.0-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 218 | 13.8 |  |
| math_multistep | math | 3/3 | 182 | 11.6 |  |
| math_modular | math | 3/3 | 194 | 12.2 |  |
| word_speed | reasoning | 3/3 | 420 | 24.9 |  |
| word_age | reasoning | 3/3 | 272 | 16.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 379 | 21.6 |  |
| logic_negation | reasoning | 3/3 | 359 | 20.5 |  |
| code_fizzbuzz | coding | 3/3 | 806 | 44.8 |  |
| code_palindrome | coding | 3/3 | 741 | 41.4 |  |
| code_reverse_words | coding | 3/3 | 732 | 40.9 |  |
| json_person | structured | 3/3 | 402 | 22.8 |  |
| format_primes | structured | 3/3 | 303 | 17.6 |  |
| json_fields | structured | 3/3 | 777 | 43.5 |  |
| cons_date_shift | consistency | 3/3 | 339 | 19.4 |  |
| cons_digit_swap | consistency | 3/3 | 263 | 15.3 |  |
| cons_dead_action | consistency | 3/3 | 320 | 18.6 |  |
| cons_unit_equivalent | consistency | 3/3 | 219 | 13.1 |  |
| cons_complementary | consistency | 3/3 | 297 | 17.1 |  |
| cons_relative_rank | consistency | 3/3 | 570 | 32.6 |  |
| longctx_inconsistent | longcontext | 2/3 | 4848 | 329.0 | empty |
| longctx_consistent | longcontext | 0/3 | 12288 | 837.6 | empty |
| longctx_needle | longcontext | 3/3 | 324 | 30.2 |  |
