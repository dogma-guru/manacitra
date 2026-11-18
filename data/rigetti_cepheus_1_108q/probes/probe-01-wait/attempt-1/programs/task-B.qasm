OPENQASM 3.0;
bit[1] b;
#pragma braket verbatim
box{
rx(3.141592653589793) $99;
delay[37900ns] $99;
}
b[0] = measure $99;
