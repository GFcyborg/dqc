// from: https://www.youtube.com/watch?v=MvX5OUK-tbE&t=53

OPENQASM 3.0;
include "stdgates.inc";

qubit[6] q;
bit[6] c;

h q[0];
h q[1];
h q[2];
h q[3];
h q[4];

x q[5];
h q[5];

cx q[5], q[0];
cx q[5], q[1];
cx q[5], q[2];
cx q[5], q[3];
cx q[5], q[4];

h q[0];
h q[1];
h q[2];
h q[3];
h q[4];
h q[5];

barrier q;

c = measure q;
