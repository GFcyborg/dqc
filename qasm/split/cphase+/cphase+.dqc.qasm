gate cphase(θ) a, b
{
  U(0, 0, θ / 2) a;
  cx a, b; //fixed case of CX
  U(0, 0, -θ / 2) b;
  cx a, b; //fixed case of CX
  U(0, 0, θ / 2) b;
}
/* Teleporting qubits into chunk 2:
 * no shared qubits from chunk 1
 */

qubit[2] q;
bit[2] c;
cphase(π / 2) q[0], q[1];
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 2
 * q[1] from chunk 2
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

c = measure q;