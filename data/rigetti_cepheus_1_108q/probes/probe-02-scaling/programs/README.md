# Programs

`template-<label>.qasm` are the four programs of section 3 of the rule, written before the submission from probe 01's
Task A and Task D templates (probe 01 hand-back, `programs/template-A.qasm` and `programs/template-D.qasm`).
Placeholders: `<QUBIT>` (the physical qubit index chosen by section 2), `<D_NS>` (d in nanoseconds, by section 2),
`<DRIVE_FRAME>`, `<READOUT_TX_FRAME>` and `<READOUT_RX_FRAME>` (the frames `Transmon_<n>_charge_tx`,
`Transmon_<n>_readout_tx` and `Transmon_<n>_readout_rx`, taken from the properties at the read; the fill stops if any
of the three is not published there).

* A0 is probe 01's Task A unchanged: no wait, 100 shots.
* A1 is probe 01's Task D with the frame as a placeholder: one play of d, 200 shots.
* A2 is A1 with a second play of the same d waveform on the same frame, in the same `cal` block: 100 shots.
* B1 is A1 with `barrier <drive>, <readout_tx>, <readout_rx>;` after the play, in the same `cal` block: 200 shots.

At the submission, `run_probe.py` fills them and writes `task-<label>.qasm` with its SHA-256 in `filled.sha256`.
