# Benchmark results

Generated: 2026-08-09 22:48 UTC

Each prompt sampled multiple times; cell shows passes/n.
Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.
Fails split as wrong/timeout/empty -- a timeout is too-slow-to-finish, not a wrong answer.

## Summary

| Model | Passes | Fails (wrong/timeout/empty) | Total time | tok/s (gen, long-only) |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 317.1s | 38.2 |
| gemma-4-e2b-Q8_0-nothink | 26/36 | 10/0/0 | 62.2s | 38.8 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 657.6s | 15.9 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 34/36 | 2/0/0 | 53.1s | 16.7 |
| lfm2.5-8b-a1b-Q8_0 | 35/36 | 1/0/0 | 227.0s | 24.7 |
| lfm2.5-2.6b-Q8_0 | 36/36 | 0/0/0 | 630.6s | 17.6 |
| nanbeige4.2-3b-Q8_0-think | 36/36 | 0/0/0 | 2236.1s | 8.5 |
| nanbeige4.2-3b-Q8_0-nothink | 28/36 | 8/0/0 | 222.7s | 9.3 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 163.0s | 30.7 |

## gemma-4-e2b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 253 | 5.2 |  |
| math_multistep | math | 3/3 | 525 | 10.2 |  |
| math_modular | math | 3/3 | 521 | 10.6 |  |
| word_speed | reasoning | 3/3 | 1213 | 29.1 |  |
| word_age | reasoning | 3/3 | 828 | 24.1 |  |
| logic_syllogism_no | reasoning | 3/3 | 992 | 33.2 |  |
| logic_negation | reasoning | 3/3 | 940 | 29.5 |  |
| code_fizzbuzz | coding | 3/3 | 2133 | 54.4 |  |
| code_palindrome | coding | 3/3 | 2307 | 59.6 |  |
| code_reverse_words | coding | 3/3 | 2270 | 58.2 |  |
| json_person | structured | 3/3 | 75 | 1.8 |  |
| format_primes | structured | 3/3 | 33 | 1.1 |  |

## gemma-4-e2b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.4 |  |
| math_multistep | math | 0/3 | 12 | 0.5 | no number ~=158 |
| math_modular | math | 0/3 | 15 | 0.7 | no number ~=24 |
| word_speed | reasoning | 3/3 | 962 | 26.3 |  |
| word_age | reasoning | 2/3 | 9 | 0.7 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.6 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.6 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 5.8 |  |
| code_palindrome | coding | 3/3 | 533 | 13.4 |  |
| code_reverse_words | coding | 3/3 | 392 | 10.0 |  |
| json_person | structured | 3/3 | 75 | 2.0 |  |
| format_primes | structured | 3/3 | 33 | 1.2 |  |

## gemma-4-26b-a4b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 803 | 43.6 |  |
| math_multistep | math | 3/3 | 826 | 47.5 |  |
| math_modular | math | 3/3 | 934 | 53.6 |  |
| word_speed | reasoning | 3/3 | 986 | 64.0 |  |
| word_age | reasoning | 3/3 | 588 | 44.6 |  |
| logic_syllogism_no | reasoning | 3/3 | 814 | 51.2 |  |
| logic_negation | reasoning | 3/3 | 932 | 65.0 |  |
| code_fizzbuzz | coding | 3/3 | 2103 | 132.0 |  |
| code_palindrome | coding | 3/3 | 1161 | 75.6 |  |
| code_reverse_words | coding | 3/3 | 1131 | 71.2 |  |
| json_person | structured | 3/3 | 75 | 5.3 |  |
| format_primes | structured | 3/3 | 45 | 4.0 |  |

## gemma-4-26b-a4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.4 |  |
| math_multistep | math | 3/3 | 12 | 1.7 |  |
| math_modular | math | 3/3 | 9 | 1.4 |  |
| word_speed | reasoning | 1/3 | 9 | 1.6 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 1.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.4 |  |
| logic_negation | reasoning | 3/3 | 6 | 1.4 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 15.0 |  |
| code_palindrome | coding | 3/3 | 223 | 14.2 |  |
| code_reverse_words | coding | 3/3 | 96 | 5.9 |  |
| json_person | structured | 3/3 | 75 | 4.5 |  |
| format_primes | structured | 3/3 | 45 | 3.2 |  |

## lfm2.5-8b-a1b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 233 | 11.0 |  |
| math_multistep | math | 3/3 | 290 | 12.8 |  |
| math_modular | math | 3/3 | 318 | 12.7 |  |
| word_speed | reasoning | 3/3 | 574 | 20.8 |  |
| word_age | reasoning | 3/3 | 469 | 22.2 |  |
| logic_syllogism_no | reasoning | 2/3 | 639 | 24.2 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 468 | 17.8 |  |
| code_fizzbuzz | coding | 3/3 | 767 | 30.0 |  |
| code_palindrome | coding | 3/3 | 655 | 25.2 |  |
| code_reverse_words | coding | 3/3 | 564 | 21.4 |  |
| json_person | structured | 3/3 | 348 | 14.3 |  |
| format_primes | structured | 3/3 | 292 | 14.6 |  |

## lfm2.5-2.6b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 343 | 21.5 |  |
| math_multistep | math | 3/3 | 434 | 26.0 |  |
| math_modular | math | 3/3 | 838 | 52.5 |  |
| word_speed | reasoning | 3/3 | 1017 | 59.6 |  |
| word_age | reasoning | 3/3 | 874 | 51.7 |  |
| logic_syllogism_no | reasoning | 3/3 | 1287 | 74.1 |  |
| logic_negation | reasoning | 3/3 | 895 | 49.6 |  |
| code_fizzbuzz | coding | 3/3 | 1787 | 94.0 |  |
| code_palindrome | coding | 3/3 | 917 | 52.8 |  |
| code_reverse_words | coding | 3/3 | 1399 | 79.5 |  |
| json_person | structured | 3/3 | 496 | 27.3 |  |
| format_primes | structured | 3/3 | 810 | 42.1 |  |

## nanbeige4.2-3b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 626 | 83.3 |  |
| math_multistep | math | 3/3 | 657 | 86.0 |  |
| math_modular | math | 3/3 | 739 | 133.0 |  |
| word_speed | reasoning | 3/3 | 1673 | 262.0 |  |
| word_age | reasoning | 3/3 | 724 | 109.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 4211 | 431.8 |  |
| logic_negation | reasoning | 3/3 | 1465 | 125.7 |  |
| code_fizzbuzz | coding | 3/3 | 2720 | 300.1 |  |
| code_palindrome | coding | 3/3 | 3176 | 390.3 |  |
| code_reverse_words | coding | 3/3 | 2875 | 305.5 |  |
| json_person | structured | 3/3 | 42 | 4.4 |  |
| format_primes | structured | 3/3 | 45 | 4.7 |  |

## nanbeige4.2-3b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.1 |  |
| math_multistep | math | 0/3 | 12 | 2.0 | no number ~=158 |
| math_modular | math | 2/3 | 822 | 87.5 | no number ~=24 |
| word_speed | reasoning | 3/3 | 438 | 49.3 |  |
| word_age | reasoning | 2/3 | 157 | 17.2 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 7 | 0.9 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.7 |  |
| code_fizzbuzz | coding | 3/3 | 252 | 25.6 |  |
| code_palindrome | coding | 3/3 | 147 | 14.9 |  |
| code_reverse_words | coding | 3/3 | 141 | 14.7 |  |
| json_person | structured | 3/3 | 42 | 4.2 |  |
| format_primes | structured | 3/3 | 45 | 4.5 |  |

## mellum2-12b-a2.5b-think-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 204 | 5.9 |  |
| math_multistep | math | 3/3 | 477 | 13.9 |  |
| math_modular | math | 3/3 | 299 | 10.9 |  |
| word_speed | reasoning | 3/3 | 616 | 19.1 |  |
| word_age | reasoning | 3/3 | 596 | 18.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 282 | 9.4 |  |
| logic_negation | reasoning | 3/3 | 643 | 21.5 |  |
| code_fizzbuzz | coding | 3/3 | 503 | 17.6 |  |
| code_palindrome | coding | 3/3 | 531 | 18.0 |  |
| code_reverse_words | coding | 3/3 | 728 | 23.8 |  |
| json_person | structured | 3/3 | 60 | 2.6 |  |
| format_primes | structured | 3/3 | 33 | 1.5 |  |
