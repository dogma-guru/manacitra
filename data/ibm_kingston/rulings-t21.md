# Test 21: the author's rulings

Recorded by the runner at 2026-11-17T02:18:45Z, as given in chat, before any job was built. The text is the author's, verbatim.

> Rulings on test 21, 17 November 2026 (UTC). None changes the rule’s text, a word or a threshold.
>
> 1. Usable in job 1: both conditions. Section 3 replaces the readout half of test 9’s test (job 1’s own readout circuits, at or below 0.03). Section 4 imports test 9’s analysis whole, so the amplitude half stands: the larger of the S and P fits’ amplitudes at least 0.2. A qubit failing either is reported with its numbers and gets no word from the scan.
> 2. The queue and midnight: the clause stands as written. If the queue carries a job’s submission past 23:59 UTC of the go’s date, stop as scripted. The remaining jobs run under a second go naming the new UTC date, the same issue and the seal. The first go’s jobs stand, and the gap is reported from the execution records.
> 3. The two readings for a monitor in more than one span are taken: the quadrature of record chosen once per qubit and job on every whole repeat with every shot; the permutation null from seed 21401 afresh for each qubit and each span read.

## How each is applied

1. `analyse_t21_job1.py` reads a qubit as usable in job 1 only if both of these hold:
   - the readout error from job 1's own four readout circuits is at or below 0.03;
   - the larger of S's and P's fitted A is at least 0.2.

   A qubit failing either gets no word from the scan and is reported with its numbers. This changes the runner's earlier reading, in which the amplitude was reported beside and not used.
2. `hw_t21.py --submitN` refuses a submission on a UTC date other than the go's. It records the refusal in `late-t21-jobN.json` and stops. Any job not yet submitted then waits for a second go naming the new UTC date, issue 79 and the seal. The jobs already submitted stand. The gap between jobs is reported from the execution records.
3. These are the readings `read_t21.py` and `read_core_t21.py` already use, unchanged:
   - the quadrature of record is chosen once per qubit and job, on every repeat's rows with every shot;
   - `read_span` starts a fresh `default_rng(21401)` for each qubit's span read.

## Ruling 4, given after the hand-back

Recorded by the runner at 2026-11-17T13:57:24Z, as given in chat after the hand-back was written and after the data were seen. The text is the author's, verbatim.

> Ruling 4 on test 21, 17 November 2026 (UTC), given after the hand-back and after the data were seen. It changes none of the rule’s text, no word and no threshold.
>
> 4. Section 6 item 2 does not cover qubit 11. The item applies where job 1 returns TWO FIXED FREQUENCIES for a qubit. Under section 3 and ruling 1, a qubit that is not usable in job 1 gets no word from the scan, and its verdict under test 9’s analysis is NOT USABLE. So job 1 does not return TWO FIXED FREQUENCIES for qubit 11; the table reading is one of its reported numbers. The positions are not computed in the hand-back. `analyse_t21_job1.py`, written before the run, already reads the item this way, and it stands.
>
> Record this as ruling 4 in `rulings-t21.md` with its UTC time, marked as given after the hand-back. Add one line to the report’s section 6 item 2 citing it. Regenerate `SHA256SUMS`. Change nothing else. The fits and the arrays stay in the hand-back as they are, so the positions remain computable by anyone later, as a reading outside the rule.

### How it is applied

No script was changed or rerun. The report's section 6 item 2 gains one line citing this ruling, and `SHA256SUMS` is regenerated. The fits and the arrays are unchanged.
