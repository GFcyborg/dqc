OPENQASM 3.0;
include "stdgates.inc";
input float[64] a;
qubit[3] q;
bit[2] mid;
bit[3] out;
gate my_gate(a) c, t {
  gphase(a / 2);
  ry(a) c;
  cx c, t;
}
gate my_phase(a) c {
  ctrl @ inv @ gphase(a) c;
}
my_gate(a * 2) q[0], q[1];
measure q[0] -> mid[0];
measure q[1] -> mid[1];
while (mid == "00") {
  reset q[0];
  reset q[1];
  my_gate(a) q[0], q[1];
  my_phase(a - pi/2) q[1];
  mid[0] = measure q[0];
  mid[1] = measure q[1];
}
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
if (mid[0]) {
  reset q[0];
  reset q[1];
}
/* Teleporting qubits into chunk 3:
 * q[0] from chunk 2
 * q[1] from chunk 2
 * q[2] from chunk 1
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
out[0] = measure q[0];
out[1] = measure q[1];
out[2] = measure q[2];