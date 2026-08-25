OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
/* Teleporting qubits into chunk 2:
 * no shared qubits from chunk 1
 */
bit[2] c;
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 1
 */
qubit q0_epr_2;
qubit q0_TO3;
bit telept_Zcorrect_q0_2;
bit telept_Xcorrect_q0_2;
reset q0_epr_2;
reset q0_TO3;
h q0_epr_2;
cx q0_epr_2, q0_TO3;
cx q[0], q0_epr_2;
h q[0];
telept_Zcorrect_q0_2 = measure q[0];
telept_Xcorrect_q0_2 = measure q0_epr_2;
if(telept_Zcorrect_q0_2) z q0_TO3;
if(telept_Xcorrect_q0_2) x q0_TO3;
// q[0] teleported into q0_TO3
h q0_TO3;
/* Teleporting qubits into chunk 4:
 * q0_TO3 from chunk 3
 * q[1] from chunk 1
 */
qubit q0_TO3_epr_3;
qubit q0_TO3_TO4;
bit telept_Zcorrect_q0_TO3_3;
bit telept_Xcorrect_q0_TO3_3;
reset q0_TO3_epr_3;
reset q0_TO3_TO4;
h q0_TO3_epr_3;
cx q0_TO3_epr_3, q0_TO3_TO4;
cx q0_TO3, q0_TO3_epr_3;
h q0_TO3;
telept_Zcorrect_q0_TO3_3 = measure q0_TO3;
telept_Xcorrect_q0_TO3_3 = measure q0_TO3_epr_3;
if(telept_Zcorrect_q0_TO3_3) z q0_TO3_TO4;
if(telept_Xcorrect_q0_TO3_3) x q0_TO3_TO4;
// q0_TO3 teleported into q0_TO3_TO4
qubit q1_epr_3;
qubit q1_TO4;
bit telept_Zcorrect_q1_3;
bit telept_Xcorrect_q1_3;
reset q1_epr_3;
reset q1_TO4;
h q1_epr_3;
cx q1_epr_3, q1_TO4;
cx q[1], q1_epr_3;
h q[1];
telept_Zcorrect_q1_3 = measure q[1];
telept_Xcorrect_q1_3 = measure q1_epr_3;
if(telept_Zcorrect_q1_3) z q1_TO4;
if(telept_Xcorrect_q1_3) x q1_TO4;
// q[1] teleported into q1_TO4
cx q0_TO3_TO4, q1_TO4;
/* Teleporting qubits into chunk 5:
 * q0_TO3_TO4 from chunk 4
 * q1_TO4 from chunk 4
 */
qubit q0_TO3_TO4_epr_4;
qubit q0_TO3_TO4_TO5;
bit telept_Zcorrect_q0_TO3_TO4_4;
bit telept_Xcorrect_q0_TO3_TO4_4;
reset q0_TO3_TO4_epr_4;
reset q0_TO3_TO4_TO5;
h q0_TO3_TO4_epr_4;
cx q0_TO3_TO4_epr_4, q0_TO3_TO4_TO5;
cx q0_TO3_TO4, q0_TO3_TO4_epr_4;
h q0_TO3_TO4;
telept_Zcorrect_q0_TO3_TO4_4 = measure q0_TO3_TO4;
telept_Xcorrect_q0_TO3_TO4_4 = measure q0_TO3_TO4_epr_4;
if(telept_Zcorrect_q0_TO3_TO4_4) z q0_TO3_TO4_TO5;
if(telept_Xcorrect_q0_TO3_TO4_4) x q0_TO3_TO4_TO5;
// q0_TO3_TO4 teleported into q0_TO3_TO4_TO5
qubit q1_TO4_epr_4;
qubit q1_TO4_TO5;
bit telept_Zcorrect_q1_TO4_4;
bit telept_Xcorrect_q1_TO4_4;
reset q1_TO4_epr_4;
reset q1_TO4_TO5;
h q1_TO4_epr_4;
cx q1_TO4_epr_4, q1_TO4_TO5;
cx q1_TO4, q1_TO4_epr_4;
h q1_TO4;
telept_Zcorrect_q1_TO4_4 = measure q1_TO4;
telept_Xcorrect_q1_TO4_4 = measure q1_TO4_epr_4;
if(telept_Zcorrect_q1_TO4_4) z q1_TO4_TO5;
if(telept_Xcorrect_q1_TO4_4) x q1_TO4_TO5;
// q1_TO4 teleported into q1_TO4_TO5
c[0] = measure q0_TO3_TO4_TO5;
c[1] = measure q1_TO4_TO5;