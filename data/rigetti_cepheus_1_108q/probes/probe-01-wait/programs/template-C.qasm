OPENQASM 3.0;
bit[1] b;
rx(3.141592653589793) $<QUBIT>;
delay[<D_NS>ns] $<QUBIT>;
b[0] = measure $<QUBIT>;
