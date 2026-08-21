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
s q[0];
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
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
z q0_TO2;
h q0_TO2;
barrier q0_TO2, q1_TO2;
/* Teleporting qubits into chunk 3:
 * q0_TO2 from chunk 2
 * q[1] from chunk 1
 */
qubit q0_TO2_epr_2;
qubit q0_TO2_TO3;
bit telept_Zcorrect_q0_TO2_2;
bit telept_Xcorrect_q0_TO2_2;
reset q0_TO2_epr_2;
reset q0_TO2_TO3;
h q0_TO2_epr_2;
cx q0_TO2_epr_2, q0_TO2_TO3;
cx q0_TO2, q0_TO2_epr_2;
h q0_TO2;
telept_Zcorrect_q0_TO2_2 = measure q0_TO2;
telept_Xcorrect_q0_TO2_2 = measure q0_TO2_epr_2;
if(telept_Zcorrect_q0_TO2_2) z q0_TO2_TO3;
if(telept_Xcorrect_q0_TO2_2) x q0_TO2_TO3;
// q0_TO2 teleported into q0_TO2_TO3
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
measure q0_TO2_TO3 -> c[0];
measure q1_TO3 -> c[1];