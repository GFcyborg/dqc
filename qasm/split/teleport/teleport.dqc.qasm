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
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 */
qubit q0_epr_1;
qubit q0_TO2;
bit telept_Zcorrect_q0_1;
bit telept_Xcorrect_q0_1;
reset q0_epr_1;
reset q0_TO2;
h q0_epr_1;
cx q0_epr_1, q0_TO2;
cx q[0], q0_epr_1;
h q[0];
telept_Zcorrect_q0_1 = measure q[0];
telept_Xcorrect_q0_1 = measure q0_epr_1;
if(telept_Zcorrect_q0_1) z q0_TO2;
if(telept_Xcorrect_q0_1) x q0_TO2;
// q[0] teleported into q0_TO2
qubit q1_epr_1;
qubit q1_TO2;
bit telept_Zcorrect_q1_1;
bit telept_Xcorrect_q1_1;
reset q1_epr_1;
reset q1_TO2;
h q1_epr_1;
cx q1_epr_1, q1_TO2;
cx q[1], q1_epr_1;
h q[1];
telept_Zcorrect_q1_1 = measure q[1];
telept_Xcorrect_q1_1 = measure q1_epr_1;
if(telept_Zcorrect_q1_1) z q1_TO2;
if(telept_Xcorrect_q1_1) x q1_TO2;
// q[1] teleported into q1_TO2
qubit q2_epr_1;
qubit q2_TO2;
bit telept_Zcorrect_q2_1;
bit telept_Xcorrect_q2_1;
reset q2_epr_1;
reset q2_TO2;
h q2_epr_1;
cx q2_epr_1, q2_TO2;
cx q[2], q2_epr_1;
h q[2];
telept_Zcorrect_q2_1 = measure q[2];
telept_Xcorrect_q2_1 = measure q2_epr_1;
if(telept_Zcorrect_q2_1) z q2_TO2;
if(telept_Xcorrect_q2_1) x q2_TO2;
// q[2] teleported into q2_TO2
U(0.3, 0.2, 0.1) q[0];
h q[1];
cx q[1], q[2];
barrier q[0], q[1], q[2];
cx q[0], q[1];
h q[0];
c0 = measure q[0];
/* Teleporting qubits into chunk 3:
 * q[1] from chunk 2
 * q[2] from chunk 2
 */
qubit q1_epr_2;
qubit q1_TO3;
bit telept_Zcorrect_q1_2;
bit telept_Xcorrect_q1_2;
reset q1_epr_2;
reset q1_TO3;
h q1_epr_2;
cx q1_epr_2, q1_TO3;
cx q[1], q1_epr_2;
h q[1];
telept_Zcorrect_q1_2 = measure q[1];
telept_Xcorrect_q1_2 = measure q1_epr_2;
if(telept_Zcorrect_q1_2) z q1_TO3;
if(telept_Xcorrect_q1_2) x q1_TO3;
// q[1] teleported into q1_TO3
qubit q2_epr_2;
qubit q2_TO3;
bit telept_Zcorrect_q2_2;
bit telept_Xcorrect_q2_2;
reset q2_epr_2;
reset q2_TO3;
h q2_epr_2;
cx q2_epr_2, q2_TO3;
cx q[2], q2_epr_2;
h q[2];
telept_Zcorrect_q2_2 = measure q[2];
telept_Xcorrect_q2_2 = measure q2_epr_2;
if(telept_Zcorrect_q2_2) z q2_TO3;
if(telept_Xcorrect_q2_2) x q2_TO3;
// q[2] teleported into q2_TO3
c1 = measure q[1];
if(c0) z q[2];
if(c1) { x q[2]; }
post q[2];
c2 = measure q[2];