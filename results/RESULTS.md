# Benchmark results

Generated: 2026-08-17 04:55 UTC

Each prompt sampled multiple times; cell shows passes/n.
Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.
Fails split as wrong/timeout/empty -- a timeout is too-slow-to-finish, not a wrong answer.

## Summary

| Model | Passes | Fails (wrong/timeout/empty) | Total time | tok/s (gen, long-only) |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 266.6s | 45.0 |
| gemma-4-e2b-Q8_0-nothink | 27/36 | 9/0/0 | 57.4s | 44.8 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 489.3s | 20.4 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 35/36 | 1/0/0 | 44.2s | 21.3 |
| lfm2.5-8b-a1b-Q8_0 | 36/36 | 0/0/0 | 194.8s | 29.8 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 208.2s | 26.9 |
| lfm2.5-2.6b-Q8_0 | 36/36 | 0/0/0 | 631.7s | 17.6 |
| nanbeige4.2-3b-Q8_0-think | 36/36 | 0/0/0 | 1779.0s | 9.8 |
| nanbeige4.2-3b-Q8_0-nothink | 28/36 | 8/0/0 | 191.6s | 10.1 |
| qwen3.8-27b-Q4_K_M-think | 36/36 | 0/0/0 | 967.8s | 3.4 |
| qwen3.8-27b-Q4_K_M-nothink | 30/36 | 6/0/0 | 217.0s | 2.9 |
| nemotron-3.5-lightning-30b-a3b-Q3_K_M | 36/36 | 0/0/0 | 497.6s | 24.4 |
| muse-glimmer-30b-high-Q4_K_XL | 36/36 | 0/0/0 | 2067.5s | 3.7 |
| north-mini-code-1.0-Q4_K_M | 36/36 | 0/0/0 | 300.9s | 16.2 |

## gemma-4-e2b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 281 | 4.1 |  |
| math_multistep | math | 3/3 | 631 | 8.2 |  |
| math_modular | math | 3/3 | 573 | 7.9 |  |
| word_speed | reasoning | 3/3 | 1407 | 20.3 |  |
| word_age | reasoning | 3/3 | 803 | 12.9 |  |
| logic_syllogism_no | reasoning | 3/3 | 1150 | 27.6 |  |
| logic_negation | reasoning | 3/3 | 1118 | 33.1 |  |
| code_fizzbuzz | coding | 3/3 | 1566 | 40.0 |  |
| code_palindrome | coding | 3/3 | 2151 | 50.9 |  |
| code_reverse_words | coding | 3/3 | 2183 | 58.5 |  |
| json_person | structured | 3/3 | 75 | 1.9 |  |
| format_primes | structured | 3/3 | 33 | 1.1 |  |

## gemma-4-e2b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.4 |  |
| math_multistep | math | 0/3 | 12 | 0.8 | no number ~=158 |
| math_modular | math | 0/3 | 15 | 1.7 | no number ~=24 |
| word_speed | reasoning | 3/3 | 1074 | 23.4 |  |
| word_age | reasoning | 3/3 | 9 | 0.6 |  |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.5 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.5 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 5.8 |  |
| code_palindrome | coding | 3/3 | 535 | 12.6 |  |
| code_reverse_words | coding | 3/3 | 375 | 8.3 |  |
| json_person | structured | 3/3 | 75 | 1.7 |  |
| format_primes | structured | 3/3 | 33 | 1.1 |  |

## gemma-4-26b-a4b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 877 | 44.6 |  |
| math_multistep | math | 3/3 | 855 | 43.4 |  |
| math_modular | math | 3/3 | 767 | 33.6 |  |
| word_speed | reasoning | 3/3 | 985 | 47.1 |  |
| word_age | reasoning | 3/3 | 701 | 32.5 |  |
| logic_syllogism_no | reasoning | 3/3 | 657 | 37.2 |  |
| logic_negation | reasoning | 3/3 | 893 | 45.8 |  |
| code_fizzbuzz | coding | 3/3 | 1532 | 70.8 |  |
| code_palindrome | coding | 3/3 | 1476 | 69.7 |  |
| code_reverse_words | coding | 3/3 | 1089 | 57.5 |  |
| json_person | structured | 3/3 | 75 | 4.2 |  |
| format_primes | structured | 3/3 | 45 | 2.8 |  |

## gemma-4-26b-a4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.3 |  |
| math_multistep | math | 3/3 | 12 | 1.9 |  |
| math_modular | math | 3/3 | 9 | 1.2 |  |
| word_speed | reasoning | 2/3 | 12 | 1.7 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 1.3 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.2 |  |
| logic_negation | reasoning | 3/3 | 6 | 1.2 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 12.1 |  |
| code_palindrome | coding | 3/3 | 210 | 10.2 |  |
| code_reverse_words | coding | 3/3 | 96 | 5.1 |  |
| json_person | structured | 3/3 | 75 | 4.3 |  |
| format_primes | structured | 3/3 | 45 | 2.7 |  |

## lfm2.5-8b-a1b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 317 | 11.1 |  |
| math_multistep | math | 3/3 | 392 | 13.6 |  |
| math_modular | math | 3/3 | 296 | 10.4 |  |
| word_speed | reasoning | 3/3 | 549 | 18.2 |  |
| word_age | reasoning | 3/3 | 477 | 15.6 |  |
| logic_syllogism_no | reasoning | 3/3 | 641 | 20.3 |  |
| logic_negation | reasoning | 3/3 | 446 | 13.8 |  |
| code_fizzbuzz | coding | 3/3 | 832 | 27.1 |  |
| code_palindrome | coding | 3/3 | 572 | 18.5 |  |
| code_reverse_words | coding | 3/3 | 623 | 21.1 |  |
| json_person | structured | 3/3 | 381 | 13.8 |  |
| format_primes | structured | 3/3 | 288 | 11.4 |  |

## mellum2-12b-a2.5b-think-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 201 | 8.6 |  |
| math_multistep | math | 3/3 | 973 | 35.5 |  |
| math_modular | math | 3/3 | 224 | 9.0 |  |
| word_speed | reasoning | 3/3 | 625 | 21.5 |  |
| word_age | reasoning | 3/3 | 501 | 16.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 504 | 21.0 |  |
| logic_negation | reasoning | 3/3 | 211 | 9.6 |  |
| code_fizzbuzz | coding | 3/3 | 1061 | 40.0 |  |
| code_palindrome | coding | 3/3 | 535 | 19.2 |  |
| code_reverse_words | coding | 3/3 | 653 | 22.8 |  |
| json_person | structured | 3/3 | 60 | 2.5 |  |
| format_primes | structured | 3/3 | 33 | 1.6 |  |

## lfm2.5-2.6b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 343 | 17.6 |  |
| math_multistep | math | 3/3 | 443 | 24.4 |  |
| math_modular | math | 3/3 | 501 | 27.9 |  |
| word_speed | reasoning | 3/3 | 1102 | 73.4 |  |
| word_age | reasoning | 3/3 | 946 | 59.6 |  |
| logic_syllogism_no | reasoning | 3/3 | 985 | 58.7 |  |
| logic_negation | reasoning | 3/3 | 797 | 41.9 |  |
| code_fizzbuzz | coding | 3/3 | 2231 | 119.1 |  |
| code_palindrome | coding | 3/3 | 1079 | 59.9 |  |
| code_reverse_words | coding | 3/3 | 1280 | 71.5 |  |
| json_person | structured | 3/3 | 527 | 29.5 |  |
| format_primes | structured | 3/3 | 893 | 48.1 |  |

## nanbeige4.2-3b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 735 | 96.3 |  |
| math_multistep | math | 3/3 | 619 | 76.7 |  |
| math_modular | math | 3/3 | 798 | 81.6 |  |
| word_speed | reasoning | 3/3 | 2151 | 213.1 |  |
| word_age | reasoning | 3/3 | 723 | 69.1 |  |
| logic_syllogism_no | reasoning | 3/3 | 3073 | 301.1 |  |
| logic_negation | reasoning | 3/3 | 1287 | 125.3 |  |
| code_fizzbuzz | coding | 3/3 | 2136 | 215.8 |  |
| code_palindrome | coding | 3/3 | 3032 | 301.5 |  |
| code_reverse_words | coding | 3/3 | 2871 | 289.8 |  |
| json_person | structured | 3/3 | 42 | 4.2 |  |
| format_primes | structured | 3/3 | 45 | 4.6 |  |

## nanbeige4.2-3b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.0 |  |
| math_multistep | math | 0/3 | 12 | 2.0 | no number ~=158 |
| math_modular | math | 2/3 | 733 | 74.4 | no number ~=24 |
| word_speed | reasoning | 3/3 | 383 | 37.4 |  |
| word_age | reasoning | 2/3 | 167 | 17.3 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 7 | 1.0 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.8 |  |
| code_fizzbuzz | coding | 3/3 | 252 | 23.4 |  |
| code_palindrome | coding | 3/3 | 146 | 13.5 |  |
| code_reverse_words | coding | 3/3 | 141 | 12.6 |  |
| json_person | structured | 3/3 | 42 | 4.0 |  |
| format_primes | structured | 3/3 | 45 | 4.1 |  |

## qwen3.8-27b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 151 | 38.1 |  |
| math_multistep | math | 3/3 | 180 | 48.0 |  |
| math_modular | math | 3/3 | 156 | 42.6 |  |
| word_speed | reasoning | 3/3 | 257 | 69.8 |  |
| word_age | reasoning | 3/3 | 174 | 51.3 |  |
| logic_syllogism_no | reasoning | 3/3 | 249 | 73.8 |  |
| logic_negation | reasoning | 3/3 | 241 | 72.7 |  |
| code_fizzbuzz | coding | 3/3 | 726 | 209.7 |  |
| code_palindrome | coding | 3/3 | 638 | 178.0 |  |
| code_reverse_words | coding | 3/3 | 427 | 143.7 |  |
| json_person | structured | 3/3 | 54 | 20.9 |  |
| format_primes | structured | 3/3 | 45 | 19.4 |  |

## qwen3.8-27b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 6.4 |  |
| math_multistep | math | 0/3 | 12 | 6.7 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 5.5 |  |
| word_speed | reasoning | 0/3 | 6 | 4.5 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 5.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 4.4 |  |
| logic_negation | reasoning | 3/3 | 6 | 4.5 |  |
| code_fizzbuzz | coding | 3/3 | 244 | 83.0 |  |
| code_palindrome | coding | 3/3 | 130 | 39.7 |  |
| code_reverse_words | coding | 3/3 | 83 | 25.2 |  |
| json_person | structured | 3/3 | 54 | 17.3 |  |
| format_primes | structured | 3/3 | 45 | 14.4 |  |

## nemotron-3.5-lightning-30b-a3b-Q3_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 712 | 26.5 |  |
| math_multistep | math | 3/3 | 745 | 27.4 |  |
| math_modular | math | 3/3 | 663 | 22.7 |  |
| word_speed | reasoning | 3/3 | 1229 | 46.3 |  |
| word_age | reasoning | 3/3 | 891 | 30.1 |  |
| logic_syllogism_no | reasoning | 3/3 | 1537 | 68.4 |  |
| logic_negation | reasoning | 3/3 | 1281 | 60.5 |  |
| code_fizzbuzz | coding | 3/3 | 1440 | 58.0 |  |
| code_palindrome | coding | 3/3 | 2049 | 90.5 |  |
| code_reverse_words | coding | 3/3 | 1470 | 61.8 |  |
| json_person | structured | 3/3 | 54 | 3.0 |  |
| format_primes | structured | 3/3 | 37 | 2.4 |  |

## muse-glimmer-30b-high-Q4_K_XL

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 267 | 69.5 |  |
| math_multistep | math | 3/3 | 301 | 73.2 |  |
| math_modular | math | 3/3 | 304 | 69.7 |  |
| word_speed | reasoning | 3/3 | 1002 | 219.9 |  |
| word_age | reasoning | 3/3 | 563 | 139.5 |  |
| logic_syllogism_no | reasoning | 3/3 | 1111 | 470.2 |  |
| logic_negation | reasoning | 3/3 | 471 | 147.4 |  |
| code_fizzbuzz | coding | 3/3 | 1276 | 271.7 |  |
| code_palindrome | coding | 3/3 | 885 | 199.6 |  |
| code_reverse_words | coding | 3/3 | 930 | 309.6 |  |
| json_person | structured | 3/3 | 302 | 49.9 |  |
| format_primes | structured | 3/3 | 251 | 47.3 |  |

## north-mini-code-1.0-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 224 | 13.2 |  |
| math_multistep | math | 3/3 | 192 | 13.1 |  |
| math_modular | math | 3/3 | 187 | 13.6 |  |
| word_speed | reasoning | 3/3 | 394 | 25.9 |  |
| word_age | reasoning | 3/3 | 227 | 16.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 239 | 15.1 |  |
| logic_negation | reasoning | 3/3 | 346 | 19.5 |  |
| code_fizzbuzz | coding | 3/3 | 600 | 34.6 |  |
| code_palindrome | coding | 3/3 | 944 | 54.6 |  |
| code_reverse_words | coding | 3/3 | 972 | 61.0 |  |
| json_person | structured | 3/3 | 291 | 17.4 |  |
| format_primes | structured | 3/3 | 251 | 16.8 |  |
