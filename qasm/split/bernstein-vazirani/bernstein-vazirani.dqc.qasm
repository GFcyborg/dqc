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
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 * q[3] from chunk 1
 * q[4] from chunk 1
 * q[5] from chunk 1
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
qubit q3_epr_1;
qubit q3_TO2;
bit telept_Zcorrect_q3_1;
bit telept_Xcorrect_q3_1;
reset q3_epr_1;
reset q3_TO2;
h q3_epr_1;
cx q3_epr_1, q3_TO2;
cx q[3], q3_epr_1;
h q[3];
telept_Zcorrect_q3_1 = measure q[3];
telept_Xcorrect_q3_1 = measure q3_epr_1;
if(telept_Zcorrect_q3_1) z q3_TO2;
if(telept_Xcorrect_q3_1) x q3_TO2;
// q[3] teleported into q3_TO2
qubit q4_epr_1;
qubit q4_TO2;
bit telept_Zcorrect_q4_1;
bit telept_Xcorrect_q4_1;
reset q4_epr_1;
reset q4_TO2;
h q4_epr_1;
cx q4_epr_1, q4_TO2;
cx q[4], q4_epr_1;
h q[4];
telept_Zcorrect_q4_1 = measure q[4];
telept_Xcorrect_q4_1 = measure q4_epr_1;
if(telept_Zcorrect_q4_1) z q4_TO2;
if(telept_Xcorrect_q4_1) x q4_TO2;
// q[4] teleported into q4_TO2
qubit q5_epr_1;
qubit q5_TO2;
bit telept_Zcorrect_q5_1;
bit telept_Xcorrect_q5_1;
reset q5_epr_1;
reset q5_TO2;
h q5_epr_1;
cx q5_epr_1, q5_TO2;
cx q[5], q5_epr_1;
h q[5];
telept_Zcorrect_q5_1 = measure q[5];
telept_Xcorrect_q5_1 = measure q5_epr_1;
if(telept_Zcorrect_q5_1) z q5_TO2;
if(telept_Xcorrect_q5_1) x q5_TO2;
// q[5] teleported into q5_TO2
cx q5_TO2, q2_TO2;
cx q5_TO2, q3_TO2;
cx q5_TO2, q4_TO2;
h q0_TO2;
h q1_TO2;
h q2_TO2;
h q3_TO2;
h q4_TO2;
h q5_TO2;
barrier q0_TO2, q1_TO2, q2_TO2, q3_TO2, q4_TO2, q5_TO2;
c[0] = measure q0_TO2;
c[1] = measure q1_TO2;
c[2] = measure q2_TO2;
c[3] = measure q3_TO2;
c[4] = measure q4_TO2;
c[5] = measure q5_TO2;