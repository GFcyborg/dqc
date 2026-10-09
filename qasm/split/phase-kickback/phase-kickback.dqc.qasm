OPENQASM 3.1;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
reset q[0];
reset q[1];
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
h q0_TO2;
x q1_TO2;
/* Teleporting qubits into chunk 3:
 * q0_TO2 from chunk 2
 * q1_TO2 from chunk 2
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
h q1_TO2_TO3;
cx q0_TO2_TO3, q1_TO2_TO3;
/* Teleporting qubits into chunk 4:
 * q0_TO2_TO3 from chunk 3
 */
qubit q0_TO2_TO3_epr_3;
qubit q0_TO2_TO3_TO4;
bit telept_Zcorrect_q0_TO2_TO3_3;
bit telept_Xcorrect_q0_TO2_TO3_3;
reset q0_TO2_TO3_epr_3;
reset q0_TO2_TO3_TO4;
h q0_TO2_TO3_epr_3;
cx q0_TO2_TO3_epr_3, q0_TO2_TO3_TO4;
cx q0_TO2_TO3, q0_TO2_TO3_epr_3;
h q0_TO2_TO3;
telept_Zcorrect_q0_TO2_TO3_3 = measure q0_TO2_TO3;
telept_Xcorrect_q0_TO2_TO3_3 = measure q0_TO2_TO3_epr_3;
if(telept_Zcorrect_q0_TO2_TO3_3) z q0_TO2_TO3_TO4;
if(telept_Xcorrect_q0_TO2_TO3_3) x q0_TO2_TO3_TO4;
// q0_TO2_TO3 teleported into q0_TO2_TO3_TO4
h q0_TO2_TO3_TO4;
/* Teleporting qubits into chunk 5:
 * q0_TO2_TO3_TO4 from chunk 4
 * q1_TO2_TO3 from chunk 3
 */
qubit q0_TO2_TO3_TO4_epr_4;
qubit q0_TO2_TO3_TO4_TO5;
bit telept_Zcorrect_q0_TO2_TO3_TO4_4;
bit telept_Xcorrect_q0_TO2_TO3_TO4_4;
reset q0_TO2_TO3_TO4_epr_4;
reset q0_TO2_TO3_TO4_TO5;
h q0_TO2_TO3_TO4_epr_4;
cx q0_TO2_TO3_TO4_epr_4, q0_TO2_TO3_TO4_TO5;
cx q0_TO2_TO3_TO4, q0_TO2_TO3_TO4_epr_4;
h q0_TO2_TO3_TO4;
telept_Zcorrect_q0_TO2_TO3_TO4_4 = measure q0_TO2_TO3_TO4;
telept_Xcorrect_q0_TO2_TO3_TO4_4 = measure q0_TO2_TO3_TO4_epr_4;
if(telept_Zcorrect_q0_TO2_TO3_TO4_4) z q0_TO2_TO3_TO4_TO5;
if(telept_Xcorrect_q0_TO2_TO3_TO4_4) x q0_TO2_TO3_TO4_TO5;
// q0_TO2_TO3_TO4 teleported into q0_TO2_TO3_TO4_TO5
qubit q1_TO2_TO3_epr_4;
qubit q1_TO2_TO3_TO5;
bit telept_Zcorrect_q1_TO2_TO3_4;
bit telept_Xcorrect_q1_TO2_TO3_4;
reset q1_TO2_TO3_epr_4;
reset q1_TO2_TO3_TO5;
h q1_TO2_TO3_epr_4;
cx q1_TO2_TO3_epr_4, q1_TO2_TO3_TO5;
cx q1_TO2_TO3, q1_TO2_TO3_epr_4;
h q1_TO2_TO3;
telept_Zcorrect_q1_TO2_TO3_4 = measure q1_TO2_TO3;
telept_Xcorrect_q1_TO2_TO3_4 = measure q1_TO2_TO3_epr_4;
if(telept_Zcorrect_q1_TO2_TO3_4) z q1_TO2_TO3_TO5;
if(telept_Xcorrect_q1_TO2_TO3_4) x q1_TO2_TO3_TO5;
// q1_TO2_TO3 teleported into q1_TO2_TO3_TO5
h q1_TO2_TO3_TO5;
c[0] = measure q0_TO2_TO3_TO4_TO5;
c[1] = measure q1_TO2_TO3_TO5;