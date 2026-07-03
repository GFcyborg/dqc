// quantum Fourier transform
include "stdgates.inc";
qubit[4] q;
bit[4] c;
reset q;
x q[0];
x q[2];
barrier q;
h q[0];
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 * q[3] from chunk 1
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
cphase(pi / 2) q[1], q[0];
h q[1];
cphase(pi / 4) q[2], q[0];
cphase(pi / 2) q[2], q[1];
h q[2];
cphase(pi / 8) q[3], q[0];
cphase(pi / 4) q[3], q[1];
cphase(pi / 2) q[3], q[2];
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 * q[3] from chunks 1, 2
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
h q[3];
c = measure q;