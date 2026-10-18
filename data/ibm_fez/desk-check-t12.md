# Test 12: the rule's desk check, run again after the run

`desk-check-t12-mantri.py` (SHA-256 `402925b3a370782e56128887f1f150618629585c57277b36e386e73f4066510b`), unchanged, run at 2026-10-18T00:32:37Z (UTC) after the fetch: 100 trials per case, its own seed 12390; Python 3.14.8, NumPy 2.5.3, SciPy 1.18.1. Its output as printed:

```
straddling repeats (1-based): [50, 100] R0 0.4749 antiphase r 0.135
1 steady: phase {'QUIET': 100}; weight {'QUIET': 100}; levels {'AGREE': 100}; w median within 0.05: 1.00; phase floor 1.14 rad = 32 kHz; pair weight floor 0.164; span errors [np.float64(0.0037), np.float64(0.0033), np.float64(0.0054)] repeats [49, 49, 23]
2 weight step to 0.10 at 25 and 75: phase {'QUIET': 100}; weight {'WITHIN': 100}; levels {'SOME': 100}; both weight switches at 25 and 75: 1.00
2b weight step to 0.15 at 25 and 75: phase {'QUIET': 100}; weight {'WITHIN': 100}; levels {'SOME': 100}; both weight switches at 25 and 75: 0.91
3 level steps 0.05 and 0.10 at the boundaries: phase {'QUIET': 100}; weight {'QUIET': 98, 'BOUNDARIES': 2}; levels {'EVERY': 100}
4 weight flip to 0.645 at the boundaries: phase {'BOUNDARIES': 100}; weight {'BOUNDARIES': 100}; levels {'EVERY': 100}; two boundary phase steps each within 0.6 rad of pi: 0.96
5 common step 50 kHz at 25 and 75: phase {'WITHIN': 100}; weight {'WITHIN': 100}; levels {'AGREE': 89, 'SOME': 11}; both phase switches placed: 0.96
5b common step 30 kHz: phase {'QUIET': 39, 'WITHIN': 61}; weight {'QUIET': 100}; levels {'AGREE': 100}; both phase switches placed: 0.13
5c common step 12 kHz: phase {'QUIET': 100}; weight {'QUIET': 100}; levels {'AGREE': 100}; both phase switches placed: 0.00
6 weight fresh per shot at 0.5: phase {'NOT USABLE': 100}; weight {'NOT USABLE': 100}; levels {'NOT USABLE': 100}; median r 0.026
```

The rates beside Mantri's, as the rule's last section reports them, are in `report-t12.md`, section 6. Every required rate is met. Four figures differ from the rule's with the same script and seed: case 1's phase floor (1.14 against 1.13 rad), case 2b's recorded rates (100 against 98, and both placed in 91 against 81), case 4's half turn rate (96 against 97), and case 5's placement (96 against 95).
