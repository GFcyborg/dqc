OPENQASM 3.0;
include "stdgates.inc";
qubit[6] q;
bit[6] c;
h q[0];
h q[1];
h q[2];
h q[3];
h q[4];
// DQC teleport bridge from chunk 1 to 2
// teleport h via EPR pair and classical correction bits
// teleport q via EPR pair and classical correction bits
x q[5];
h q[5];
cx q[5], q[0];
cx q[5], q[1];
// DQC teleport bridge from chunk 2 to 3
// teleport cx via EPR pair and classical correction bits
// teleport h via EPR pair and classical correction bits
// teleport q via EPR pair and classical correction bits
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