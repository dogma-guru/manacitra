# Test 13: the rule's desk check, run again after the read

`desk-check-t13-mantri.py` (SHA-256 `f41207c22880ac718bf6a06700622a559ee069edb8cb899e4fdc49045925709a`), unchanged, run at 2026-10-18T01:36:23Z (UTC) after the read: 100 trials per case, its own seed 13390; Python 3.14.8, NumPy 2.5.3. Its output as printed:

```
case 1 independent: ratio median 1.00 [0.85, 1.15]; lag-1 ac median -0.003; scatter ratio median 0.99; (a) {np.str_('INDEPENDENT'): np.int64(100)}; (b) {np.str_('NOT CORRELATED'): np.int64(100)}; 1/e lag median 1 [1, 21]; correlation time read in 0, median nan s (true mean dwell None; sweep 0.029 s)
case 2 interleaved, dwell 1 s: ratio median 40.19 [25.25, 41.43]; lag-1 ac median 0.774; scatter ratio median 0.18; (a) {np.str_('SHARED'): np.int64(100)}; (b) {np.str_('CORRELATED'): np.int64(100)}; 1/e lag median 15 [7, 62]; correlation time read in 100, median 0.433 s (true mean dwell 1.0; sweep 0.029 s)
case 3 interleaved, dwell 20 ms: ratio median 18.20 [16.38, 19.87]; lag-1 ac median 0.033; scatter ratio median 0.51; (a) {np.str_('SHARED'): np.int64(100)}; (b) {np.str_('CORRELATED'): np.int64(18), np.str_('NOT CORRELATED'): np.int64(82)}; 1/e lag median 1 [1, 1]; correlation time read in 0, median nan s (true mean dwell 0.02; sweep 0.029 s)
case 4 interleaved, dwell 100 ms: ratio median 33.58 [31.72, 35.41]; lag-1 ac median 0.441; scatter ratio median 0.24; (a) {np.str_('SHARED'): np.int64(100)}; (b) {np.str_('CORRELATED'): np.int64(100)}; 1/e lag median 2 [2, 3]; correlation time read in 44, median 0.087 s (true mean dwell 0.1; sweep 0.029 s)
```

The rates beside Mantri's are in `report-t13.md`, section 5. Every required rate is met, and the rerun reproduces every rate the rule reports. The CORRELATED and NOT CORRELATED word the script prints for the lag 1 autocorrelation is the script's, not the rule's.
