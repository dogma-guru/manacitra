# Kickoff 61: the rule, fixed before the run

Written 15 October 2026, before the job was built or submitted. Author: Anish Patel. This file states the design, the analysis and the verdict rule for Kickoff 61. Its SHA-256 is posted publicly before the run, and the file is published unchanged after it.

## The question

After a maintenance on 14 to 15 October 2026, ibm_fez's published readout errors changed: at the stamp of 13:39 UTC on 15 October, 134 of its 156 qubits publish a readout error above 3%, where on 14 October nearly all were below it. Between the maintenance and that stamp, the published values on some qubits alternated between their earlier levels and values of 0.25 to 0.50 from one stamp to the next.

On eighteen fez qubits, does the readout error measured directly agree with the readout error published at the time of the run?

## The qubits

Fixed here, not drawn: the eighteen qubits of the six chains of Kickoff 54, each chain written L1-M-L3:

- 31-30-29, 75-74-73, 120-121-116, 96-103-104 (Kickoff 53's chains);
- 143-144-145, 144-143-142.

Their waiting qubits M are 30, 74, 121, 103, 144 and 143.

## The run

- **Processor:** ibm_fez, one job.
- **The circuits:**
  - **A, all together, prepared in |0⟩:** measure all eighteen qubits, with no gate. Gives P(1|0) per qubit, measured together.
  - **B, all together, prepared in |1⟩:** X on each of the eighteen, then measure all. Gives P(0|1) per qubit, measured together.
  - **Per waiting qubit M, alone (six M, three circuits each):** measure M with no gate; X on M, then measure; and the zero-wait baseline used since Kickoff 50 (H, no wait, H, measure on M). Gives P(1|0), P(0|1) and the baseline P(1) with no other qubit measured.
- **Shots:** 20 circuits, each run as 2 copies of 2,000 shots. Interleaving seed 6101.
- **Settings:** dynamical decoupling, gate twirling and measurement twirling all off. No readout error mitigation.
- **When:** not while the day's calibration cycle is in progress, from a stamp at which T1 changed on more than half the qubits until 30 minutes after the next stamp at which CZ errors changed on more than half the edges. The stamp in force at submission is recorded, with the published readout error, P(1|0) and P(0|1) of each of the eighteen qubits at it.

## The analysis

- **Measured readout error** per qubit: e = (P(1|0) + P(0|1)) / 2, from circuits A and B with the copies pooled, the same average IBM's published `readout_error` is defined as.
- **Published readout error** per qubit: the value at the stamp in force when the job ran (at submission; if a new stamp appears before the job finishes, both are recorded and the comparison is made against each).
- **Intervals:** 90% intervals on e from one bootstrap over shots and copies, seed 61, 10,000 draws.

## The verdict

Per qubit, comparing the measured e (its interval) with the published value p:

| verdict | condition |
|---|---|
| **CONSISTENT** | e's interval contains a value within the larger of 0.02 and p/2 of p |
| **INCONSISTENT** | otherwise |

**H61, for the chip as published:** PUBLISHED READABLE if every qubit is CONSISTENT; PUBLISHED NOT READABLE if six or more of the eighteen are INCONSISTENT; MIXED otherwise.

**Beside the verdict, not used in it:**

1. **The measured readout of Kickoff 54's chains:** whether every one of the eighteen qubits has measured e below 0.05.
2. **Alone against together:** for each M, P(1|0) and P(0|1) alone beside the values from A and B.
3. **The zero-wait baseline** per M, and whether any exceeds 0.1.
4. **The calibration record:** the stamp at build, at submission, every 5 minutes until the job finishes, and after the fetch; for each new stamp, which published values changed; the job's status changes with their times; and the published readout error of the eighteen qubits at every stamp read.

The rule is not changed after the data, whatever they show.
