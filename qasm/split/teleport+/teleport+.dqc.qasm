OPENQASM 3.1;
include "stdgates.inc";
qubit[3] q;
bit c0;
bit c1;
bit c2;
gate post q { }
reset q;
U(0.3, 0.2, 0.1) q[0];
h q[1];
cx q[1], q[2];
barrier q;
cx q[0], q[1];
h q[0];
// DQC teleport bridge from chunk 1 to 2
// teleport c0 via EPR pair and classical correction bits
// teleport c1 via EPR pair and classical correction bits
// teleport c2 via EPR pair and classical correction bits
// teleport post via EPR pair and classical correction bits
// teleport q via EPR pair and classical correction bits
c0 = measure q[0];
pragma dqc.v1.split id=1
c1 = measure q[1];
if(c0  ) z q[2];
if(c1  ) { x q[2]; }
post q[2];
pragma dqc.v1.split id=2
c2 = measure q[2];