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
while (mid == "00") {
  reset q0_TO2;
  reset q1_TO2;
  my_gate(a) q0_TO2, q1_TO2;
  my_phase(a - pi/2) q1_TO2;
  mid[0] = measure q0_TO2;
  mid[1] = measure q1_TO2;
}
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
if (mid[0]) {
  reset q0_TO2_TO3;
  reset q1_TO2_TO3;
}
/* Teleporting qubits into chunk 4:
 * q0_TO2_TO3 from chunk 3
 * q1_TO2_TO3 from chunk 3
 * q[2] from chunk 1
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
qubit q1_TO2_TO3_epr_3;
qubit q1_TO2_TO3_TO4;
bit telept_Zcorrect_q1_TO2_TO3_3;
bit telept_Xcorrect_q1_TO2_TO3_3;
reset q1_TO2_TO3_epr_3;
reset q1_TO2_TO3_TO4;
h q1_TO2_TO3_epr_3;
cx q1_TO2_TO3_epr_3, q1_TO2_TO3_TO4;
cx q1_TO2_TO3, q1_TO2_TO3_epr_3;
h q1_TO2_TO3;
telept_Zcorrect_q1_TO2_TO3_3 = measure q1_TO2_TO3;
telept_Xcorrect_q1_TO2_TO3_3 = measure q1_TO2_TO3_epr_3;
if(telept_Zcorrect_q1_TO2_TO3_3) z q1_TO2_TO3_TO4;
if(telept_Xcorrect_q1_TO2_TO3_3) x q1_TO2_TO3_TO4;
// q1_TO2_TO3 teleported into q1_TO2_TO3_TO4
qubit q2_epr_3;
qubit q2_TO4;
bit telept_Zcorrect_q2_3;
bit telept_Xcorrect_q2_3;
reset q2_epr_3;
reset q2_TO4;
h q2_epr_3;
cx q2_epr_3, q2_TO4;
cx q[2], q2_epr_3;
h q[2];
telept_Zcorrect_q2_3 = measure q[2];
telept_Xcorrect_q2_3 = measure q2_epr_3;
if(telept_Zcorrect_q2_3) z q2_TO4;
if(telept_Xcorrect_q2_3) x q2_TO4;
// q[2] teleported into q2_TO4
out[0] = measure q0_TO2_TO3_TO4;
out[1] = measure q1_TO2_TO3_TO4;
out[2] = measure q2_TO4;