// https://github.com/GFcyborg/dqc

OPENQASM 3.1;
include "stdgates.inc";

qubit[2] q;
bit[2] c;

reset q; //= 00
h q[0]; //= +

x q[1]; //= 1
h q[1]; //= -

// phase kickback:
cx q[0], q[1]; // cx(+-) = --

h q[0]; //= 1
h q[1]; //= 1

// Measure both qubits
c[0] = measure q[0];
c[1] = measure q[1];

