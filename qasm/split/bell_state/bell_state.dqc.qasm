OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
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
bit[2] c;
h q[0];
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 2
 * q[1] from chunk 1
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
cx q[0], q[1];
/* Teleporting qubits into chunk 4:
 * q[0] from chunk 3
 * q[1] from chunk 3
 */
qubit q0_epr_3;
qubit q0_epr_TARGET_3;
bit telept_Zcorrect_q0_3;
bit telept_Xcorrect_q0_3;
reset q0_epr_3;
reset q0_epr_TARGET_3;
h q0_epr_3;
cx q0_epr_3, q0_epr_TARGET_3;
cx q[0], q0_epr_3;
h q[0];
telept_Zcorrect_q0_3 = measure q[0];
telept_Xcorrect_q0_3 = measure q0_epr_3;
if(telept_Zcorrect_q0_3) z q0_epr_TARGET_3;
if(telept_Xcorrect_q0_3) x q0_epr_TARGET_3;
// q[0] teleported into q0_epr_TARGET_3
qubit q1_epr_3;
qubit q1_epr_TARGET_3;
bit telept_Zcorrect_q1_3;
bit telept_Xcorrect_q1_3;
reset q1_epr_3;
reset q1_epr_TARGET_3;
h q1_epr_3;
cx q1_epr_3, q1_epr_TARGET_3;
cx q[1], q1_epr_3;
h q[1];
telept_Zcorrect_q1_3 = measure q[1];
telept_Xcorrect_q1_3 = measure q1_epr_3;
if(telept_Zcorrect_q1_3) z q1_epr_TARGET_3;
if(telept_Xcorrect_q1_3) x q1_epr_TARGET_3;
// q[1] teleported into q1_epr_TARGET_3
c[0] = measure q[0];
c[1] = measure q[1];