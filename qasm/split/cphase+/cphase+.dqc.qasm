OPENQASM 3.1;
include "stdgates.inc";
gate my_cphase(θ) a, b
{
  U(0, 0, θ / 2) a;
  cx a, b;
  U(0, 0, -θ / 2) b;
  cx a, b;
  U(0, 0, θ / 2) b;
}
/* Teleporting qubits into chunk 2:
 * no shared qubits from chunk 1
 */
qubit[2] q;
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 2
 * q[1] from chunk 2
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
bit[2] c;
my_cphase(π / 2) q[0], q[1];
/* Teleporting qubits into chunk 4:
 * q[0] from chunk 3
 * q[1] from chunk 3
 */
qubit q0_epr_3;
qubit q0_TO4;
bit telept_Zcorrect_q0_3;
bit telept_Xcorrect_q0_3;
reset q0_epr_3;
reset q0_TO4;
h q0_epr_3;
cx q0_epr_3, q0_TO4;
cx q[0], q0_epr_3;
h q[0];
telept_Zcorrect_q0_3 = measure q[0];
telept_Xcorrect_q0_3 = measure q0_epr_3;
if(telept_Zcorrect_q0_3) z q0_TO4;
if(telept_Xcorrect_q0_3) x q0_TO4;
// q[0] teleported into q0_TO4
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
c[0] = measure q[0];
c[1] = measure q[1];