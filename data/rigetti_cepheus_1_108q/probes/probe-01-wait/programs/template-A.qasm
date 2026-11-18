OPENQASM 3.0;
bit[1] b;
#pragma braket verbatim
box{
rx(3.141592653589793) $<QUBIT>;
}
b[0] = measure $<QUBIT>;
