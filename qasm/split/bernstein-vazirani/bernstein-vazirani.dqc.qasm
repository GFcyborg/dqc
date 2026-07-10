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
qubit q0_epr_TARGET_1;
bit telept_Zcorrect_q0_1;
bit telept_Xcorrect_q0_1;
reset q0_epr_1;
reset q0_epr_TARGET_1;
h q0_epr_1;
cx q0_epr_1, q0_epr_TARGET_1;
cx q[0], q0_epr_1;
h q[0];
telept_Zcorrect_q0_1 = measure q[0];
telept_Xcorrect_q0_1 = measure q0_epr_1;
if(telept_Zcorrect_q0_1) z q0_epr_TARGET_1;
if(telept_Xcorrect_q0_1) x q0_epr_TARGET_1;
// q[0] teleported into q0_epr_TARGET_1
qubit q1_epr_1;
qubit q1_epr_TARGET_1;
bit telept_Zcorrect_q1_1;
bit telept_Xcorrect_q1_1;
reset q1_epr_1;
reset q1_epr_TARGET_1;
h q1_epr_1;
cx q1_epr_1, q1_epr_TARGET_1;
cx q[1], q1_epr_1;
h q[1];
telept_Zcorrect_q1_1 = measure q[1];
telept_Xcorrect_q1_1 = measure q1_epr_1;
if(telept_Zcorrect_q1_1) z q1_epr_TARGET_1;
if(telept_Xcorrect_q1_1) x q1_epr_TARGET_1;
// q[1] teleported into q1_epr_TARGET_1
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
qubit q3_epr_1;
qubit q3_epr_TARGET_1;
bit telept_Zcorrect_q3_1;
bit telept_Xcorrect_q3_1;
reset q3_epr_1;
reset q3_epr_TARGET_1;
h q3_epr_1;
cx q3_epr_1, q3_epr_TARGET_1;
cx q[3], q3_epr_1;
h q[3];
telept_Zcorrect_q3_1 = measure q[3];
telept_Xcorrect_q3_1 = measure q3_epr_1;
if(telept_Zcorrect_q3_1) z q3_epr_TARGET_1;
if(telept_Xcorrect_q3_1) x q3_epr_TARGET_1;
// q[3] teleported into q3_epr_TARGET_1
qubit q4_epr_1;
qubit q4_epr_TARGET_1;
bit telept_Zcorrect_q4_1;
bit telept_Xcorrect_q4_1;
reset q4_epr_1;
reset q4_epr_TARGET_1;
h q4_epr_1;
cx q4_epr_1, q4_epr_TARGET_1;
cx q[4], q4_epr_1;
h q[4];
telept_Zcorrect_q4_1 = measure q[4];
telept_Xcorrect_q4_1 = measure q4_epr_1;
if(telept_Zcorrect_q4_1) z q4_epr_TARGET_1;
if(telept_Xcorrect_q4_1) x q4_epr_TARGET_1;
// q[4] teleported into q4_epr_TARGET_1
qubit q5_epr_1;
qubit q5_epr_TARGET_1;
bit telept_Zcorrect_q5_1;
bit telept_Xcorrect_q5_1;
reset q5_epr_1;
reset q5_epr_TARGET_1;
h q5_epr_1;
cx q5_epr_1, q5_epr_TARGET_1;
cx q[5], q5_epr_1;
h q[5];
telept_Zcorrect_q5_1 = measure q[5];
telept_Xcorrect_q5_1 = measure q5_epr_1;
if(telept_Zcorrect_q5_1) z q5_epr_TARGET_1;
if(telept_Xcorrect_q5_1) x q5_epr_TARGET_1;
// q[5] teleported into q5_epr_TARGET_1
cx q[5], q[2];
cx q[5], q[3];
cx q[5], q[4];
h q[0];
h q[1];
/* Teleporting qubits into chunk 3:
 * q[0] from chunks 1, 2
 * q[1] from chunks 1, 2
 * q[2] from chunks 1, 2
 * q[3] from chunks 1, 2
 * q[4] from chunks 1, 2
 * q[5] from chunks 1, 2
 */
qubit q0_epr_2;
qubit q0_epr_TARGET_2;
bit telept_Zcorrect_q0_2;
bit telept_Xcorrect_q0_2;
reset q0_epr_2;
reset q0_epr_TARGET_2;
h q0_epr_2;
cx q0_epr_2, q0_epr_TARGET_2;
cx q[0], q0_epr_2;
h q[0];
telept_Zcorrect_q0_2 = measure q[0];
telept_Xcorrect_q0_2 = measure q0_epr_2;
if(telept_Zcorrect_q0_2) z q0_epr_TARGET_2;
if(telept_Xcorrect_q0_2) x q0_epr_TARGET_2;
// q[0] teleported into q0_epr_TARGET_2
qubit q1_epr_2;
qubit q1_epr_TARGET_2;
bit telept_Zcorrect_q1_2;
bit telept_Xcorrect_q1_2;
reset q1_epr_2;
reset q1_epr_TARGET_2;
h q1_epr_2;
cx q1_epr_2, q1_epr_TARGET_2;
cx q[1], q1_epr_2;
h q[1];
telept_Zcorrect_q1_2 = measure q[1];
telept_Xcorrect_q1_2 = measure q1_epr_2;
if(telept_Zcorrect_q1_2) z q1_epr_TARGET_2;
if(telept_Xcorrect_q1_2) x q1_epr_TARGET_2;
// q[1] teleported into q1_epr_TARGET_2
qubit q2_epr_2;
qubit q2_epr_TARGET_2;
bit telept_Zcorrect_q2_2;
bit telept_Xcorrect_q2_2;
reset q2_epr_2;
reset q2_epr_TARGET_2;
h q2_epr_2;
cx q2_epr_2, q2_epr_TARGET_2;
cx q[2], q2_epr_2;
h q[2];
telept_Zcorrect_q2_2 = measure q[2];
telept_Xcorrect_q2_2 = measure q2_epr_2;
if(telept_Zcorrect_q2_2) z q2_epr_TARGET_2;
if(telept_Xcorrect_q2_2) x q2_epr_TARGET_2;
// q[2] teleported into q2_epr_TARGET_2
qubit q3_epr_2;
qubit q3_epr_TARGET_2;
bit telept_Zcorrect_q3_2;
bit telept_Xcorrect_q3_2;
reset q3_epr_2;
reset q3_epr_TARGET_2;
h q3_epr_2;
cx q3_epr_2, q3_epr_TARGET_2;
cx q[3], q3_epr_2;
h q[3];
telept_Zcorrect_q3_2 = measure q[3];
telept_Xcorrect_q3_2 = measure q3_epr_2;
if(telept_Zcorrect_q3_2) z q3_epr_TARGET_2;
if(telept_Xcorrect_q3_2) x q3_epr_TARGET_2;
// q[3] teleported into q3_epr_TARGET_2
qubit q4_epr_2;
qubit q4_epr_TARGET_2;
bit telept_Zcorrect_q4_2;
bit telept_Xcorrect_q4_2;
reset q4_epr_2;
reset q4_epr_TARGET_2;
h q4_epr_2;
cx q4_epr_2, q4_epr_TARGET_2;
cx q[4], q4_epr_2;
h q[4];
telept_Zcorrect_q4_2 = measure q[4];
telept_Xcorrect_q4_2 = measure q4_epr_2;
if(telept_Zcorrect_q4_2) z q4_epr_TARGET_2;
if(telept_Xcorrect_q4_2) x q4_epr_TARGET_2;
// q[4] teleported into q4_epr_TARGET_2
qubit q5_epr_2;
qubit q5_epr_TARGET_2;
bit telept_Zcorrect_q5_2;
bit telept_Xcorrect_q5_2;
reset q5_epr_2;
reset q5_epr_TARGET_2;
h q5_epr_2;
cx q5_epr_2, q5_epr_TARGET_2;
cx q[5], q5_epr_2;
h q[5];
telept_Zcorrect_q5_2 = measure q[5];
telept_Xcorrect_q5_2 = measure q5_epr_2;
if(telept_Zcorrect_q5_2) z q5_epr_TARGET_2;
if(telept_Xcorrect_q5_2) x q5_epr_TARGET_2;
// q[5] teleported into q5_epr_TARGET_2
h q[2];
h q[3];
h q[4];
h q[5];
barrier q[0], q[1], q[2], q[3], q[4], q[5];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
c[3] = measure q[3];
c[4] = measure q[4];
c[5] = measure q[5];