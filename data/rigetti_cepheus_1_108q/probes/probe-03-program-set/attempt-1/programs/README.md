# Programs

`template-E1.qasm` and `template-E2.qasm` are the two executables of section 3 of the rule, written before the go.

* E1 is probe 02's B1 template unchanged (its SHA-256 equals probe 02's `template-B1.qasm`,
  36d5d95c4dbb41fff5370a5c3c4ee6ef961b3a48b52d25b8b6c41510f5253e21): `rx(pi)` in a verbatim box, one play of d on the
  drive frame, a barrier across the drive and the two readout frames, measure.
* E2 is E1 with a second `play(<DRIVE_FRAME>, wait_d);` before the barrier, in the same `cal` block. It is not probe
  02's A2, which had two plays and no barrier.

Placeholders are probe 02's: `<QUBIT>`, `<D_NS>`, `<DRIVE_FRAME>`, `<READOUT_TX_FRAME>`, `<READOUT_RX_FRAME>`. At the go
`run_probe.py` fills them from the properties and writes `task-E1.qasm` and `task-E2.qasm` with their hashes in
`filled.sha256`. The program set is built from those two texts as strings, E1 first.
