// QFT and measure, version 2
include "stdgates.inc";

qubit[4] q;
bit c0;
bit c1;
bit c2;
bit c3;

reset q;
h q;
barrier q;
h q[0];
measure q[0] -> c0;
/* Teleporting qubits into chunk 2:
 * c0 from chunk 1
 * c1 from chunk 1
 * c2 from chunk 1
 * h from chunk 1
 * q from chunk 1
 */
if(c0 == 1) { rz(pi / 2) q[1]; }
h q[1];
measure q[1] -> c1;
if(c0==1) { rz(pi / 4) q[2]; }
if(c1==1) { rz(pi / 2) q[2]; }
h q[2];
measure q[2] -> c2;
/* Teleporting qubits into chunk 3:
 * c0 from chunk 2
 * c1 from chunk 2
 * c2 from chunk 2
 * h from chunk 2
 * pi from chunk 2
 * q from chunk 2
 * rz from chunk 2
 */
if(c0 == 1) { rz(pi / 8) q[3]; }
if(c1 == 1) { rz(pi / 4) q[3]; }
if(c2 == 1) { rz(pi / 2) q[3]; }
h q[3];
measure q[3] -> c3;