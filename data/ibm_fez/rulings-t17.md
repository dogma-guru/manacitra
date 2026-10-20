# Test 17: the author's rulings, given before anything was built

The runner put four readings to the author after the hash check, because the rule leaves a choice at each. The author ruled on all four in chat at 2026-10-19T14:00:21Z (UTC), after the go and before any circuit was built. No data of this test existed.

1. **Part B's analysis.** The rule says "test 11's monitor analysis and verdicts (its sections 1 to 10 for the monitor jobs)"; test 11's rule numbers 8 analysis steps and test 12's numbers 10. Ruling: reading (a). Test 12's steps 1 to 10 at 1,000 shots, 298 repeats and R0 0.4770, with test 11's phase and weight words and test 12's level word.
2. **Section 9's synthetic sets.** Ruling: this run's own spans as recorded (every Part A job that ran, and Part B); each job's spans held at that job's mean duty; the two lines at this run's observed values in the quadrature of record; generated shot by shot as test 15's desk check generates them, with τ_c 0.2 s; each set read through the same code as the live read (threshold, duty, τ_c, sd, then Z); 2,000 sets, the seed recorded before the check runs.
3. **The middle test, a span that is not SHARED.** Test 15 gives the telegraph sd for SHARED spans only. Ruling: a job with any span that is not SHARED contributes no contrast and is listed.
4. **The note of 19 October** that the rule says is published with the run: `tests/handback/t16-mantri-read-and-scorecard-2026-10-19.md`.

## A ruling given after the go, before any job was submitted

5. **A run that slips past midnight UTC.** At 2026-10-19T16:32:35Z (UTC), no job submitted, ibm_fez's day cycle was still in progress: its T1 stamp of 11:46:20Z had no CZ stamp after it, and test 7's rule allows no submission until 30 minutes after that CZ stamp. The runner asked whether a job submitted after 23:59Z needs a fresh go. The author's ruling: "The original go covers it but it should be recorded that it was a wait for a stamp as the cause." So the go of 19 October covers such a job, and if any job of this test is submitted on 20 October (UTC), the cause on the record is the wait for ibm_fez's CZ stamp.
