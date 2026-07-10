OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
bit c0;
bit c1;
bit c2;
gate post q { }
reset q[0];
reset q[1];
reset q[2];
U(0.3, 0.2, 0.1) q[0];
h q[1];
cx q[1], q[2];
barrier q[0], q[1], q[2];
cx q[0], q[1];
h q[0];
c0 = measure q[0];
c1 = measure q[1];
/* Teleporting qubits into chunk 2:
 * q[2] from chunk 1
 */
qubit q2_epr_1;
qubit q2_epr_TARGET_1;
bit telept_Zcorrect_q2_1;
bit telept_Xcorrect_q2_1;
reset q2_epr_1;
reset q2_epr_TARGET_1;
h q2_epr_1;
cx q2_epr_1, q2_epr_TARGET_1;
cx q[2], q2_epr_1;
h q[2];
telept_Zcorrect_q2_1 = measure q[2];
telept_Xcorrect_q2_1 = measure q2_epr_1;
if(telept_Zcorrect_q2_1) z q2_epr_TARGET_1;
if(telept_Xcorrect_q2_1) x q2_epr_TARGET_1;
// q[2] teleported into q2_epr_TARGET_1
if(c0) z q[2];
if(c1) { x q[2]; }
post q[2];
c2 = measure q[2];