# Test 15: the tables

From `fits-t15.json` (computed 2026-10-18T02:34:48Z). Every number is in that file.

## 1. The jobs, the counts check and the words

| job | processor | job id | shots | positions | counts check | whole repeats per span | straddling repeats | the job's word |
|---|---|---|---|---|---|---|---|---|
| test 10, job 1 | ibm_kingston | `db9q7phgv2cc73e5tqb0` | 1000 | 300 | pass (0 position, 0 qubit mismatches) | 49, 50, 49 | none | **MIXED** |
| test 10, job 2 | ibm_kingston | `db9q9i7i0auc73912jrg` | 1000 | 300 | pass (0 position, 0 qubit mismatches) | 49, 50, 49 | none | **MIXED** |
| test 10, job 3 | ibm_kingston | `db9qb0ni0auc73912ljg` | 1000 | 300 | pass (0 position, 0 qubit mismatches) | 49, 50, 49 | none | **NOT SEPARABLE** |
| test 11, job 2 | ibm_fez | `db9t7v424mrc7384ibh0` | 1000 | 300 | pass (0 position, 0 qubit mismatches) | 48, 49, 48 | 49, 50, 100 | **SHARED** |
| test 11, job 3 | ibm_fez | `db9t919gv2cc73e61ljg` | 1000 | 300 | pass (0 position, 0 qubit mismatches) | 49, 49, 48 | 50, 100 | **SHARED** |
| test 12 | ibm_fez | `dba168hgv2cc73e6732g` | 500 | 250 | pass (0 position, 0 qubit mismatches) | 49, 49, 23 | 49, 100 | **SHARED** |
| test 14 | ibm_fez | `dba2c1s24mrc7384pvdg` | 500 | 248 | pass (0 position, 0 qubit mismatches) | 24, 24, 11 | 25, 50 | **SHARED** |
| test 11, job 1 (beside) | | `db9t6ek24mrc7384i83g` | | 260 | pass (0 position, 0 qubit mismatches) | | | no word |
| test 9, job 2 (beside) | | `db9obroc77vs7381pqe0` | | 292 | pass (0 position, 0 qubit mismatches) | | | no word |

## 2. Every separable span

Columns: whole repeats; the quadrature of record; the sharing ratio and its word; the 1/e lag in sweeps; τ_c (a ceiling marked *); the duty b of the high state; the duty on w's branch and the published w (fez); the telegraph sd; the four quarter-span duties; switches; mean dwells high and low (s; † where the mid-sweep fraction is above 10 percent at 1,000 shots); the mid-sweep fraction (middle fifth) and, for 143, the fraction between 0.2 and 0.8.

| job | qubit | span | n | quad | ratio | word | lag | τ_c (s) | b | w duty | published w | sd | quarters | switches | dwells high, low | mid fifth | 0.2 to 0.8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| test 10, job 1 | 11 | 0 | 49 | X | 13.62 | SHARED | 1 | 0.095* | 0.214 |  |  | 0.0318 | 0.192, 0.256, 0.164, 0.244 | 265 | 0.051, 0.187 | 0.071 |  |
| test 10, job 1 | 11 | 1 | 50 | X | 14.76 | SHARED | 1 | 0.095* | 0.209 |  |  | 0.0315 | 0.184, 0.208, 0.240, 0.204 | 272 | 0.049, 0.183 | 0.059 |  |
| test 10, job 1 | 11 | 2 | 49 | X | 14.55 | SHARED | 1 | 0.095* | 0.217 |  |  | 0.0319 | 0.232, 0.228, 0.208, 0.200 | 284 | 0.048, 0.173 | 0.063 |  |
| test 10, job 1 | 43 | 0 | 49 | Y | 1.06 | INDEPENDENT | 6 |  | 0.470 |  |  |  | 0.472, 0.420, 0.412, 0.576 | 465† | 0.064, 0.072† | 0.206 |  |
| test 10, job 1 | 43 | 1 | 50 | Y | 0.98 | INDEPENDENT | 1 |  | 0.497 |  |  |  | 0.432, 0.464, 0.548, 0.544 | 511† | 0.062, 0.062† | 0.221 |  |
| test 10, job 1 | 43 | 2 | 49 | Y | 0.94 | INDEPENDENT | 7 |  | 0.534 |  |  |  | 0.508, 0.548, 0.568, 0.512 | 492† | 0.069, 0.060† | 0.220 |  |
| test 10, job 1 | 95 | 0 | 49 | X | 6.07 | SHARED | 1 | 0.095* | 0.237 |  |  | 0.0329 | 0.228, 0.184, 0.284, 0.252 | 339† | 0.044, 0.142† | 0.149 |  |
| test 10, job 1 | 95 | 1 | 50 | X | 7.60 | SHARED | 1 | 0.095* | 0.196 |  |  | 0.0307 | 0.196, 0.220, 0.176, 0.192 | 273 | 0.045, 0.186 | 0.058 |  |
| test 10, job 1 | 95 | 2 | 49 | X | 6.98 | SHARED | 1 | 0.095* | 0.203 |  |  | 0.0312 | 0.184, 0.180, 0.200, 0.248 | 292 | 0.044, 0.172 | 0.089 |  |
| test 10, job 1 | 120 | 0 | 49 | X | 1.18 | INDEPENDENT | 2 |  | 0.271 |  |  |  | 0.256, 0.288, 0.272, 0.268 | 373† | 0.046, 0.123† | 0.216 |  |
| test 10, job 1 | 120 | 1 | 50 | X | 5.95 | SHARED | 11 | 0.349 | 0.285 |  |  | 0.0670 | 0.164, 0.292, 0.348, 0.336 | 326† | 0.055, 0.138† | 0.156 |  |
| test 10, job 1 | 120 | 2 | 49 | X | 1.33 | INDEPENDENT | 2 |  | 0.369 |  |  |  | 0.360, 0.392, 0.336, 0.388 | 437† | 0.053, 0.091† | 0.366 |  |
| test 10, job 1 | 134 | 0 | 49 | X | 1.05 | INDEPENDENT | 1 |  | 0.432 |  |  |  | 0.428, 0.448, 0.440, 0.412 | 500† | 0.055, 0.072† | 0.174 |  |
| test 10, job 1 | 134 | 1 | 50 | X | 1.02 | INDEPENDENT | 3 |  | 0.326 |  |  |  | 0.328, 0.364, 0.348, 0.264 | 416† | 0.050, 0.102† | 0.164 |  |
| test 10, job 1 | 134 | 2 | 49 | X | 1.01 | INDEPENDENT | 4 |  | 0.461 |  |  |  | 0.440, 0.488, 0.432, 0.484 | 491† | 0.059, 0.069† | 0.184 |  |
| test 10, job 2 | 11 | 0 | 49 | X | 14.97 | SHARED | 1 | 0.095* | 0.216 |  |  | 0.0319 | 0.200, 0.244, 0.204, 0.216 | 283 | 0.048, 0.175 | 0.059 |  |
| test 10, job 2 | 11 | 1 | 50 | X | 13.61 | SHARED | 1 | 0.095* | 0.207 |  |  | 0.0314 | 0.248, 0.172, 0.176, 0.232 | 276 | 0.048, 0.181 | 0.057 |  |
| test 10, job 2 | 11 | 2 | 49 | X | 15.84 | SHARED | 1 | 0.095* | 0.213 |  |  | 0.0317 | 0.200, 0.216, 0.208, 0.228 | 274 | 0.049, 0.181 | 0.075 |  |
| test 10, job 2 | 43 | 0 | 49 | Y | 0.96 | INDEPENDENT | 2 |  | 0.463 |  |  |  | 0.460, 0.500, 0.480, 0.412 | 476† | 0.062, 0.071† | 0.256 |  |
| test 10, job 2 | 43 | 1 | 50 | Y | 0.94 | INDEPENDENT | 1 |  | 0.508 |  |  |  | 0.536, 0.496, 0.460, 0.540 | 503† | 0.064, 0.062† | 0.234 |  |
| test 10, job 2 | 43 | 2 | 49 | Y | 1.02 | INDEPENDENT | 2 |  | 0.506 |  |  |  | 0.496, 0.484, 0.488, 0.556 | 483† | 0.066, 0.065† | 0.213 |  |
| test 10, job 2 | 95 | 0 | 49 | X | 7.50 | SHARED | 1 | 0.095* | 0.214 |  |  | 0.0318 | 0.240, 0.172, 0.200, 0.244 | 313† | 0.043, 0.158† | 0.116 |  |
| test 10, job 2 | 95 | 1 | 50 | X | 7.28 | SHARED | 1 | 0.095* | 0.207 |  |  | 0.0314 | 0.232, 0.188, 0.232, 0.176 | 318 | 0.041, 0.157 | 0.075 |  |
| test 10, job 2 | 95 | 2 | 49 | X | 6.99 | SHARED | 1 | 0.095* | 0.199 |  |  | 0.0309 | 0.196, 0.208, 0.212, 0.180 | 301† | 0.042, 0.168† | 0.112 |  |
| test 10, job 2 | 120 | 0 | 49 | X | 5.37 | SHARED | 11 | 0.348 | 0.299 |  |  | 0.0679 | 0.208, 0.328, 0.384, 0.276 | 376† | 0.050, 0.117† | 0.201 |  |
| test 10, job 2 | 120 | 1 | 50 | X | 9.62 | SHARED | 22 | 0.698 | 0.358 |  |  | 0.1006 | 0.404, 0.272, 0.308, 0.448 | 363† | 0.062, 0.112† | 0.208 |  |
| test 10, job 2 | 120 | 2 | 49 | X | 1.31 | INDEPENDENT | 4 |  | 0.353 |  |  |  | 0.308, 0.400, 0.388, 0.316 | 408† | 0.055, 0.100† | 0.203 |  |
| test 10, job 2 | 134 | 0 | 49 | X | 0.99 | INDEPENDENT | 6 |  | 0.424 |  |  |  | 0.412, 0.400, 0.424, 0.460 | 475† | 0.056, 0.077† | 0.187 |  |
| test 10, job 2 | 134 | 1 | 50 | X | 1.01 | INDEPENDENT | 1 |  | 0.340 |  |  |  | 0.360, 0.292, 0.316, 0.392 | 465† | 0.046, 0.090† | 0.163 |  |
| test 10, job 2 | 134 | 2 | 49 | X | 1.01 | INDEPENDENT | 1 |  | 0.326 |  |  |  | 0.284, 0.364, 0.312, 0.344 | 457† | 0.045, 0.093† | 0.149 |  |
| test 11, job 2 | 143 | 0 | 48 | Y | 23.32 | SHARED | 5 | 0.137 | 0.335 | 0.335 | 0.340 | 0.0472 | 0.264, 0.368, 0.296, 0.412 | 169 | 0.108, 0.215 | 0.080 | 0.257 |
| test 11, job 2 | 143 | 1 | 49 | Y | 24.29 | SHARED | 6 | 0.167 | 0.403 | 0.403 | 0.392 | 0.0537 | 0.440, 0.248, 0.476, 0.448 | 181 | 0.123, 0.182 | 0.078 | 0.284 |
| test 11, job 2 | 143 | 2 | 48 | Y | 21.91 | SHARED | 4 | 0.121 | 0.358 | 0.358 | 0.360 | 0.0429 | 0.464, 0.480, 0.220, 0.268 | 214 | 0.101, 0.179 | 0.094 | 0.308 |
| test 11, job 3 | 143 | 0 | 49 | Y | 27.68 | SHARED | 5 | 0.140 | 0.314 | 0.314 | 0.323 | 0.0464 | 0.272, 0.452, 0.360, 0.172 | 85 | 0.205, 0.448 | 0.020 | 0.102 |
| test 11, job 3 | 143 | 1 | 49 | Y | 29.11 | SHARED | 6 | 0.183 | 0.341 | 0.341 | 0.350 | 0.0519 | 0.400, 0.316, 0.384, 0.264 | 76 | 0.273, 0.515 | 0.017 | 0.081 |
| test 11, job 3 | 143 | 2 | 48 | Y | 25.71 | SHARED | 7 | 0.191 | 0.230 | 0.230 | 0.237 | 0.0498 | 0.180, 0.432, 0.260, 0.048 | 62 | 0.202, 0.656 | 0.011 | 0.068 |
| test 12 | 143 | 0 | 49 | Y | 37.58 | SHARED | 6 | 0.173 | 0.356 | 0.356 | 0.356 | 0.0742 | 0.528, 0.176, 0.312, 0.408 | 30 | 0.321, 0.619 | 0.006 | 0.032 |
| test 12 | 143 | 1 | 49 | Y | 36.43 | SHARED | 5 | 0.175 | 0.344 | 0.344 | 0.343 | 0.0672 | 0.336, 0.280, 0.344, 0.416 | 39 | 0.301, 0.574 | 0.018 | 0.056 |
| test 12 | 143 | 2 | 23 | Y | 16.38 | SHARED | 10 | 0.151 | 0.206 | 0.206 | 0.206 | 0.0809 | 0.032, 0.272, 0.272, 0.248 | 16 | 0.195, 0.667 | 0.002 | 0.024 |
| test 14 | 143 | 0 | 24 | Y | 18.59 | SHARED | 6 | 0.174 | 0.434 | 0.434 | 0.430 | 0.0768 | 0.288, 0.512, 0.544, 0.392 | 40 | 0.314, 0.391 | 0.010 | 0.048 |
| test 14 | 143 | 1 | 24 | Y | 17.90 | SHARED | 6 | 0.174 | 0.368 | 0.368 | 0.365 | 0.0747 | 0.272, 0.432, 0.400, 0.368 | 40 | 0.267, 0.436 | 0.016 | 0.052 |
| test 14 | 143 | 2 | 11 | Y | 8.78 | SHARED | 25 | 0.375 | 0.462 | 0.462 | 0.460 | 0.1577 | 0.480, 0.424, 0.328, 0.616 | 17 | 0.385, 0.448 | 0.002 | 0.038 |

## 3. The table of section 5: every boundary of a monitor job, under the telegraph error

The duties are b of the high state (for 143, b is w's branch in every span). Δ is the later span's duty less the earlier's. ‡ marks a combined sd that includes a span read at the three-sweep ceiling. Published: the record's weight difference and its shot-noise ratio; beside, that difference over the same telegraph sd.

| job | qubit | spans | duties | span words | Δ | combined sd | ratio | word | published Δw | published shot-noise ratio | published Δw over the same sd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| test 10, job 1 | 11 | 0 to 1 | 0.214, 0.209 | SHARED, SHARED | -0.005 | 0.0447‡ | 0.11 | **NO CHANGE** | none published |  |  |
| test 10, job 1 | 11 | 1 to 2 | 0.209, 0.217 | SHARED, SHARED | 0.008 | 0.0448‡ | 0.18 | **NO CHANGE** | none published |  |  |
| test 10, job 1 | 43 | 0 to 1 | 0.470, 0.497 | INDEPENDENT, INDEPENDENT | 0.027 |  |  | **NOT READ** | none published |  |  |
| test 10, job 1 | 43 | 1 to 2 | 0.497, 0.534 | INDEPENDENT, INDEPENDENT | 0.037 |  |  | **NOT READ** | none published |  |  |
| test 10, job 1 | 95 | 0 to 1 | 0.237, 0.196 | SHARED, SHARED | -0.041 | 0.0451‡ | 0.91 | **NO CHANGE** | none published |  |  |
| test 10, job 1 | 95 | 1 to 2 | 0.196, 0.203 | SHARED, SHARED | 0.007 | 0.0438‡ | 0.16 | **NO CHANGE** | none published |  |  |
| test 10, job 1 | 120 | 0 to 1 | 0.271, 0.285 | INDEPENDENT, SHARED | 0.014 |  |  | **NOT READ** | none published |  |  |
| test 10, job 1 | 120 | 1 to 2 | 0.285, 0.369 | SHARED, INDEPENDENT | 0.084 |  |  | **NOT READ** | none published |  |  |
| test 10, job 1 | 134 | 0 to 1 | 0.432, 0.326 | INDEPENDENT, INDEPENDENT | -0.106 |  |  | **NOT READ** | none published |  |  |
| test 10, job 1 | 134 | 1 to 2 | 0.326, 0.461 | INDEPENDENT, INDEPENDENT | 0.135 |  |  | **NOT READ** | none published |  |  |
| test 10, job 2 | 11 | 0 to 1 | 0.216, 0.207 | SHARED, SHARED | -0.009 | 0.0447‡ | 0.20 | **NO CHANGE** | none published |  |  |
| test 10, job 2 | 11 | 1 to 2 | 0.207, 0.213 | SHARED, SHARED | 0.006 | 0.0446‡ | 0.13 | **NO CHANGE** | none published |  |  |
| test 10, job 2 | 43 | 0 to 1 | 0.463, 0.508 | INDEPENDENT, INDEPENDENT | 0.045 |  |  | **NOT READ** | none published |  |  |
| test 10, job 2 | 43 | 1 to 2 | 0.508, 0.506 | INDEPENDENT, INDEPENDENT | -0.002 |  |  | **NOT READ** | none published |  |  |
| test 10, job 2 | 95 | 0 to 1 | 0.214, 0.207 | SHARED, SHARED | -0.007 | 0.0447‡ | 0.16 | **NO CHANGE** | none published |  |  |
| test 10, job 2 | 95 | 1 to 2 | 0.207, 0.199 | SHARED, SHARED | -0.008 | 0.0441‡ | 0.18 | **NO CHANGE** | none published |  |  |
| test 10, job 2 | 120 | 0 to 1 | 0.299, 0.358 | SHARED, SHARED | 0.059 | 0.1213 | 0.49 | **NO CHANGE** | none published |  |  |
| test 10, job 2 | 120 | 1 to 2 | 0.358, 0.353 | SHARED, INDEPENDENT | -0.005 |  |  | **NOT READ** | none published |  |  |
| test 10, job 2 | 134 | 0 to 1 | 0.424, 0.340 | INDEPENDENT, INDEPENDENT | -0.084 |  |  | **NOT READ** | none published |  |  |
| test 10, job 2 | 134 | 1 to 2 | 0.340, 0.326 | INDEPENDENT, INDEPENDENT | -0.014 |  |  | **NOT READ** | none published |  |  |
| test 11, job 2 | 143 | 0 to 1 | 0.335, 0.403 | SHARED, SHARED | 0.068 | 0.0715 | 0.95 | **NO CHANGE** | 0.052 | 15.5 | 0.72, NO CHANGE |
| test 11, job 2 | 143 | 1 to 2 | 0.403, 0.358 | SHARED, SHARED | -0.045 | 0.0687 | 0.65 | **NO CHANGE** | -0.032 | -9.7 | 0.47, NO CHANGE |
| test 11, job 3 | 143 | 0 to 1 | 0.314, 0.341 | SHARED, SHARED | 0.027 | 0.0696 | 0.39 | **NO CHANGE** | 0.027 | 8.3 | 0.39, NO CHANGE |
| test 11, job 3 | 143 | 1 to 2 | 0.341, 0.230 | SHARED, SHARED | -0.111 | 0.0719 | 1.54 | **NO CHANGE** | -0.113 | -35.1 | 1.57, NO CHANGE |
| test 12 | 143 | 0 to 1 | 0.356, 0.344 | SHARED, SHARED | -0.012 | 0.1001 | 0.12 | **NO CHANGE** | -0.013 | -2.7 | 0.13, NO CHANGE |
| test 12 | 143 | 1 to 2 | 0.344, 0.206 | SHARED, SHARED | -0.138 | 0.1051 | 1.31 | **NO CHANGE** | -0.137 | -24.6 | 1.30, NO CHANGE |
| test 14 | 143 | 0 to 1 | 0.434, 0.368 | SHARED, SHARED | -0.066 | 0.1071 | 0.62 | **NO CHANGE** | -0.066 | -9.5 | 0.62, NO CHANGE |
| test 14 | 143 | 1 to 2 | 0.368, 0.462 | SHARED, SHARED | 0.094 | 0.1745 | 0.54 | **NO CHANGE** | 0.096 | 11.0 | 0.55, NO CHANGE |

**The counts of the table**, by processor and job:

| processor | job | CHANGE | BETWEEN | NO CHANGE | NOT READ |
|---|---|---|---|---|---|
| ibm_fez | test 11, job 2 | 0 | 0 | 2 | 0 |
| ibm_fez | test 11, job 3 | 0 | 0 | 2 | 0 |
| ibm_fez | test 12 | 0 | 0 | 2 | 0 |
| ibm_fez | test 14 | 0 | 0 | 2 | 0 |
| ibm_kingston | test 10, job 1 | 0 | 0 | 4 | 6 |
| ibm_kingston | test 10, job 2 | 0 | 0 | 5 | 5 |
| **ibm_kingston** | **all** | **0** | **0** | **9** | **11** |
| **ibm_fez** | **all** | **0** | **0** | **8** | **0** |

## 4. The sensitivity of every boundary word

| job | qubit | spans | ratio | threshold at the 20th to 80th midpoint | τ_c less one sweep | τ_c plus one sweep | word changes |
|---|---|---|---|---|---|---|---|
| test 10, job 1 | 11 | 0 to 1 | 0.11 | 0.88, NO CHANGE | 0.14, NO CHANGE | 0.10, NO CHANGE | none |
| test 10, job 1 | 11 | 1 to 2 | 0.18 | 0.12, NO CHANGE | 0.22, NO CHANGE | 0.15, NO CHANGE | none |
| test 10, job 1 | 95 | 0 to 1 | 0.91 | 0.10, NO CHANGE | 1.11, NO CHANGE | 0.79, NO CHANGE | none |
| test 10, job 1 | 95 | 1 to 2 | 0.16 | 1.81, NO CHANGE | 0.20, NO CHANGE | 0.14, NO CHANGE | none |
| test 10, job 2 | 11 | 0 to 1 | 0.20 | 0.30, NO CHANGE | 0.25, NO CHANGE | 0.17, NO CHANGE | none |
| test 10, job 2 | 11 | 1 to 2 | 0.13 | 0.22, NO CHANGE | 0.16, NO CHANGE | 0.12, NO CHANGE | none |
| test 10, job 2 | 95 | 0 to 1 | 0.16 | 1.36, NO CHANGE | 0.19, NO CHANGE | 0.14, NO CHANGE | none |
| test 10, job 2 | 95 | 1 to 2 | 0.18 | 1.06, NO CHANGE | 0.22, NO CHANGE | 0.16, NO CHANGE | none |
| test 10, job 2 | 120 | 0 to 1 | 0.49 | 1.14, NO CHANGE | 0.50, NO CHANGE | 0.47, NO CHANGE | none |
| test 11, job 2 | 143 | 0 to 1 | 0.95 | 0.81, NO CHANGE | 1.05, NO CHANGE | 0.87, NO CHANGE | none |
| test 11, job 2 | 143 | 1 to 2 | 0.65 | 0.49, NO CHANGE | 0.73, NO CHANGE | 0.60, NO CHANGE | none |
| test 11, job 3 | 143 | 0 to 1 | 0.39 | 0.33, NO CHANGE | 0.43, NO CHANGE | 0.36, NO CHANGE | none |
| test 11, job 3 | 143 | 1 to 2 | 1.54 | 1.50, NO CHANGE | 1.68, NO CHANGE | 1.44, NO CHANGE | none |
| test 12 | 143 | 0 to 1 | 0.12 | 0.14, NO CHANGE | 0.13, NO CHANGE | 0.11, NO CHANGE | none |
| test 12 | 143 | 1 to 2 | 1.31 | 1.31, NO CHANGE | 1.42, NO CHANGE | 1.23, NO CHANGE | none |
| test 14 | 143 | 0 to 1 | 0.62 | 0.58, NO CHANGE | 0.67, NO CHANGE | 0.57, NO CHANGE | none |
| test 14 | 143 | 1 to 2 | 0.54 | 0.54, NO CHANGE | 0.56, NO CHANGE | 0.52, NO CHANGE | none |

## 5. Between 143's monitor jobs, and τ_c by job and stamp

| job | running (UTC) | stamp at submission | span duties on w's branch | job mean | job sd | τ_c per span (s) | median τ_c (s) |
|---|---|---|---|---|---|---|---|
| test 11, job 2 | 2026-10-17T20:01:01Z | 2026-10-17 14:48:16-04:00 | 0.335, 0.403, 0.358 | 0.365 | 0.0278 | 0.137, 0.167, 0.121 | 0.137 |
| test 11, job 3 | 2026-10-17T20:03:18Z | 2026-10-17 14:48:16-04:00 | 0.314, 0.341, 0.230 | 0.295 | 0.0285 | 0.140, 0.183, 0.191 | 0.183 |
| test 12 | 2026-10-18T00:30:27Z | 2026-10-17 20:16:24-04:00 | 0.356, 0.344, 0.206 | 0.302 | 0.0429 | 0.173, 0.175, 0.151 | 0.173 |
| test 14 | 2026-10-18T01:51:04Z | 2026-10-17 20:56:30-04:00 | 0.434, 0.368, 0.462 | 0.421 | 0.0635 | 0.174, 0.174, 0.375 | 0.174 |

| jobs | hours between | stamp between | Δ of the job means | combined sd | ratio | word |
|---|---|---|---|---|---|---|
| test 11, job 2 to test 11, job 3 | 0.04 | same | -0.070 | 0.0398 | 1.77 | **NO CHANGE** |
| test 11, job 3 to test 12 | 4.45 | changed | 0.007 | 0.0515 | 0.14 | **NO CHANGE** |
| test 12 to test 14 | 1.34 | changed | 0.119 | 0.0767 | 1.56 | **NO CHANGE** |

## 6. Test 14's two waits

The antiphase wait (5.6 µs) is the monitor; its rows are in tables 2 and 3. The in-phase wait (11.2 µs): median phase -0.609 rad, quadrature of record X.

| span | n | X ratio | Y ratio (the in-phase Y per shot) | published Y scatter above binomial | X sweep means: 10th, 50th, 90th | X duty, the rule's threshold | Y sweep means: 10th, 50th, 90th | per-row lag 1, X and Y |
|---|---|---|---|---|---|---|---|---|
| 0 | 24 | 1.14 | 1.12 | 2.00 | 0.792, 0.875, 0.958 | 0.386 | 0.125, 0.250, 0.375 | 0.002, 0.004 |
| 1 | 24 | 0.89 | 1.12 | 1.00 | 0.792, 0.875, 0.958 | 0.350 | 0.125, 0.250, 0.375 | -0.011, -0.006 |
| 2 | 11 | 1.01 | 1.00 | 2.12 | 0.727, 0.909, 1.000 | 0.560 | 0.091, 0.273, 0.364 | -0.012, -0.005 |

At the antiphase wait, the other quadrature (X) beside: ratios 2.78, 2.63, 1.74.

## 7. The autocorrelation of m_j at lags 490 to 510 (1,000-shot jobs, separable spans)

Reported, with no word. One lag's standard error under no correlation is about 0.032.

| job | qubit | span | word | at lag 500 | largest absolute value, and its lag | at lag 1 |
|---|---|---|---|---|---|---|
| test 10, job 1 | 11 | 0 | SHARED | +0.001 | 0.046 at 494 | +0.234 |
| test 10, job 1 | 11 | 1 | SHARED | -0.008 | 0.047 at 493 | +0.205 |
| test 10, job 1 | 11 | 2 | SHARED | -0.046 | 0.051 at 492 | +0.192 |
| test 10, job 1 | 43 | 0 | INDEPENDENT | -0.023 | 0.059 at 508 | +0.063 |
| test 10, job 1 | 43 | 1 | INDEPENDENT | -0.015 | 0.056 at 502 | -0.008 |
| test 10, job 1 | 43 | 2 | INDEPENDENT | -0.006 | 0.072 at 498 | +0.017 |
| test 10, job 1 | 95 | 0 | SHARED | -0.035 | 0.063 at 499 | +0.075 |
| test 10, job 1 | 95 | 1 | SHARED | +0.047 | 0.047 at 500 | +0.081 |
| test 10, job 1 | 95 | 2 | SHARED | +0.016 | 0.065 at 508 | +0.115 |
| test 10, job 1 | 120 | 0 | INDEPENDENT | -0.007 | 0.050 at 493 | +0.072 |
| test 10, job 1 | 120 | 1 | SHARED | -0.025 | 0.029 at 502 | +0.812 |
| test 10, job 1 | 120 | 2 | INDEPENDENT | +0.020 | 0.053 at 502 | +0.116 |
| test 10, job 1 | 134 | 0 | INDEPENDENT | -0.002 | 0.056 at 498 | +0.010 |
| test 10, job 1 | 134 | 1 | INDEPENDENT | -0.021 | 0.048 at 492 | +0.023 |
| test 10, job 1 | 134 | 2 | INDEPENDENT | -0.005 | 0.052 at 501 | +0.030 |
| test 10, job 2 | 11 | 0 | SHARED | +0.006 | 0.042 at 497 | +0.194 |
| test 10, job 2 | 11 | 1 | SHARED | -0.036 | 0.036 at 499 | +0.187 |
| test 10, job 2 | 11 | 2 | SHARED | +0.020 | 0.054 at 501 | +0.169 |
| test 10, job 2 | 43 | 0 | INDEPENDENT | -0.011 | 0.035 at 490 | +0.096 |
| test 10, job 2 | 43 | 1 | INDEPENDENT | -0.034 | 0.054 at 499 | -0.036 |
| test 10, job 2 | 43 | 2 | INDEPENDENT | -0.010 | 0.049 at 503 | +0.023 |
| test 10, job 2 | 95 | 0 | SHARED | +0.004 | 0.054 at 501 | +0.100 |
| test 10, job 2 | 95 | 1 | SHARED | +0.001 | 0.035 at 497 | +0.038 |
| test 10, job 2 | 95 | 2 | SHARED | +0.022 | 0.042 at 499 | +0.075 |
| test 10, job 2 | 120 | 0 | SHARED | -0.010 | 0.034 at 491 | +0.790 |
| test 10, job 2 | 120 | 1 | SHARED | -0.033 | 0.040 at 494 | +0.825 |
| test 10, job 2 | 120 | 2 | INDEPENDENT | -0.028 | 0.044 at 510 | +0.162 |
| test 10, job 2 | 134 | 0 | INDEPENDENT | +0.012 | 0.047 at 494 | +0.000 |
| test 10, job 2 | 134 | 1 | INDEPENDENT | +0.049 | 0.049 at 500 | -0.028 |
| test 10, job 2 | 134 | 2 | INDEPENDENT | -0.032 | 0.059 at 495 | -0.064 |
| test 11, job 2 | 143 | 0 | SHARED | +0.034 | 0.113 at 507 | +0.763 |
| test 11, job 2 | 143 | 1 | SHARED | +0.040 | 0.041 at 496 | +0.758 |
| test 11, job 2 | 143 | 2 | SHARED | -0.079 | 0.121 at 503 | +0.690 |
| test 11, job 3 | 143 | 0 | SHARED | -0.049 | 0.097 at 510 | +0.847 |
| test 11, job 3 | 143 | 1 | SHARED | +0.006 | 0.033 at 506 | +0.868 |
| test 11, job 3 | 143 | 2 | SHARED | -0.115 | 0.117 at 499 | +0.865 |

## 8. The kingston qubits not on the list (NOT SEPARABLE; the ratio beside)

| job | qubit spans read | median ratio | 5th to 95th percentile | above 3 | 1.5 to 3 | below 1.5 | the qubits with a span above 3 |
|---|---|---|---|---|---|---|---|
| test 10, job 1 | 189 | 1.061 | 0.962 to 2.933 | 8 | 16 | 165 | 36, 47, 77, 104 |
| test 10, job 2 | 189 | 1.056 | 0.955 to 3.217 | 12 | 14 | 163 | 36, 47, 62, 80, 104 |
| test 10, job 3 | 168 | 1.059 | 0.951 to 2.036 | 5 | 23 | 140 | 29, 34 |

## 9. The beside readings of section 7

**Test 11's job 1 (shuffled)**, per span on the Y and the X positions, no word:

| span | Y rows | Y ratio | Y per-row lag 1 (se) | X rows | X ratio | X per-row lag 1 (se) |
|---|---|---|---|---|---|---|
| 0 | 51 | 1.24 | 0.099 (0.0036) | 49 | 0.98 | 0.097 (0.0037) |
| 1 | 46 | 1.09 | 0.084 (0.0038) | 51 | 0.86 | 0.107 (0.0036) |
| 2 | 31 | 0.99 | 0.110 (0.0046) | 28 | 0.94 | 0.122 (0.0049) |

**Test 9's job 2 (the scan)**, per qubit of S and span. Whole repeats per span: span 0, repeats 1 to 6; span 1, repeats 8 to 12; span 2, repeats 14 to 18.

| over all 67 qubits and 3 spans | median | 5th to 95th percentile | largest |
|---|---|---|---|
| ratio on the Y positions | 1.024 | 0.945 to 1.439 | 3.682 |
| ratio on the X positions | 1.046 | 0.948 to 4.469 | 9.957 |
| within-span scatter of each circuit kind against binomial, pooled | 0.971 | 0.706 to 1.312 | 1.514 |

| qubit | the record | span: Y ratio, X ratio, Y per-row lag 1, within-span scatter |
|---|---|---|
| 11 | listed | 0: 1.07, 4.47, +0.004, 1.18; 1: 1.09, 5.03, +0.004, 1.04; 2: 1.04, 4.23, -0.004, 0.81 |
| 43 | listed; STEPPED | 0: 1.22, 4.69, +0.021, 0.97; 1: 1.47, 6.63, +0.051, 0.93; 2: 1.07, 7.22, +0.061, 0.95 |
| 95 | listed | 0: 1.06, 5.01, +0.006, 0.99; 1: 1.09, 5.73, -0.001, 0.97; 2: 1.09, 4.62, -0.004, 0.90 |
| 120 | listed; STEPPED | 0: 1.05, 0.98, +0.006, 0.95; 1: 1.03, 1.02, +0.011, 1.38; 2: 3.68, 7.94, +0.138, 0.76 |
| 134 | listed; MOVING | 0: 1.70, 9.96, +0.136, 0.74; 1: 1.04, 1.00, +0.004, 1.24; 2: 1.00, 0.96, -0.008, 1.09 |
| 0 | STEPPED | 0: 1.16, 1.08, +0.003, 1.11; 1: 1.17, 1.42, +0.001, 0.81; 2: 1.13, 1.35, +0.003, 0.99 |
| 33 | STEPPED | 0: 1.11, 1.36, -0.010, 1.01; 1: 1.15, 1.34, +0.006, 0.87; 2: 2.76, 2.04, +0.036, 1.05 |
| 62 | STEPPED | 0: 0.99, 1.27, +0.001, 1.15; 1: 1.02, 1.51, +0.010, 0.97; 2: 1.00, 1.33, +0.001, 0.82 |
| 67 | STEPPED | 0: 1.00, 0.99, +0.001, 1.16; 1: 0.94, 1.03, -0.003, 1.03; 2: 1.08, 1.01, +0.004, 0.89 |
| 69 | STEPPED | 0: 0.96, 1.01, -0.002, 0.80; 1: 1.00, 0.98, +0.003, 1.05; 2: 1.04, 1.07, -0.002, 1.36 |
| 89 | STEPPED | 0: 1.05, 1.05, -0.002, 0.79; 1: 1.02, 1.02, +0.001, 1.15; 2: 1.09, 0.98, +0.013, 1.10 |
| 101 | STEPPED | 0: 1.02, 0.98, +0.003, 1.33; 1: 1.07, 1.01, +0.007, 0.90; 2: 1.01, 1.02, -0.010, 1.12 |
| 152 | STEPPED | 0: 0.99, 1.11, -0.006, 0.89; 1: 1.00, 1.14, -0.004, 0.89; 2: 1.08, 0.98, -0.006, 0.83 |
| 36 | MOVING | 0: 1.03, 1.00, +0.005, 1.00; 1: 0.97, 1.02, +0.002, 1.19; 2: 1.04, 1.05, +0.006, 1.14 |
| 132 | MOVING | 0: 1.05, 1.03, +0.007, 1.35; 1: 1.07, 1.00, +0.000, 0.97; 2: 1.01, 0.98, -0.005, 1.29 |
| 155 | MOVING | 0: 2.42, 3.57, +0.042, 1.02; 1: 2.17, 3.30, +0.031, 0.90; 2: 2.14, 3.64, +0.036, 0.86 |

Qubits with a ratio above 3 on the Y or the X positions in any span: 11, 43, 47, 95, 120, 134, 155.

**The shuffled jobs' published weights per span, with the telegraph sd at a borrowed τ_c** of 0.137 s (t11-job2, the median of its spans' tau_c), labelled as borrowed:

| job | spans | published weights | Δ | combined sd (borrowed τ_c) | ratio | word | published shot-noise ratio |
|---|---|---|---|---|---|---|---|
| test 11, job 1 | 0 to 1 | 0.496, 0.433 | -0.063 | 0.0542 | 1.16 | NO CHANGE (borrowed) | -13.2 |
| test 11, job 1 | 1 to 2 | 0.433, 0.448 | 0.015 | 0.0616 | 0.25 | NO CHANGE (borrowed) | 2.6 |
| test 7 | 0 to 1 | 0.457, 0.315 | -0.142 | 0.0535 | 2.65 | BETWEEN (borrowed) | none published |
| test 7 | 1 to 2 | 0.315, 0.274 | -0.041 | 0.0579 | 0.71 | NO CHANGE (borrowed) | none published |
| test 8, job 1 | | NOT ON THE RECORD | | | | | |
| test 9, job 1 | | NOT ON THE RECORD | | | | | |

