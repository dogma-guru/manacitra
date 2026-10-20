# Test 11 day 3: the rule's desk check, run again after the run

`tests/t11-fez-143-day2/desk-check-t11-mantri.py` (SHA-256 `1cff036a2cedb7f82830aaf5cdd2ee77e6d78a5c5d5718526ac0082e4dcb95cb`, the same file day 2 reran) was run unchanged at 2026-10-19T04:19:11Z (UTC), after job 3's counts were fetched: 100 trials per case, its own seed 11390, Python 3.14.8, NumPy 2.5.3, isolated mode, from a scratch directory.

Its output, as printed:

```
R0 0.466; antiphase r 0.135; phase difference of the lines 1.004 pi
1 steady: phase {'QUIET': 100}; weight {'QUIET': 100}; w median within 0.05 of 0.355: 1.00; median phase threshold 0.82 rad = 23.2 kHz; median weight threshold 0.118
2 weight step to 0.15 at 30 and 80: phase {'QUIET': 100}; weight {'SWITCHES WITHIN SPANS': 100}; both weight switches at 30 and 80: 1.00
2b weight step to 0.20 at 30 and 80: phase {'QUIET': 100}; weight {'SWITCHES WITHIN SPANS': 100}; both weight switches at 30 and 80: 0.90
3 weight flip to 0.645 at the boundaries: phase {'SWITCHES AT BOUNDARIES ONLY': 100}; weight {'SWITCHES AT BOUNDARIES ONLY': 100}; boundary switches at 49 and 99: 1.00; each within 0.5 rad of pi: 1.00; middle-span weight within 0.05 of 0.645: 1.00
4 common step 4 kHz at 30 and 80: phase {'QUIET': 100}; weight {'QUIET': 100}
5 common step 40 kHz at 30 and 80: phase {'SWITCHES WITHIN SPANS': 100}; weight {'QUIET': 100}; both phase switches at 30 and 80: 1.00
5c common step 30 kHz at 30 and 80: phase {'SWITCHES WITHIN SPANS': 98, 'QUIET': 2}; weight {'QUIET': 100}; both phase switches at 30 and 80: 0.81
5b common step 12 kHz at 30 and 80: phase {'QUIET': 99, 'SWITCHES WITHIN SPANS': 1}; weight {'QUIET': 100}; both phase switches at 30 and 80: 0.00
6 weight fresh per shot at 0.5: phase {'NOT USABLE': 100}; weight {'NOT USABLE': 100}; median r 0.019
```

| case | rerun on day 3 | day 2's rerun | Mantri (rule) |
|---|---|---|---|
| 1 steady | QUIET 100, WEIGHT QUIET 100; median w within 0.05 of 0.355 in 100; median phase threshold 0.82 rad (23.2 kHz); median weight threshold 0.118 | the same | every required rate at 100 of 100; floor 0.82 rad, 23 kHz; weight floor 0.118 |
| 2 weight to 0.15, within spans | WEIGHT SWITCHES WITHIN SPANS 100; both at the planted repeats 100; phase QUIET 100 | the same | 100 of 100 |
| 2b weight to 0.20 (recorded) | WEIGHT SWITCHES WITHIN SPANS 100; both at the planted repeats 90; phase QUIET 100 | the same (90) | both at the planted repeats 91 |
| 3 weight flip at the boundaries | SWITCHES AT BOUNDARIES ONLY 100 on both channels; at the boundary repeats 100; each within 0.5 rad of a half turn 100; middle span within 0.05 of 0.645 in 100 | the same | 100 of 100 on each |
| 4 common step 4 kHz | QUIET 100 | the same | QUIET 100 |
| 5 common step 40 kHz | SWITCHES WITHIN SPANS 100; both at the planted repeats 100 | the same | 100 of 100 |
| 5c common step 30 kHz (recorded) | SWITCHES WITHIN SPANS 98; both placed 81 | the same (81) | 98; both placed 79 |
| 5b common step 12 kHz (recorded) | QUIET 99 | the same | QUIET 99 |
| 6 weight fresh per shot | NOT USABLE 100; median r 0.019 | the same | NOT USABLE; median r 0.019 |

Every required rate is met. The output is line for line the same as day 2's rerun. The two recorded rates that differ from the rule's figures (90 against 91, 81 against 79) differ as they did on day 2.
