OPENQASM 3.1;
include "stdgates.inc";
qubit[4] q;
bit c0;
bit c1;
bit c2;
bit c3;
reset q[0];
reset q[1];
reset q[2];
reset q[3];
h q;
barrier q[0], q[1], q[2], q[3];
h q[0];
measure q[0] -> c0;
if(c0) { rz(pi / 2) q[1];
}
h q[1];
measure q[1] -> c1;
if(c0) { rz(pi / 4) q[2]; }
if(c1) { rz(pi / 2) q[2]; }
h q[2];
/* Teleporting qubits into chunk 2:
 * q[2] from chunk 1
 * q[3] from chunk 1
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
measure q[2] -> c2;
if(c0) { rz(pi / 8) q[3]; }
if(c1) { rz(pi / 4) q[3]; }
if(c2) { rz(pi / 2) q[3]; }
h q[3];
/* Teleporting qubits into chunk 3:
 * q[3] from chunk 2
 */
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
measure q[3] -> c3;