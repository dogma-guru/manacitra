# Changelog

## 0.1.0 (unreleased)

The first version.

- The core: the two test circuits with exact three-CZ synthesis and their ideal values; the kept share and its shot
  noise; the statistics; the map rule, the payoff rule and the persistence rule (with Amendment A1 and the original
  rule beside it); disjoint pairs, rounds of disjoint pairs, pair choice; the random stand-in workload.
- Backends: a simulator (Qiskit Aer or numpy, always available) and IBM Quantum (Qiskit Runtime), with the submit-once
  guard, the usage read and the time cap. Experimental: Open Quantum, and a Cirq simulation of a published noise model.
- The dataset: the counts and analyses of the runs on ibm_fez and ibm_kingston (5 October 2026), of the run on Rigetti
  Cepheus-1-108Q through Open Quantum (Kickoff 34b, the same day; Amendment A2) and of the simulated control, with a
  test that reproduces every archived statistic.
- Pinned circuits: every circuit the package runs ships as an exact gate list, so every platform runs the same
  gate sequences (`src/manacitra/pinned_circuits.json`, `tools/pin_circuits.py`).
- Sealing: `manacitra seal | reveal | verify`, salted SHA-256 commitments. Signing: a gated CI workflow that signs
  commit records, data files and release artifacts with Sigstore's keyless signing (off until `MANACITRA_SIGN` is
  `true`). `data/SHA256SUMS` for catching corrupted files.
- Safety (Amendment A3): every spending submission goes through the submit-once guard; Open Quantum checks the
  balance, the quote and the budget across waves again immediately before sending, and keeps credit reservations in
  the ledger. The dataset is found from a clone, `MANACITRA_DATA` or `--data`, with a clear stop when it is missing.
- The README, the long-form documentation, six diagrams and three examples. The README explains how the results were
  made: kickoffs (Amendment A2).
- Ownership (Kickoff 01, Amendment A1): copyright Dogma LLC (doing business as Dogma Guru), developed by Anish Patel.
  Contributions under Apache 2.0, inbound as outbound, with a Developer Certificate of Origin sign-off checked in CI.
  The full CC BY 4.0 legal code in `data/LICENSE` and `docs/LICENSE`.
