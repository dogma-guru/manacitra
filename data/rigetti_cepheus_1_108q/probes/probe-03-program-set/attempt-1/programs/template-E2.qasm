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
    play(<DRIVE_FRAME>, wait_d);
    play(<DRIVE_FRAME>, wait_d);
    barrier <DRIVE_FRAME>, <READOUT_TX_FRAME>, <READOUT_RX_FRAME>;
}
b[0] = measure $<QUBIT>;
