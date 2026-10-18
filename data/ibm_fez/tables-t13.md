# Test 13: tables from fits-t13.json

## The words and ratios per span (the quadrature of record, Y)

| job | span | whole repeats | ratio (a) | word | 1/e lag (sweeps) | sweep | correlation time | per row lag 1 autocorrelation (se) |
|---|---|---|---|---|---|---|---|---|
| test 11, job 2 | 0 | 48 | 23.32 | **SHARED** | 5 | 27.5 ms | 0.137 s (5 sweeps) | 0.365 (0.0046) |
| test 11, job 2 | 1 | 49 | 24.29 | **SHARED** | 6 | 27.8 ms | 0.167 s (6 sweeps) | 0.367 (0.0045) |
| test 11, job 2 | 2 | 48 | 21.91 | **SHARED** | 4 | 30.2 ms | 0.121 s (4 sweeps) | 0.302 (0.0046) |
| test 11, job 3 | 0 | 49 | 27.68 | **SHARED** | 5 | 28.1 ms | 0.140 s (5 sweeps) | 0.475 (0.0045) |
| test 11, job 3 | 1 | 49 | 29.11 | **SHARED** | 6 | 30.5 ms | 0.183 s (6 sweeps) | 0.512 (0.0045) |
| test 11, job 3 | 2 | 48 | 25.71 | **SHARED** | 7 | 27.3 ms | 0.191 s (7 sweeps) | 0.460 (0.0046) |
| test 12 | 0 | 49 | 37.58 | **SHARED** | 6 | 28.8 ms | 0.173 s (6 sweeps) | 0.683 (0.0064) |
| test 12 | 1 | 49 | 36.43 | **SHARED** | 5 | 35.0 ms | 0.175 s (5 sweeps) | 0.649 (0.0064) |
| test 12 | 2 | 23 | 16.38 | **SHARED** | 10 | 15.1 ms | 0.151 s (10 sweeps) | 0.643 (0.0093) |

## The X quadrature, beside, without words

| job | span | ratio (a) | 1/e lag (sweeps) | per row lag 1 autocorrelation (se) |
|---|---|---|---|---|
| test 11, job 2 | 0 | 8.31 | 5 | 0.120 (0.0046) |
| test 11, job 2 | 1 | 8.46 | 6 | 0.118 (0.0045) |
| test 11, job 2 | 2 | 7.39 | 4 | 0.084 (0.0046) |
| test 11, job 3 | 0 | 11.22 | 5 | 0.185 (0.0045) |
| test 11, job 3 | 1 | 10.14 | 6 | 0.165 (0.0045) |
| test 11, job 3 | 2 | 9.22 | 7 | 0.145 (0.0046) |
| test 12 | 0 | 4.53 | 6 | 0.066 (0.0064) |
| test 12 | 1 | 4.81 | 5 | 0.077 (0.0064) |
| test 12 | 2 | 2.11 | 13 | 0.042 (0.0093) |

## The scatter check (c), with the shared state prediction beside

| job | span | Y from the arrays | Y from the counts | Y predicted if shared | X from the arrays | X from the counts | X predicted if shared | b | p_l, p_u in Y |
|---|---|---|---|---|---|---|---|---|---|
| test 11, job 2 | 0 | 0.485 | 0.485 | 0.300 | 0.998 | 0.998 | 0.833 | 0.340 | 0.073, 0.921 |
| test 11, job 2 | 1 | 0.444 | 0.444 | 0.291 | 0.770 | 0.770 | 0.822 | 0.392 | 0.074, 0.921 |
| test 11, job 2 | 2 | 0.448 | 0.448 | 0.303 | 0.567 | 0.567 | 0.822 | 0.360 | 0.075, 0.919 |
| test 11, job 3 | 0 | 0.470 | 0.470 | 0.326 | 0.562 | 0.562 | 0.817 | 0.323 | 0.077, 0.914 |
| test 11, job 3 | 1 | 0.369 | 0.369 | 0.321 | 0.888 | 0.888 | 0.808 | 0.350 | 0.078, 0.913 |
| test 11, job 3 | 2 | 0.401 | 0.401 | 0.392 | 0.662 | 0.662 | 0.825 | 0.237 | 0.084, 0.907 |
| test 12 | 0 | 0.224 | 0.224 | 0.151 | 0.748 | 0.748 | 0.959 | 0.356 | 0.035, 0.960 |
| test 12 | 1 | 0.185 | 0.185 | 0.169 | 1.168 | 1.168 | 0.945 | 0.343 | 0.039, 0.956 |
| test 12 | 2 | 0.322 | 0.322 | 0.241 | 0.950 | 0.950 | 0.947 | 0.206 | 0.044, 0.951 |

## Job 1 (test 11's shuffled job), beside, without words

| span | Y rows | Y ratio (a) | Y per row lag 1 (se) | X rows | X ratio (a) | X per row lag 1 (se) |
|---|---|---|---|---|---|---|
| 0 | 51 | 1.24 | 0.099 (0.0036) | 49 | 0.98 | 0.097 (0.0037) |
| 1 | 46 | 1.09 | 0.084 (0.0038) | 51 | 0.86 | 0.107 (0.0036) |
| 2 | 31 | 0.99 | 0.110 (0.0046) | 28 | 0.94 | 0.122 (0.0049) |
