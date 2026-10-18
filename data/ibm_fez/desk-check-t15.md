# Test 15: the rule's desk check, run again after the read

`desk-check-t15-mantri.py` was run unchanged after the read, from 02:36:14Z to 02:36:16Z on 18 October 2026 (UTC). It used 400 trials per case and its own seed, 15390, on Python 3.14.8 and NumPy 2.5.3.

- **The script.** SHA-256 `6a00696e62181b927fb6ab04d5055f227d4b2b412927ba5052f2f6f62f418a74`, the same file as `tests/t15-error-model-read/desk-check-t15-mantri.py`.
- **The output.** It is in `desk-check-t15-rerun.log`, beside this file.

| case | required | the rerun | Mantri's rates (rule, section 10) |
|---|---|---|---|
| b 0.344, τ_c 0.17 s | the empirical sd of the span duty within 15 percent of the formula; τ_c recovered within 15 percent | empirical 0.071, formula 0.073, the rule's median sd 0.073; τ_c 0.173 s | empirical 0.071, formula 0.073, median sd 0.073; τ_c 0.173 s |
| b 0.344, τ_c 0.5 s | the same | empirical 0.121, formula 0.125, median sd 0.113; τ_c 0.432 s | empirical 0.121, formula 0.125, median sd 0.113; τ_c 0.432 s |
| b 0.206, τ_c 0.15 s | the same | empirical 0.059, formula 0.058, median sd 0.060; τ_c 0.144 s | empirical 0.059, formula 0.058, median sd 0.060; τ_c 0.144 s |
| b 0.45, τ_c 0.17 s | the same (the duty unfolded) | empirical 0.070, formula 0.076, median sd 0.077; τ_c 0.173 s | empirical 0.070, formula 0.076, median sd 0.077; τ_c 0.173 s |
| boundary, no true change | CHANGE in at most 2 percent | NO CHANGE 95.5, BETWEEN 4.0, CHANGE 0.5 | NO CHANGE 95.5, BETWEEN 4.0, CHANGE 0.5 |
| boundary, a true change of 0.219 | reported | NO CHANGE 59.8, BETWEEN 30.8, CHANGE 9.5 | NO CHANGE 59.8, BETWEEN 30.8, CHANGE 9.5 |
| boundary, a true change of 0.137 | reported | NO CHANGE 74.2, BETWEEN 21.0, CHANGE 4.8 | NO CHANGE 74.2, BETWEEN 21.0, CHANGE 4.8 |

The rerun gives every one of Mantri's rates in the rule's table, to the figures given there.

Read against the requirement column:

- **The empirical sd against the formula** is within 15 percent in every case. The largest gap is 8 percent (0.070 against 0.076).
- **The recovered τ_c** is within 15 percent of the truth in every case. The rule itself names the largest gap, 14 percent at τ_c 0.5 s.
- **CHANGE with no true change** is 0.5 percent, inside the 2 percent the rule allows.
