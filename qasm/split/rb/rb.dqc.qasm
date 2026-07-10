OPENQASM 3.1;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
reset q[0];
reset q[1];
h q[0];
barrier q[0], q[1];
cz q[0], q[1];
barrier q[0], q[1];
s q[0];
cz q[0], q[1];
barrier q[0], q[1];
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
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
s q[0];
z q[0];
h q[0];
barrier q[0], q[1];
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
measure q[0] -> c[0];
measure q[1] -> c[1];