OPENQASM 3.1;
include "stdgates.inc";
input float[64] a;
input float[64] b;
qubit[3] q_qe;
bit[2] mid;
bit[3] out;
gate my_gate(a, b) c, t {
  gphase(a / 2);
  ry(a) c;
  rz(b) c;
  cx c, t;
}
gate my_phase(a) c {
  ctrl @ inv @ gphase(a) c;
}
my_gate(a * 2, b) q_qe[0], q_qe[1];
measure q_qe[0] -> mid[0];
measure q_qe[1] -> mid[1];
while (mid == "00") {
  reset q_qe[0];
  reset q_qe[1];
  my_gate(a, b) q_qe[0], q_qe[1];
  my_phase(a - pi / 2) q_qe[1];
  mid[0] = measure q_qe[0];
  mid[1] = measure q_qe[1];
}
if (mid[0]) {
  reset q_qe[0];
  reset q_qe[1];
}
out[0] = measure q_qe[0];
out[1] = measure q_qe[1];
out[2] = measure q_qe[2];
gate my_cphase(θ) x, y {
  U(0, 0, θ / 2) x;
  cx x, y;
  U(0, 0, -θ / 2) y;
  cx x, y;
  U(0, 0, θ / 2) y;
}
qubit[4] q_b;
bit c_b0;
bit c_b1;
bit c_b2;
bit c_b3;
/* Teleporting qubits into chunk 2:
 * q_b[0] from chunk 1
 * q_b[1] from chunk 1
 * q_b[2] from chunk 1
 * q_b[3] from chunk 1
 */
qubit q_b0_epr_1;
qubit q_b0_TO2;
bit telept_Zcorrect_q_b0_1;
bit telept_Xcorrect_q_b0_1;
reset q_b0_epr_1;
reset q_b0_TO2;
h q_b0_epr_1;
cx q_b0_epr_1, q_b0_TO2;
cx q_b[0], q_b0_epr_1;
h q_b[0];
telept_Zcorrect_q_b0_1 = measure q_b[0];
telept_Xcorrect_q_b0_1 = measure q_b0_epr_1;
if(telept_Zcorrect_q_b0_1) z q_b0_TO2;
if(telept_Xcorrect_q_b0_1) x q_b0_TO2;
// q_b[0] teleported into q_b0_TO2
qubit q_b1_epr_1;
qubit q_b1_TO2;
bit telept_Zcorrect_q_b1_1;
bit telept_Xcorrect_q_b1_1;
reset q_b1_epr_1;
reset q_b1_TO2;
h q_b1_epr_1;
cx q_b1_epr_1, q_b1_TO2;
cx q_b[1], q_b1_epr_1;
h q_b[1];
telept_Zcorrect_q_b1_1 = measure q_b[1];
telept_Xcorrect_q_b1_1 = measure q_b1_epr_1;
if(telept_Zcorrect_q_b1_1) z q_b1_TO2;
if(telept_Xcorrect_q_b1_1) x q_b1_TO2;
// q_b[1] teleported into q_b1_TO2
qubit q_b2_epr_1;
qubit q_b2_TO2;
bit telept_Zcorrect_q_b2_1;
bit telept_Xcorrect_q_b2_1;
reset q_b2_epr_1;
reset q_b2_TO2;
h q_b2_epr_1;
cx q_b2_epr_1, q_b2_TO2;
cx q_b[2], q_b2_epr_1;
h q_b[2];
telept_Zcorrect_q_b2_1 = measure q_b[2];
telept_Xcorrect_q_b2_1 = measure q_b2_epr_1;
if(telept_Zcorrect_q_b2_1) z q_b2_TO2;
if(telept_Xcorrect_q_b2_1) x q_b2_TO2;
// q_b[2] teleported into q_b2_TO2
qubit q_b3_epr_1;
qubit q_b3_TO2;
bit telept_Zcorrect_q_b3_1;
bit telept_Xcorrect_q_b3_1;
reset q_b3_epr_1;
reset q_b3_TO2;
h q_b3_epr_1;
cx q_b3_epr_1, q_b3_TO2;
cx q_b[3], q_b3_epr_1;
h q_b[3];
telept_Zcorrect_q_b3_1 = measure q_b[3];
telept_Xcorrect_q_b3_1 = measure q_b3_epr_1;
if(telept_Zcorrect_q_b3_1) z q_b3_TO2;
if(telept_Xcorrect_q_b3_1) x q_b3_TO2;
// q_b[3] teleported into q_b3_TO2
reset q_b0_TO2;
reset q_b1_TO2;
reset q_b2_TO2;
reset q_b3_TO2;
h q_b0_TO2;
measure q_b0_TO2 -> c_b0;
if (c_b0) { rz(pi / 2) q_b1_TO2; }
h q_b1_TO2;
measure q_b1_TO2 -> c_b1;
if (c_b0) { rz(pi / 4) q_b2_TO2; }
if (!c_b1) { x q_b2_TO2; }
my_cphase(pi / 2) q_b2_TO2, q_b3_TO2;
h q_b2_TO2;
measure q_b2_TO2 -> c_b2;
  x q_b3_TO2;
/* Teleporting qubits into chunk 3:
 * q_b3_TO2 from chunk 2
 */
qubit q_b3_TO2_epr_2;
qubit q_b3_TO2_TO3;
bit telept_Zcorrect_q_b3_TO2_2;
bit telept_Xcorrect_q_b3_TO2_2;
reset q_b3_TO2_epr_2;
reset q_b3_TO2_TO3;
h q_b3_TO2_epr_2;
cx q_b3_TO2_epr_2, q_b3_TO2_TO3;
cx q_b3_TO2, q_b3_TO2_epr_2;
h q_b3_TO2;
telept_Zcorrect_q_b3_TO2_2 = measure q_b3_TO2;
telept_Xcorrect_q_b3_TO2_2 = measure q_b3_TO2_epr_2;
if(telept_Zcorrect_q_b3_TO2_2) z q_b3_TO2_TO3;
if(telept_Xcorrect_q_b3_TO2_2) x q_b3_TO2_TO3;
// q_b3_TO2 teleported into q_b3_TO2_TO3
h q_b3_TO2_TO3;
measure q_b3_TO2_TO3 -> c_b3;
gate majority x, y, z {
    cx z, y;
    cx z, x;
    ccx x, y, z;
}
gate unmaj x, y, z {
    ccx x, y, z;
    cx z, x;
    cx x, y;
}
qubit[1] cin;
qubit[2] aa;
qubit[2] bb;
qubit[1] cout;
bit[3] ans;
/* Teleporting qubits into chunk 4:
 * aa[0] from chunk 3
 * aa[1] from chunk 3
 * bb[0] from chunk 3
 * bb[1] from chunk 3
 * cin from chunk 3
 * cout from chunk 3
 */
qubit aa0_epr_3;
qubit aa0_TO4;
bit telept_Zcorrect_aa0_3;
bit telept_Xcorrect_aa0_3;
reset aa0_epr_3;
reset aa0_TO4;
h aa0_epr_3;
cx aa0_epr_3, aa0_TO4;
cx aa[0], aa0_epr_3;
h aa[0];
telept_Zcorrect_aa0_3 = measure aa[0];
telept_Xcorrect_aa0_3 = measure aa0_epr_3;
if(telept_Zcorrect_aa0_3) z aa0_TO4;
if(telept_Xcorrect_aa0_3) x aa0_TO4;
// aa[0] teleported into aa0_TO4
qubit aa1_epr_3;
qubit aa1_TO4;
bit telept_Zcorrect_aa1_3;
bit telept_Xcorrect_aa1_3;
reset aa1_epr_3;
reset aa1_TO4;
h aa1_epr_3;
cx aa1_epr_3, aa1_TO4;
cx aa[1], aa1_epr_3;
h aa[1];
telept_Zcorrect_aa1_3 = measure aa[1];
telept_Xcorrect_aa1_3 = measure aa1_epr_3;
if(telept_Zcorrect_aa1_3) z aa1_TO4;
if(telept_Xcorrect_aa1_3) x aa1_TO4;
// aa[1] teleported into aa1_TO4
qubit bb0_epr_3;
qubit bb0_TO4;
bit telept_Zcorrect_bb0_3;
bit telept_Xcorrect_bb0_3;
reset bb0_epr_3;
reset bb0_TO4;
h bb0_epr_3;
cx bb0_epr_3, bb0_TO4;
cx bb[0], bb0_epr_3;
h bb[0];
telept_Zcorrect_bb0_3 = measure bb[0];
telept_Xcorrect_bb0_3 = measure bb0_epr_3;
if(telept_Zcorrect_bb0_3) z bb0_TO4;
if(telept_Xcorrect_bb0_3) x bb0_TO4;
// bb[0] teleported into bb0_TO4
qubit bb1_epr_3;
qubit bb1_TO4;
bit telept_Zcorrect_bb1_3;
bit telept_Xcorrect_bb1_3;
reset bb1_epr_3;
reset bb1_TO4;
h bb1_epr_3;
cx bb1_epr_3, bb1_TO4;
cx bb[1], bb1_epr_3;
h bb[1];
telept_Zcorrect_bb1_3 = measure bb[1];
telept_Xcorrect_bb1_3 = measure bb1_epr_3;
if(telept_Zcorrect_bb1_3) z bb1_TO4;
if(telept_Xcorrect_bb1_3) x bb1_TO4;
// bb[1] teleported into bb1_TO4
qubit cin_epr_3;
qubit cin_TO4;
bit telept_Zcorrect_cin_3;
bit telept_Xcorrect_cin_3;
reset cin_epr_3;
reset cin_TO4;
h cin_epr_3;
cx cin_epr_3, cin_TO4;
cx cin, cin_epr_3;
h cin;
telept_Zcorrect_cin_3 = measure cin;
telept_Xcorrect_cin_3 = measure cin_epr_3;
if(telept_Zcorrect_cin_3) z cin_TO4;
if(telept_Xcorrect_cin_3) x cin_TO4;
// cin teleported into cin_TO4
qubit cout_epr_3;
qubit cout_TO4;
bit telept_Zcorrect_cout_3;
bit telept_Xcorrect_cout_3;
reset cout_epr_3;
reset cout_TO4;
h cout_epr_3;
cx cout_epr_3, cout_TO4;
cx cout, cout_epr_3;
h cout;
telept_Zcorrect_cout_3 = measure cout;
telept_Xcorrect_cout_3 = measure cout_epr_3;
if(telept_Zcorrect_cout_3) z cout_TO4;
if(telept_Xcorrect_cout_3) x cout_TO4;
// cout teleported into cout_TO4
reset cin_TO4;
reset aa0_TO4;
reset aa1_TO4;
reset bb0_TO4;
reset bb1_TO4;
reset cout_TO4;
  x aa0_TO4;
  x bb0_TO4;
  x bb1_TO4;
majority cin_TO4[0], bb0_TO4, aa0_TO4;
majority aa0_TO4, bb[0 + 1], aa[0 + 1];
cx aa1_TO4, cout_TO4[0];
unmaj aa0_TO4, bb[0 + 1], aa[0 + 1];
unmaj cin_TO4[0], bb0_TO4, aa0_TO4;
measure bb0_TO4 -> ans[0];
measure bb1_TO4 -> ans[1];
measure cout_TO4[0] -> ans[2];
qubit[3] q_extra;
bit[3] c_extra;
/* Teleporting qubits into chunk 5:
 * q_extra[0] from chunk 4
 * q_extra[1] from chunk 4
 * q_extra[2] from chunk 4
 */
qubit q_extra0_epr_4;
qubit q_extra0_TO5;
bit telept_Zcorrect_q_extra0_4;
bit telept_Xcorrect_q_extra0_4;
reset q_extra0_epr_4;
reset q_extra0_TO5;
h q_extra0_epr_4;
cx q_extra0_epr_4, q_extra0_TO5;
cx q_extra[0], q_extra0_epr_4;
h q_extra[0];
telept_Zcorrect_q_extra0_4 = measure q_extra[0];
telept_Xcorrect_q_extra0_4 = measure q_extra0_epr_4;
if(telept_Zcorrect_q_extra0_4) z q_extra0_TO5;
if(telept_Xcorrect_q_extra0_4) x q_extra0_TO5;
// q_extra[0] teleported into q_extra0_TO5
qubit q_extra1_epr_4;
qubit q_extra1_TO5;
bit telept_Zcorrect_q_extra1_4;
bit telept_Xcorrect_q_extra1_4;
reset q_extra1_epr_4;
reset q_extra1_TO5;
h q_extra1_epr_4;
cx q_extra1_epr_4, q_extra1_TO5;
cx q_extra[1], q_extra1_epr_4;
h q_extra[1];
telept_Zcorrect_q_extra1_4 = measure q_extra[1];
telept_Xcorrect_q_extra1_4 = measure q_extra1_epr_4;
if(telept_Zcorrect_q_extra1_4) z q_extra1_TO5;
if(telept_Xcorrect_q_extra1_4) x q_extra1_TO5;
// q_extra[1] teleported into q_extra1_TO5
qubit q_extra2_epr_4;
qubit q_extra2_TO5;
bit telept_Zcorrect_q_extra2_4;
bit telept_Xcorrect_q_extra2_4;
reset q_extra2_epr_4;
reset q_extra2_TO5;
h q_extra2_epr_4;
cx q_extra2_epr_4, q_extra2_TO5;
cx q_extra[2], q_extra2_epr_4;
h q_extra[2];
telept_Zcorrect_q_extra2_4 = measure q_extra[2];
telept_Xcorrect_q_extra2_4 = measure q_extra2_epr_4;
if(telept_Zcorrect_q_extra2_4) z q_extra2_TO5;
if(telept_Xcorrect_q_extra2_4) x q_extra2_TO5;
// q_extra[2] teleported into q_extra2_TO5
h q_extra0_TO5;
cx q_extra0_TO5, q_extra1_TO5;
cx q_extra1_TO5, q_extra2_TO5;
// pragma dqc.test "informational pragma for rule #99 coverage";
c_extra[0] = measure q_extra0_TO5;
c_extra[1] = measure q_extra1_TO5;
c_extra[2] = measure q_extra2_TO5;