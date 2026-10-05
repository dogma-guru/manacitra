# Changelog

## 0.1.0 (unreleased)

The first version.

- The core: the two test circuits with exact three-CZ synthesis and their ideal values; the kept share and its shot
  noise; the statistics; the map rule, the payoff rule and the persistence rule (with Amendment A1 and the original
  rule beside it); disjoint pairs, rounds of disjoint pairs, pair choice; the random stand-in workload.
- Backends: a simulator (Qiskit Aer or numpy, always available) and IBM Quantum (Qiskit Runtime), with the submit-once
  guard, the usage read and the time cap. Experimental: Open Quantum, and a Cirq simulation of a published noise model.
- The dataset: the counts and analyses of the runs on ibm_fez and ibm_kingston (5 October 2026) and of the simulated
  control, with a test that reproduces every archived statistic.
- The README, the long-form documentation, four diagrams and three examples.
