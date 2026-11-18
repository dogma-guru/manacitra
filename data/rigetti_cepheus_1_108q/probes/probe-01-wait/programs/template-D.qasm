OPENQASM 3.0;
bit[1] b;
cal {
    waveform wait_d = constant(<D_NS>ns, 0.0);
}
#pragma braket verbatim
box{
rx(3.141592653589793) $<QUBIT>;
}
cal {
    play(Transmon_<QUBIT>_charge_tx, wait_d);
}
b[0] = measure $<QUBIT>;
