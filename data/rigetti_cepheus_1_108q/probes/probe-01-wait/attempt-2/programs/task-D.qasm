OPENQASM 3.0;
bit[1] b;
cal {
    waveform wait_d = constant(37900ns, 0.0);
}
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
}
cal {
    play(Transmon_99_charge_tx, wait_d);
}
b[0] = measure $99;
