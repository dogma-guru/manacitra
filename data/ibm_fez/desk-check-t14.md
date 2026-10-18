# Test 14: the rule's desk check, run again after the run

`desk-check-t14-mantri.py` (SHA-256 `68eb68e66dac98f34d15f349a7dd61b428fba0f34f3897a54893eeecd93800c9`), unchanged, run at 2026-10-18T01:52:38Z (UTC) after the fetch: 100 trials per case, its own seed 14390; Python 3.14.8, NumPy 2.5.3. Its output as printed:

```
case 1 steady: weight {'AGREE': 100}; envelope {'AGREE': 100}; frame {'AGREE': 100}; attribution [((np.str_('NOTHING'), np.str_('NOTHING')), 100)]
   floors: control phase pair 0.30 rad = 4.3 kHz; R0 level se [0.0037 0.0037 0.0055]; w level se [0.005  0.005  0.0074]; R0 median 0.4666 (true 0.4662); r_a 0.148; r_c 0.447
case 2 weight levels 0.06 and 0.14: weight {'EVERY': 100}; envelope {'AGREE': 100}; frame {'AGREE': 100}; attribution [((np.str_('WEIGHT'), np.str_('WEIGHT')), 100)]
case 3 envelope down 15 percent at boundary 2: weight {'AGREE': 100}; envelope {'SOME': 100}; frame {'AGREE': 100}; attribution [((np.str_('NOTHING'), np.str_('ENVELOPE')), 100)]
   fixed-R0 reading calls a weight change at boundary 2 in 1 trials; live-R0 reading in 0
case 3b envelope down 40 percent at boundary 2: weight {'AGREE': 100}; envelope {'SOME': 100}; frame {'AGREE': 100}; attribution [((np.str_('NOTHING'), np.str_('ENVELOPE')), 100)]
   fixed-R0 reading calls a weight change at boundary 2 in 93 trials; live-R0 reading in 0
case 4 frame 10 kHz at boundary 1: weight {'AGREE': 100}; envelope {'AGREE': 100}; frame {'SOME': 100}; attribution [((np.str_('FRAME'), np.str_('NOTHING')), 100)]
case 5 weight 0.14 and frame 10 kHz at boundary 2: weight {'SOME': 100}; envelope {'AGREE': 100}; frame {'SOME': 100}; attribution [((np.str_('NOTHING'), np.str_('MIXED')), 100)]
case 6 midpoint up 0.02 at boundary 2: weight {'AGREE': 100}; envelope {'AGREE': 71, 'SOME': 29}; frame {'AGREE': 100}; attribution [((np.str_('NOTHING'), np.str_('ENVELOPE')), 29), ((np.str_('NOTHING'), np.str_('NOTHING')), 71)]
   fixed-R0 reading calls a weight change at boundary 2 in 4 trials; live-R0 reading in 0
```

| case | required (rule, section 9) | rerun | Mantri (rule, section 9) |
|---|---|---|---|
| 1 steady | AGREE on all three; NOTHING at both boundaries, 100 | 100; NOTHING at both 100; floors 0.30 rad (4.3 kHz), R0 level errors 0.0037, 0.0037, 0.0055, weight level errors 0.005, 0.005, 0.0074; R0 median 0.4666 against 0.4662 | 100; floors as section 5; R0 median 0.4666 against 0.4662 |
| 2 weight levels down 0.06 and 0.14 | weight EVERY; envelope and frame AGREE; WEIGHT at both, at least 95 | 100; 100; 100 | 100; 100; 100 |
| 3 envelope down 15 percent at boundary 2 | envelope SOME; weight AGREE; ENVELOPE at boundary 2, at least 95 | 100; 100; 100; the fixed R0 reading calls a weight change in 1 | 100; 100; 100 |
| 3b envelope down 40 percent at boundary 2 | as case 3; the fixed R0 reading calls a weight change in at least 90 while the live reading calls none | ENVELOPE 100; fixed R0 weight change in **93**, live in 0 | ENVELOPE 100; fixed R0 weight change in **98**, live in 0 |
| 4 frame 10 kHz at boundary 1 | frame SOME; FRAME at boundary 1; NOTHING at boundary 2, at least 95 | 100; 100 | 100; 100 |
| 5 weight down 0.14 and frame 10 kHz at boundary 2 | MIXED at boundary 2, at least 95 | 100 | 100 |
| 6 midpoint up 0.02 at boundary 2 (recorded) | reported | ENVELOPE at boundary 2 in 29, NOTHING in 71; the fixed R0 reading calls a weight change in 4 | ENVELOPE in 29, NOTHING in 71; fixed R0 in 4 |

Every required rate is met in the rerun. One figure differs from the rule's with the same script and seed: case 3b's fixed R0 rate, 93 against 98. The environment Mantri ran is not recorded here.

The run's own analysis (`monitor_t14.py`) was also checked before the run on the same seven cases, with its own seed 14391 (`synth-t14.json`), and met every required rate. That check is not the rule's desk check.
