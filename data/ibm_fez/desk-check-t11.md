# Test 11: the rule's desk check, run again after the run

`desk-check-t11-mantri.py` (SHA-256 `1cff036a2cedb7f82830aaf5cdd2ee77e6d78a5c5d5718526ac0082e4dcb95cb`), unchanged, run at 2026-10-17T20:07:12Z (UTC) after job 3's fetch: 100 trials per case, its own seed 11390; Python 3.14.8, NumPy 2.5.3, SciPy 1.18.1. Its output as printed:

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

The rates beside Mantri's, as the rule's last section reports them, are in `report-t11.md`, section 7. Every required rate is met. Two recorded rates differ by one and two trials from the rule's figures: case 2b, 90 against 91; case 5c's placement, 81 against 79.
