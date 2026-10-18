# Test 15: the readings put to the author before the go

After the hash check and the fetch, and before any array was opened, the runner put six points to the author in the runner's chat. At each one the rule could not be applied as written. The runner also listed the readings it would take unless the author objected. The author's go followed at 2026-10-18T02:30Z (UTC), with no objection and no separate ruling. The runner applied the proposals as stated below. The rule was not changed; these fix how its words are applied where the rule leaves a choice.

## The six points

1. **The separable kingston qubits (section 4).** These are the qubits with a two-line record in test 8 or test 9:
   - 43: TWO FIXED FREQUENCIES in test 8's jobs 1 and 3;
   - 134: TWO FIXED FREQUENCIES in test 8's job 1;
   - 11 and 95: TWO FIXED FREQUENCIES in test 9's job 1;
   - 120: STEPPED on test 9's scan at two values 72 kHz apart.

   Test 10 gave four of them their own waits: 43 at 46 µs, 11 and 120 at 6 µs, 134 at 12 µs. 95 ran at the common 20 µs and is noted as such. All five are in set S (test 10's jobs 1 and 2), and none is in S′ (job 3).
2. **The qubits not on that list.** Each reads NOT SEPARABLE whatever its ratio, with the ratio reported beside. A job's word reads the listed qubits only.
3. **Spans that are not SHARED.** τ_c is read only on SHARED spans, and the telegraph sd needs it. A boundary with a span that is not SHARED on either side gets no word: it is listed as NOT READ, with its duties shown, and counted in its own column.
4. **Test 8's and test 9's job 1 (section 7).** Per-span weights by A26's method are on the record only for test 7 and test 11's job 1. Test 9's span check gives only blocks of 26 positions and the weights at the positions nearest each boundary. These two rows are marked NOT ON THE RECORD, and nothing new is computed for them.
5. **The mid-sweep fraction (section 6).** The two lines' values are the span's 10th and 90th percentiles of m_j. The middle fifth runs from 0.4 to 0.6 of the way between them. For 143 only, the fraction of sweeps between 0.2 and 0.8 is given beside, for comparison with the figures the rule quotes from test 13. The 10 percent mark of section 4 reads the middle fifth.
6. **Test 14's in-phase duty (section 6).** The rule's threshold comes from each series' own 10th and 90th percentiles, so a series with one level gives a duty near one half by construction. The duty under the rule's threshold is reported with that note, beside the in-phase series' sharing ratio and its percentiles. Nothing is read into "near one".

## The readings listed by the runner

- **The 1/e lag** is searched out to lag 200, as in Mantri's desk check. Test 13 searched to lag 80.
- **The branch of w.** The record's w is the duty of the state on the line at c − R0 g(θ̄), test 13's convention (its p_u). So w corresponds to b when g(θ̄) < 0 and to 1 − b otherwise. Comparisons between 143's jobs are made on that branch. The runner stops and asks if the branch differs between jobs.
- **A job's mean duty** is the mean of its span duties. Its sd is √(Σ sd²) / n.
- **The borrowed τ_c** of section 7 is the median over the spans of the same qubit's nearest monitor job in time. Test 7 and test 11's job 1 borrow from test 11's job 2.
- **Test 14's published level changes** are the live R0 figures, with fixed R0 beside. Its NOT USABLE stays on its rows.
- **Kingston boundaries in the section 5 table.** Test 10 published phases and no weights. The boundaries of the listed qubits enter the table with "none published" in the published column, counted under kingston, apart from fez.
- **Test 9's job 2 (section 7)** is read per qubit of S and per span, on the Y positions and on the X positions separately, with the readout left out and the rows in submitted order. The within-span scatter of the rows' means against binomial is taken per circuit kind (one wait and one quadrature) across the span's whole repeats, then pooled per qubit and span.
- **Test 14's in-phase Y scatter "restated per shot"** is the per-shot sharing ratio of the in-phase Y positions, beside the published 2.00, 1.00 and 2.12.
