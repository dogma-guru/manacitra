# Test 19: the author's rulings

Received in chat on 15 November 2026 (UTC), recorded by the runner at 2026-11-15T02:53:43Z. The author states that neither ruling changes the rule's text, a word or a threshold.

1. **Case 5 of section 10.** The published table on each synthetic chip is Kickoff 62's own measured values dealt out to the qubits in a random order. 200 chips, the seed recorded before the case runs. It is a recorded case, changes no word, and does not hold date 1. Mantri's case 5 figures in section 10 were made a different way; they are named as a stand-in and not compared with the runner's.
2. **Dates.** Every date of test 19 is a UTC date. Date 1 is the UTC date of the first go. The 14 days of section 3 are counted in UTC dates from date 1, and the 20 hours between the jobs' submission times. The past-midnight clause stands as written.
3. **Cases 2 and 3.** The runner's choices are accepted as run, both ways reported: on case 2, roles kept from 15 October and dealt at random; on case 3, a published value allowed below 0 and clipped at 0.

## Case 5 seed, recorded before the case runs

Seed: 19015 (NumPy `default_rng`), recorded at 2026-11-15T02:53:43Z.

## Ruling 4, received in chat on 15 November 2026 (UTC), recorded 2026-11-15T03:03:14Z

A go under which no job was built or submitted, because ibm_fez was not accepting jobs, is withdrawn. It sets no date. The runner records the go, the backend's status and the UTC time. Date 1 is the UTC date of the next go under which a job is submitted.

Applied: the go of 15 November 2026 (issue 77) is withdrawn and sets no date. Its record is in stop-t19-d1.md.

## Ruling 5, received in chat on 15 November 2026 (UTC), recorded 2026-11-15T03:04:03Z

Asked: how the cycle clause of test 7's rule reads when the 48 hours hold no stamp at which T1 changed on more than half the qubits. Answer: "No cycle, no bar." With no such stamp in the 48 hours, no cycle is in progress and the clause does not hold the job. Where such a stamp exists, the clause applies as written: no submission from that stamp until 30 minutes after the next stamp at which CZ errors changed on more than half the edges.

Applied in hw_t19.py (window_and_cycle) before any build.
