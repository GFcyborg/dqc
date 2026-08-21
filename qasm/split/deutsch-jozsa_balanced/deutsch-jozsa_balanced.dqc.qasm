OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
qubit    anc;
bit[3]   c;
x anc;
barrier q[0], q[1], q[2], anc;
h q[0];
h q[1];
h q[2];
h anc;
barrier q[0], q[1], q[2], anc;
cx q[0], anc;
/* Teleporting qubits into chunk 2:
 * anc from chunk 1
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 */
qubit anc_epr_1;
qubit anc_TO2;
bit telept_Zcorrect_anc_1;
bit telept_Xcorrect_anc_1;
reset anc_epr_1;
reset anc_TO2;
h anc_epr_1;
cx anc_epr_1, anc_TO2;
cx anc, anc_epr_1;
h anc;
telept_Zcorrect_anc_1 = measure anc;
telept_Xcorrect_anc_1 = measure anc_epr_1;
if(telept_Zcorrect_anc_1) z anc_TO2;
if(telept_Xcorrect_anc_1) x anc_TO2;
// anc teleported into anc_TO2
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
cx q1_TO2, anc_TO2;
cx q2_TO2, anc_TO2;
barrier q0_TO2, q1_TO2, q2_TO2, anc_TO2;
h q0_TO2;
/* Teleporting qubits into chunk 3:
 * anc_TO2 from chunk 2
 * q0_TO2 from chunks 1, 2
 * q1_TO2 from chunks 1, 2
 * q2_TO2 from chunks 1, 2
 */
qubit anc_TO2_epr_2;
qubit anc_TO2_TO3;
bit telept_Zcorrect_anc_TO2_2;
bit telept_Xcorrect_anc_TO2_2;
reset anc_TO2_epr_2;
reset anc_TO2_TO3;
h anc_TO2_epr_2;
cx anc_TO2_epr_2, anc_TO2_TO3;
cx anc_TO2, anc_TO2_epr_2;
h anc_TO2;
telept_Zcorrect_anc_TO2_2 = measure anc_TO2;
telept_Xcorrect_anc_TO2_2 = measure anc_TO2_epr_2;
if(telept_Zcorrect_anc_TO2_2) z anc_TO2_TO3;
if(telept_Xcorrect_anc_TO2_2) x anc_TO2_TO3;
// anc_TO2 teleported into anc_TO2_TO3
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
qubit q1_TO2_epr_2;
qubit q1_TO2_TO3;
bit telept_Zcorrect_q1_TO2_2;
bit telept_Xcorrect_q1_TO2_2;
reset q1_TO2_epr_2;
reset q1_TO2_TO3;
h q1_TO2_epr_2;
cx q1_TO2_epr_2, q1_TO2_TO3;
cx q1_TO2, q1_TO2_epr_2;
h q1_TO2;
telept_Zcorrect_q1_TO2_2 = measure q1_TO2;
telept_Xcorrect_q1_TO2_2 = measure q1_TO2_epr_2;
if(telept_Zcorrect_q1_TO2_2) z q1_TO2_TO3;
if(telept_Xcorrect_q1_TO2_2) x q1_TO2_TO3;
// q1_TO2 teleported into q1_TO2_TO3
qubit q2_TO2_epr_2;
qubit q2_TO2_TO3;
bit telept_Zcorrect_q2_TO2_2;
bit telept_Xcorrect_q2_TO2_2;
reset q2_TO2_epr_2;
reset q2_TO2_TO3;
h q2_TO2_epr_2;
cx q2_TO2_epr_2, q2_TO2_TO3;
cx q2_TO2, q2_TO2_epr_2;
h q2_TO2;
telept_Zcorrect_q2_TO2_2 = measure q2_TO2;
telept_Xcorrect_q2_TO2_2 = measure q2_TO2_epr_2;
if(telept_Zcorrect_q2_TO2_2) z q2_TO2_TO3;
if(telept_Xcorrect_q2_TO2_2) x q2_TO2_TO3;
// q2_TO2 teleported into q2_TO2_TO3
h q1_TO2_TO3;
h q2_TO2_TO3;
barrier q0_TO2_TO3, q1_TO2_TO3, q2_TO2_TO3, anc_TO2_TO3;
c[0] = measure q0_TO2_TO3;
c[1] = measure q1_TO2_TO3;
c[2] = measure q2_TO2_TO3;