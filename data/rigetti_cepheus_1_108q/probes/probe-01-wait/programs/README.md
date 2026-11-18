# Programs

`template-<letter>.qasm` are the four programs of section 3 of the rule, written before the go, with two placeholders:
`<QUBIT>` (the physical qubit index chosen by section 2) and `<D_NS>` (d in nanoseconds, by section 2).
At the go, `run_probe.py` fills them and writes `task-<letter>.qasm` with its SHA-256 in `filled.sha256`.

Forms follow what the installed Braket SDK itself emits for a verbatim box and for a pulse play
(`Circuit.add_verbatim_box`, `PulseSequence.play` with a `ConstantWaveform`), so that the only new line in B, C and D
is the wait. `rx(pi)` is written as the SDK writes it, `rx(3.141592653589793)`.
Task D's waveform is declared in a `cal` block and played on the published frame `Transmon_<QUBIT>_charge_tx`;
no frame or port is defined locally.
