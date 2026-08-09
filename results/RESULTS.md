# Benchmark results

Generated: 2026-07-30 06:23 UTC

Each prompt sampled multiple times; cell shows passes/n.
Wall-clock total = sum of all attempt times. tok/s computed only over attempts >=50 tokens.
Fails split as wrong/timeout/empty -- a timeout is too-slow-to-finish, not a wrong answer.

## Summary

| Model | Passes | Fails (wrong/timeout/empty) | Total time | tok/s (gen, long-only) |
|---|---|---|---|---|
| gemma-4-e2b-Q8_0-think | 36/36 | 0/0/0 | 166.0s | 66.7 |
| gemma-4-e2b-Q8_0-nothink | 25/36 | 11/0/0 | 34.5s | 71.2 |
| gemma-4-e4b-Q4_K_M-think | 36/36 | 0/0/0 | 189.9s | 34.4 |
| gemma-4-e4b-Q4_K_M-nothink | 26/36 | 10/0/0 | 43.8s | 36.2 |
| gemma-4-12b-Q4_K_M-think | 36/36 | 0/0/0 | 657.0s | 15.1 |
| gemma-4-12b-Q4_K_M-nothink | 28/36 | 8/0/0 | 69.5s | 14.7 |
| gemma-4-26b-a4b-Q4_K_M-think | 36/36 | 0/0/0 | 303.2s | 33.5 |
| gemma-4-26b-a4b-Q4_K_M-nothink | 35/36 | 1/0/0 | 27.6s | 34.5 |
| gemma-4-31b-qat-Q4_K_XL-think | 36/36 | 0/0/0 | 1016.4s | 7.8 |
| gemma-4-31b-qat-Q4_K_XL-nothink | 35/36 | 1/0/0 | 112.4s | 7.8 |
| qwen3.5-2b-Q8_0-mtp-think | 34/36 | 2/0/0 | 1189.2s | 40.7 |
| qwen3.5-2b-Q8_0-mtp-nothink | 20/36 | 16/0/0 | 25.9s | 46.1 |
| qwen3.5-4b-Q8_0-mtp-think | 35/36 | 1/0/0 | 876.8s | 24.8 |
| qwen3.5-4b-Q8_0-mtp-nothink | 20/36 | 16/0/0 | 27.1s | 28.3 |
| qwen3.5-9b-Q8_0-mtp-think | 36/36 | 0/0/0 | 1418.8s | 15.1 |
| qwen3.5-9b-Q8_0-mtp-nothink | 26/36 | 10/0/0 | 43.9s | 17.2 |
| qwen3.6-27b-Q4_K_M-mtp-think | 30/36 | 0/6/0 | 4005.5s | 5.5 |
| qwen3.6-27b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 139.8s | 5.4 |
| qwen3.6-35b-a3b-Q4_K_M-mtp-think | 35/36 | 0/1/0 | 1386.9s | 20.9 |
| qwen3.6-35b-a3b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 42.1s | 22.5 |
| ornith-1.0-35b-Q4_K_M-mtp-think | 35/36 | 0/1/0 | 1602.4s | 24.0 |
| ornith-1.0-35b-Q4_K_M-mtp-nothink | 30/36 | 6/0/0 | 29.0s | 25.8 |
| ornith-1.0-9b-think-Q8_0 | 36/36 | 0/0/0 | 1382.7s | 9.3 |
| agents-a1-4b-think-Q8_0 | 36/36 | 0/0/0 | 1323.5s | 12.7 |
| ministral-3-8b-Q8_0 | 19/36 | 17/0/0 | 113.7s | 5.8 |
| ministral-3-14b-Q4_K_M | 21/36 | 15/0/0 | 119.4s | 6.0 |
| glm-4.7-flash-Q4_K_M | 36/36 | 0/0/0 | 935.4s | 16.7 |
| lfm2.5-8b-a1b-Q8_0 | 35/36 | 1/0/0 | 192.3s | 30.2 |
| mellum2-12b-a2.5b-think-Q4_K_M | 36/36 | 0/0/0 | 156.2s | 31.3 |
| granite-4.1-8b-Q8_0 | 30/36 | 6/0/0 | 225.4s | 6.6 |
| olmo-3.1-32b-instruct-Q4_K_M | 27/36 | 9/0/0 | 253.1s | 2.4 |

## gemma-4-e2b-Q8_0-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.4 |  |
| math_multistep | math | 3/3 | 677 | 8.7 |  |
| math_modular | math | 3/3 | 363 | 4.5 |  |
| word_speed | reasoning | 3/3 | 1249 | 16.3 |  |
| word_age | reasoning | 3/3 | 773 | 11.3 |  |
| logic_syllogism_no | reasoning | 3/3 | 1043 | 17.8 |  |
| logic_negation | reasoning | 3/3 | 932 | 15.5 |  |
| code_fizzbuzz | coding | 3/3 | 1372 | 20.5 |  |
| code_palindrome | coding | 3/3 | 2154 | 32.3 |  |
| code_reverse_words | coding | 3/3 | 2376 | 37.2 |  |
| json_person | structured | 3/3 | 75 | 1.1 |  |
| format_primes | structured | 3/3 | 33 | 0.6 |  |

## gemma-4-e2b-Q8_0-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.4 |  |
| math_multistep | math | 0/3 | 12 | 0.5 | no number ~=158 |
| math_modular | math | 0/3 | 15 | 0.5 | no number ~=24 |
| word_speed | reasoning | 3/3 | 959 | 13.8 |  |
| word_age | reasoning | 1/3 | 9 | 0.4 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.3 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.3 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 3.3 |  |
| code_palindrome | coding | 3/3 | 534 | 7.6 |  |
| code_reverse_words | coding | 3/3 | 408 | 5.7 |  |
| json_person | structured | 3/3 | 75 | 1.1 |  |
| format_primes | structured | 3/3 | 33 | 0.6 |  |

## gemma-4-e4b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 552 | 15.5 |  |
| math_multistep | math | 3/3 | 544 | 14.5 |  |
| math_modular | math | 3/3 | 713 | 18.5 |  |
| word_speed | reasoning | 3/3 | 809 | 23.2 |  |
| word_age | reasoning | 3/3 | 917 | 26.5 |  |
| logic_syllogism_no | reasoning | 3/3 | 964 | 31.4 |  |
| logic_negation | reasoning | 3/3 | 800 | 25.9 |  |
| code_fizzbuzz | coding | 3/3 | 486 | 13.2 |  |
| code_palindrome | coding | 3/3 | 327 | 9.0 |  |
| code_reverse_words | coding | 3/3 | 293 | 8.7 |  |
| json_person | structured | 3/3 | 73 | 2.2 |  |
| format_primes | structured | 3/3 | 33 | 1.3 |  |

## gemma-4-e4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.7 |  |
| math_multistep | math | 0/3 | 12 | 0.9 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 0.7 |  |
| word_speed | reasoning | 2/3 | 330 | 9.2 | no number ~=2.25 |
| word_age | reasoning | 0/3 | 9 | 0.7 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.6 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.6 |  |
| code_fizzbuzz | coding | 3/3 | 408 | 11.1 |  |
| code_palindrome | coding | 3/3 | 358 | 10.2 |  |
| code_reverse_words | coding | 3/3 | 201 | 5.7 |  |
| json_person | structured | 3/3 | 73 | 2.1 |  |
| format_primes | structured | 3/3 | 33 | 1.3 |  |

## gemma-4-12b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 741 | 46.8 |  |
| math_multistep | math | 3/3 | 820 | 51.6 |  |
| math_modular | math | 3/3 | 776 | 48.5 |  |
| word_speed | reasoning | 3/3 | 882 | 57.4 |  |
| word_age | reasoning | 3/3 | 753 | 48.9 |  |
| logic_syllogism_no | reasoning | 3/3 | 908 | 65.0 |  |
| logic_negation | reasoning | 3/3 | 744 | 50.2 |  |
| code_fizzbuzz | coding | 3/3 | 1411 | 90.5 |  |
| code_palindrome | coding | 3/3 | 1463 | 100.1 |  |
| code_reverse_words | coding | 3/3 | 1280 | 88.9 |  |
| json_person | structured | 3/3 | 75 | 5.4 |  |
| format_primes | structured | 3/3 | 45 | 3.7 |  |

## gemma-4-12b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.4 |  |
| math_multistep | math | 0/3 | 12 | 2.4 | no number ~=158 |
| math_modular | math | 3/3 | 118 | 9.2 |  |
| word_speed | reasoning | 1/3 | 9 | 1.8 | no number ~=2.25 |
| word_age | reasoning | 0/3 | 6 | 1.5 | no number ~=10 |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.6 |  |
| logic_negation | reasoning | 3/3 | 6 | 1.6 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 17.4 |  |
| code_palindrome | coding | 3/3 | 236 | 16.4 |  |
| code_reverse_words | coding | 3/3 | 96 | 7.1 |  |
| json_person | structured | 3/3 | 75 | 5.5 |  |
| format_primes | structured | 3/3 | 45 | 3.6 |  |

## gemma-4-26b-a4b-Q4_K_M-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 1051 | 29.6 |  |
| math_multistep | math | 3/3 | 684 | 18.8 |  |
| math_modular | math | 3/3 | 742 | 21.0 |  |
| word_speed | reasoning | 3/3 | 1124 | 32.4 |  |
| word_age | reasoning | 3/3 | 680 | 20.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 799 | 25.7 |  |
| logic_negation | reasoning | 3/3 | 819 | 26.6 |  |
| code_fizzbuzz | coding | 3/3 | 1463 | 42.9 |  |
| code_palindrome | coding | 3/3 | 1458 | 45.0 |  |
| code_reverse_words | coding | 3/3 | 1189 | 36.8 |  |
| json_person | structured | 3/3 | 75 | 2.5 |  |
| format_primes | structured | 3/3 | 45 | 1.8 |  |

## gemma-4-26b-a4b-Q4_K_M-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.7 |  |
| math_multistep | math | 3/3 | 12 | 0.8 |  |
| math_modular | math | 3/3 | 9 | 0.8 |  |
| word_speed | reasoning | 2/3 | 12 | 1.1 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 0.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 0.9 |  |
| logic_negation | reasoning | 3/3 | 6 | 0.8 |  |
| code_fizzbuzz | coding | 3/3 | 264 | 7.5 |  |
| code_palindrome | coding | 3/3 | 223 | 6.6 |  |
| code_reverse_words | coding | 3/3 | 96 | 3.3 |  |
| json_person | structured | 3/3 | 75 | 2.6 |  |
| format_primes | structured | 3/3 | 45 | 1.8 |  |

## gemma-4-31b-qat-Q4_K_XL-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 497 | 61.9 |  |
| math_multistep | math | 3/3 | 448 | 55.4 |  |
| math_modular | math | 3/3 | 691 | 82.1 |  |
| word_speed | reasoning | 3/3 | 815 | 102.2 |  |
| word_age | reasoning | 3/3 | 614 | 78.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 665 | 91.8 |  |
| logic_negation | reasoning | 3/3 | 657 | 89.4 |  |
| code_fizzbuzz | coding | 3/3 | 1180 | 146.9 |  |
| code_palindrome | coding | 3/3 | 1134 | 144.7 |  |
| code_reverse_words | coding | 3/3 | 1056 | 143.3 |  |
| json_person | structured | 3/3 | 75 | 11.4 |  |
| format_primes | structured | 3/3 | 45 | 8.4 |  |

## gemma-4-31b-qat-Q4_K_XL-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 3.4 |  |
| math_multistep | math | 3/3 | 12 | 3.6 |  |
| math_modular | math | 3/3 | 9 | 3.6 |  |
| word_speed | reasoning | 2/3 | 14 | 4.5 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 3.6 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 3.8 |  |
| logic_negation | reasoning | 3/3 | 6 | 3.6 |  |
| code_fizzbuzz | coding | 3/3 | 242 | 30.5 |  |
| code_palindrome | coding | 3/3 | 177 | 23.4 |  |
| code_reverse_words | coding | 3/3 | 96 | 13.8 |  |
| json_person | structured | 3/3 | 75 | 10.8 |  |
| format_primes | structured | 3/3 | 45 | 7.9 |  |

## qwen3.5-2b-Q8_0-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 858 | 16.7 |  |
| math_multistep | math | 3/3 | 2708 | 58.0 |  |
| math_modular | math | 3/3 | 1437 | 28.3 |  |
| word_speed | reasoning | 3/3 | 9131 | 215.2 |  |
| word_age | reasoning | 3/3 | 1267 | 26.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 3098 | 76.7 |  |
| logic_negation | reasoning | 3/3 | 4293 | 103.3 |  |
| code_fizzbuzz | coding | 2/3 | 6130 | 151.2 | exec error: SyntaxError: 'return' outside function |
| code_palindrome | coding | 2/3 | 7814 | 204.1 | is_palindrome('A man, a plan, a canal: Panama') -> False, want True |
| code_reverse_words | coding | 3/3 | 11602 | 307.7 |  |
| json_person | structured | 3/3 | 48 | 1.0 |  |
| format_primes | structured | 3/3 | 45 | 1.0 |  |

## qwen3.5-2b-Q8_0-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.5 |  |
| math_multistep | math | 0/3 | 10 | 0.4 | no number ~=158 |
| math_modular | math | 0/3 | 11 | 0.4 | no number ~=24 |
| word_speed | reasoning | 1/3 | 142 | 3.4 | no number ~=2.25 |
| word_age | reasoning | 2/3 | 13 | 0.5 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.4 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.3 |  |
| code_fizzbuzz | coding | 1/3 | 354 | 7.6 | fizzbuzz(7) -> '', want '7' |
| code_palindrome | coding | 2/3 | 223 | 4.7 | is_palindrome('A man, a plan, a canal: Panama') -> False, want True |
| code_reverse_words | coding | 2/3 | 256 | 5.7 | reverse_words('  hello   world  ') -> 'world   hello', want 'world hello' |
| json_person | structured | 3/3 | 39 | 1.0 |  |
| format_primes | structured | 3/3 | 45 | 1.0 |  |

## qwen3.5-4b-Q8_0-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 968 | 36.1 |  |
| math_multistep | math | 3/3 | 1316 | 46.0 |  |
| math_modular | math | 3/3 | 1206 | 42.1 |  |
| word_speed | reasoning | 3/3 | 1851 | 68.0 |  |
| word_age | reasoning | 3/3 | 973 | 35.6 |  |
| logic_syllogism_no | reasoning | 3/3 | 1954 | 81.0 |  |
| logic_negation | reasoning | 3/3 | 1251 | 47.9 |  |
| code_fizzbuzz | coding | 3/3 | 2257 | 83.3 |  |
| code_palindrome | coding | 3/3 | 4538 | 199.2 |  |
| code_reverse_words | coding | 2/3 | 5328 | 234.0 | reverse_words('the sky is blue') -> 'the sky is blue', want 'blue is sky the' |
| json_person | structured | 3/3 | 42 | 1.8 |  |
| format_primes | structured | 3/3 | 37 | 1.8 |  |

## qwen3.5-4b-Q8_0-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.7 |  |
| math_multistep | math | 0/3 | 12 | 1.0 | no number ~=158 |
| math_modular | math | 0/3 | 15 | 1.1 | no number ~=24 |
| word_speed | reasoning | 0/3 | 6 | 1.0 | no number ~=2.25 |
| word_age | reasoning | 2/3 | 9 | 0.8 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 0.7 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 0.8 |  |
| code_fizzbuzz | coding | 3/3 | 244 | 8.6 |  |
| code_palindrome | coding | 3/3 | 132 | 5.2 |  |
| code_reverse_words | coding | 0/3 | 84 | 3.5 | reverse_words('the sky is blue') -> 'eulb si yks eht', want 'blue is sky the' |
| json_person | structured | 3/3 | 42 | 1.9 |  |
| format_primes | structured | 3/3 | 41 | 1.8 |  |

## qwen3.5-9b-Q8_0-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 1164 | 70.8 |  |
| math_multistep | math | 3/3 | 1420 | 84.4 |  |
| math_modular | math | 3/3 | 924 | 54.4 |  |
| word_speed | reasoning | 3/3 | 1452 | 87.2 |  |
| word_age | reasoning | 3/3 | 995 | 59.3 |  |
| logic_syllogism_no | reasoning | 3/3 | 3866 | 278.8 |  |
| logic_negation | reasoning | 3/3 | 1303 | 88.2 |  |
| code_fizzbuzz | coding | 3/3 | 4582 | 303.6 |  |
| code_palindrome | coding | 3/3 | 2062 | 134.7 |  |
| code_reverse_words | coding | 3/3 | 3498 | 250.9 |  |
| json_person | structured | 3/3 | 42 | 3.3 |  |
| format_primes | structured | 3/3 | 45 | 3.2 |  |

## qwen3.5-9b-Q8_0-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 1.3 |  |
| math_multistep | math | 0/3 | 12 | 1.8 | no number ~=158 |
| math_modular | math | 0/3 | 12 | 1.7 | no number ~=24 |
| word_speed | reasoning | 0/3 | 6 | 1.4 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 1.2 |  |
| logic_syllogism_no | reasoning | 2/3 | 6 | 1.2 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 1.3 |  |
| code_fizzbuzz | coding | 3/3 | 237 | 13.8 |  |
| code_palindrome | coding | 3/3 | 132 | 8.2 |  |
| code_reverse_words | coding | 3/3 | 83 | 5.4 |  |
| json_person | structured | 3/3 | 42 | 3.3 |  |
| format_primes | structured | 3/3 | 45 | 3.2 |  |

## qwen3.6-27b-Q4_K_M-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 619 | 106.4 |  |
| math_multistep | math | 3/3 | 981 | 168.2 |  |
| math_modular | math | 3/3 | 971 | 168.8 |  |
| word_speed | reasoning | 3/3 | 2006 | 345.4 |  |
| word_age | reasoning | 3/3 | 1488 | 253.4 |  |
| logic_syllogism_no | reasoning | 3/3 | 1852 | 329.8 |  |
| logic_negation | reasoning | 3/3 | 986 | 178.6 |  |
| code_fizzbuzz | coding | 1/3 | 762 | 745.5 | api error: TimeoutError |
| code_palindrome | coding | 0/3 | 0 | 900.0 | api error: TimeoutError |
| code_reverse_words | coding | 2/3 | 2379 | 783.3 | api error: TimeoutError |
| json_person | structured | 3/3 | 54 | 14.5 |  |
| format_primes | structured | 3/3 | 45 | 11.6 |  |

## qwen3.6-27b-Q4_K_M-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 5.1 |  |
| math_multistep | math | 0/3 | 12 | 5.4 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 3.9 |  |
| word_speed | reasoning | 0/3 | 6 | 4.0 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 4.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 4.0 |  |
| logic_negation | reasoning | 3/3 | 6 | 3.9 |  |
| code_fizzbuzz | coding | 3/3 | 258 | 47.9 |  |
| code_palindrome | coding | 3/3 | 130 | 23.7 |  |
| code_reverse_words | coding | 3/3 | 84 | 15.6 |  |
| json_person | structured | 3/3 | 42 | 9.9 |  |
| format_primes | structured | 3/3 | 45 | 12.4 |  |

## qwen3.6-35b-a3b-Q4_K_M-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 808 | 37.7 |  |
| math_multistep | math | 3/3 | 1190 | 53.9 |  |
| math_modular | math | 3/3 | 2552 | 122.4 |  |
| word_speed | reasoning | 3/3 | 1564 | 66.0 |  |
| word_age | reasoning | 3/3 | 762 | 33.7 |  |
| logic_syllogism_no | reasoning | 3/3 | 1042 | 48.9 |  |
| logic_negation | reasoning | 3/3 | 1832 | 79.8 |  |
| code_fizzbuzz | coding | 3/3 | 1796 | 81.6 |  |
| code_palindrome | coding | 3/3 | 9712 | 477.1 |  |
| code_reverse_words | coding | 2/3 | 1356 | 381.1 | api error: TimeoutError |
| json_person | structured | 3/3 | 42 | 2.4 |  |
| format_primes | structured | 3/3 | 45 | 2.4 |  |

## qwen3.6-35b-a3b-Q4_K_M-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.8 |  |
| math_multistep | math | 0/3 | 12 | 1.6 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 1.0 |  |
| word_speed | reasoning | 0/3 | 6 | 1.1 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 1.2 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 1.6 |  |
| logic_negation | reasoning | 3/3 | 6 | 0.9 |  |
| code_fizzbuzz | coding | 3/3 | 258 | 11.5 |  |
| code_palindrome | coding | 3/3 | 132 | 8.6 |  |
| code_reverse_words | coding | 3/3 | 84 | 8.9 |  |
| json_person | structured | 3/3 | 42 | 2.4 |  |
| format_primes | structured | 3/3 | 45 | 2.4 |  |

## ornith-1.0-35b-Q4_K_M-mtp-think

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 940 | 35.0 |  |
| math_multistep | math | 3/3 | 1217 | 46.6 |  |
| math_modular | math | 3/3 | 1457 | 56.0 |  |
| word_speed | reasoning | 3/3 | 2335 | 103.8 |  |
| word_age | reasoning | 3/3 | 842 | 33.0 |  |
| logic_syllogism_no | reasoning | 3/3 | 2189 | 88.5 |  |
| logic_negation | reasoning | 3/3 | 1553 | 62.3 |  |
| code_fizzbuzz | coding | 2/3 | 6821 | 574.6 | api error: TimeoutError |
| code_palindrome | coding | 3/3 | 7657 | 330.0 |  |
| code_reverse_words | coding | 3/3 | 6175 | 268.4 |  |
| json_person | structured | 3/3 | 42 | 2.1 |  |
| format_primes | structured | 3/3 | 45 | 2.0 |  |

## ornith-1.0-35b-Q4_K_M-mtp-nothink

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 0.7 |  |
| math_multistep | math | 0/3 | 12 | 1.1 | no number ~=158 |
| math_modular | math | 3/3 | 9 | 1.0 |  |
| word_speed | reasoning | 0/3 | 6 | 0.9 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 9 | 0.9 |  |
| logic_syllogism_no | reasoning | 3/3 | 6 | 0.9 |  |
| logic_negation | reasoning | 3/3 | 6 | 0.9 |  |
| code_fizzbuzz | coding | 3/3 | 237 | 9.2 |  |
| code_palindrome | coding | 3/3 | 132 | 5.2 |  |
| code_reverse_words | coding | 3/3 | 84 | 4.1 |  |
| json_person | structured | 3/3 | 42 | 2.1 |  |
| format_primes | structured | 3/3 | 45 | 2.1 |  |

## ornith-1.0-9b-think-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 740 | 82.5 |  |
| math_multistep | math | 3/3 | 884 | 111.4 |  |
| math_modular | math | 3/3 | 946 | 111.8 |  |
| word_speed | reasoning | 3/3 | 1408 | 146.1 |  |
| word_age | reasoning | 3/3 | 781 | 78.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 1316 | 132.3 |  |
| logic_negation | reasoning | 3/3 | 915 | 93.1 |  |
| code_fizzbuzz | coding | 3/3 | 2849 | 286.3 |  |
| code_palindrome | coding | 3/3 | 1862 | 190.4 |  |
| code_reverse_words | coding | 3/3 | 1085 | 138.8 |  |
| json_person | structured | 3/3 | 42 | 5.5 |  |
| format_primes | structured | 3/3 | 45 | 5.7 |  |

## agents-a1-4b-think-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 1084 | 75.5 |  |
| math_multistep | math | 3/3 | 1324 | 84.4 |  |
| math_modular | math | 3/3 | 1461 | 93.2 |  |
| word_speed | reasoning | 3/3 | 1434 | 108.1 |  |
| word_age | reasoning | 3/3 | 1164 | 93.1 |  |
| logic_syllogism_no | reasoning | 3/3 | 1235 | 95.0 |  |
| logic_negation | reasoning | 3/3 | 963 | 73.4 |  |
| code_fizzbuzz | coding | 3/3 | 1769 | 138.8 |  |
| code_palindrome | coding | 3/3 | 2760 | 246.5 |  |
| code_reverse_words | coding | 3/3 | 3503 | 306.6 |  |
| json_person | structured | 3/3 | 53 | 5.3 |  |
| format_primes | structured | 3/3 | 33 | 3.5 |  |

## ministral-3-8b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 5.2 |  |
| math_multistep | math | 0/3 | 9 | 1.8 | no number ~=158 |
| math_modular | math | 0/3 | 9 | 1.8 | no number ~=24 |
| word_speed | reasoning | 0/3 | 12 | 2.3 | no number ~=2.25 |
| word_age | reasoning | 1/3 | 9 | 1.9 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 9 | 1.7 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 9 | 1.9 |  |
| code_fizzbuzz | coding | 3/3 | 228 | 39.5 |  |
| code_palindrome | coding | 3/3 | 156 | 26.8 |  |
| code_reverse_words | coding | 0/3 | 69 | 11.8 | reverse_words('the sky is blue') -> 'the sky is blue', want 'blue is sky the' |
| json_person | structured | 3/3 | 66 | 11.4 |  |
| format_primes | structured | 3/3 | 45 | 7.6 |  |

## ministral-3-14b-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 12 | 8.7 |  |
| math_multistep | math | 0/3 | 9 | 2.0 | no number ~=158 |
| math_modular | math | 0/3 | 15 | 2.5 | no number ~=24 |
| word_speed | reasoning | 0/3 | 6 | 1.7 | no number ~=2.25 |
| word_age | reasoning | 0/3 | 9 | 1.8 | no number ~=10 |
| logic_syllogism_no | reasoning | 0/3 | 6 | 1.6 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 9 | 1.6 |  |
| code_fizzbuzz | coding | 3/3 | 235 | 38.9 |  |
| code_palindrome | coding | 3/3 | 156 | 26.3 |  |
| code_reverse_words | coding | 3/3 | 81 | 13.9 |  |
| json_person | structured | 3/3 | 66 | 12.8 |  |
| format_primes | structured | 3/3 | 45 | 7.5 |  |

## glm-4.7-flash-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 538 | 34.3 |  |
| math_multistep | math | 3/3 | 865 | 53.2 |  |
| math_modular | math | 3/3 | 738 | 53.5 |  |
| word_speed | reasoning | 3/3 | 1546 | 102.8 |  |
| word_age | reasoning | 3/3 | 982 | 63.1 |  |
| logic_syllogism_no | reasoning | 3/3 | 2811 | 159.4 |  |
| logic_negation | reasoning | 3/3 | 1335 | 74.9 |  |
| code_fizzbuzz | coding | 3/3 | 1898 | 113.0 |  |
| code_palindrome | coding | 3/3 | 2847 | 165.8 |  |
| code_reverse_words | coding | 3/3 | 1941 | 108.3 |  |
| json_person | structured | 3/3 | 63 | 4.7 |  |
| format_primes | structured | 3/3 | 42 | 2.4 |  |

## lfm2.5-8b-a1b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 295 | 9.5 |  |
| math_multistep | math | 3/3 | 377 | 13.4 |  |
| math_modular | math | 3/3 | 271 | 9.2 |  |
| word_speed | reasoning | 3/3 | 561 | 18.5 |  |
| word_age | reasoning | 3/3 | 611 | 21.2 |  |
| logic_syllogism_no | reasoning | 3/3 | 592 | 20.4 |  |
| logic_negation | reasoning | 3/3 | 420 | 13.0 |  |
| code_fizzbuzz | coding | 3/3 | 777 | 25.9 |  |
| code_palindrome | coding | 3/3 | 627 | 20.0 |  |
| code_reverse_words | coding | 2/3 | 631 | 20.5 | reverse_words('the sky is blue') -> 'the sky is blue', want 'blue is sky the' |
| json_person | structured | 3/3 | 348 | 10.6 |  |
| format_primes | structured | 3/3 | 292 | 10.1 |  |

## mellum2-12b-a2.5b-think-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 221 | 6.3 |  |
| math_multistep | math | 3/3 | 686 | 22.5 |  |
| math_modular | math | 3/3 | 279 | 8.7 |  |
| word_speed | reasoning | 3/3 | 642 | 19.6 |  |
| word_age | reasoning | 3/3 | 650 | 19.8 |  |
| logic_syllogism_no | reasoning | 3/3 | 338 | 10.8 |  |
| logic_negation | reasoning | 3/3 | 494 | 16.4 |  |
| code_fizzbuzz | coding | 3/3 | 417 | 13.2 |  |
| code_palindrome | coding | 3/3 | 477 | 16.7 |  |
| code_reverse_words | coding | 3/3 | 556 | 18.3 |  |
| json_person | structured | 3/3 | 60 | 2.4 |  |
| format_primes | structured | 3/3 | 33 | 1.5 |  |

## granite-4.1-8b-Q8_0

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 6 | 0.7 |  |
| math_multistep | math | 2/3 | 69 | 10.7 | no number ~=158 |
| math_modular | math | 1/3 | 16 | 2.3 | no number ~=24 |
| word_speed | reasoning | 3/3 | 565 | 86.5 |  |
| word_age | reasoning | 3/3 | 280 | 42.6 |  |
| logic_syllogism_no | reasoning | 0/3 | 6 | 1.3 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 1.1 |  |
| code_fizzbuzz | coding | 3/3 | 231 | 33.8 |  |
| code_palindrome | coding | 3/3 | 131 | 20.4 |  |
| code_reverse_words | coding | 3/3 | 84 | 12.7 |  |
| json_person | structured | 3/3 | 55 | 8.5 |  |
| format_primes | structured | 3/3 | 30 | 4.8 |  |

## olmo-3.1-32b-instruct-Q4_K_M

| Prompt | Category | Passes | Tokens (sum) | Time (sum, s) | First fail reason |
|---|---|---|---|---|---|
| math_mul | math | 3/3 | 6 | 9.2 |  |
| math_multistep | math | 0/3 | 6 | 7.7 | no number ~=158 |
| math_modular | math | 3/3 | 6 | 7.1 |  |
| word_speed | reasoning | 0/3 | 10 | 9.5 | no number ~=2.25 |
| word_age | reasoning | 3/3 | 6 | 7.5 |  |
| logic_syllogism_no | reasoning | 0/3 | 6 | 5.9 | first token was 'no', want 'yes' |
| logic_negation | reasoning | 3/3 | 6 | 5.3 |  |
| code_fizzbuzz | coding | 3/3 | 207 | 85.0 |  |
| code_palindrome | coding | 3/3 | 123 | 47.8 |  |
| code_reverse_words | coding | 3/3 | 84 | 35.2 |  |
| json_person | structured | 3/3 | 39 | 18.1 |  |
| format_primes | structured | 3/3 | 30 | 14.9 |  |
