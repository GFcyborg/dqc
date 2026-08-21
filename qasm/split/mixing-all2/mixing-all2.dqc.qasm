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
reset q_b[0];
reset q_b[1];
reset q_b[2];
reset q_b[3];
h q_b[0];
measure q_b[0] -> c_b0;
if (c_b0) { rz(pi / 2) q_b[1]; }
h q_b[1];
measure q_b[1] -> c_b1;
if (c_b0) { rz(pi / 4) q_b[2]; }
if (!c_b1) { x q_b[2]; }
my_cphase(pi / 2) q_b[2], q_b[3];
h q_b[2];
measure q_b[2] -> c_b2;
  x q_b[3];
h q_b[3];
measure q_b[3] -> c_b3;
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
reset cin;
reset aa[0];
reset aa[1];
reset bb[0];
reset bb[1];
reset cout;
  x aa[0];
  x bb[0];
  x bb[1];
majority cin[0], bb[0], aa[0];
majority aa[0], bb[0 + 1], aa[0 + 1];
cx aa[1], cout[0];
/* Teleporting qubits into chunk 2:
 * aa[0] from chunk 1
 * aa[1] from chunk 1
 * bb[0] from chunk 1
 * bb[1] from chunk 1
 * cin[0] from chunk 1
 * cout[0] from chunk 1
 */
qubit aa0_epr_1;
qubit aa0_TO2;
bit telept_Zcorrect_aa0_1;
bit telept_Xcorrect_aa0_1;
reset aa0_epr_1;
reset aa0_TO2;
h aa0_epr_1;
cx aa0_epr_1, aa0_TO2;
cx aa[0], aa0_epr_1;
h aa[0];
telept_Zcorrect_aa0_1 = measure aa[0];
telept_Xcorrect_aa0_1 = measure aa0_epr_1;
if(telept_Zcorrect_aa0_1) z aa0_TO2;
if(telept_Xcorrect_aa0_1) x aa0_TO2;
// aa[0] teleported into aa0_TO2
qubit aa1_epr_1;
qubit aa1_TO2;
bit telept_Zcorrect_aa1_1;
bit telept_Xcorrect_aa1_1;
reset aa1_epr_1;
reset aa1_TO2;
h aa1_epr_1;
cx aa1_epr_1, aa1_TO2;
cx aa[1], aa1_epr_1;
h aa[1];
telept_Zcorrect_aa1_1 = measure aa[1];
telept_Xcorrect_aa1_1 = measure aa1_epr_1;
if(telept_Zcorrect_aa1_1) z aa1_TO2;
if(telept_Xcorrect_aa1_1) x aa1_TO2;
// aa[1] teleported into aa1_TO2
qubit bb0_epr_1;
qubit bb0_TO2;
bit telept_Zcorrect_bb0_1;
bit telept_Xcorrect_bb0_1;
reset bb0_epr_1;
reset bb0_TO2;
h bb0_epr_1;
cx bb0_epr_1, bb0_TO2;
cx bb[0], bb0_epr_1;
h bb[0];
telept_Zcorrect_bb0_1 = measure bb[0];
telept_Xcorrect_bb0_1 = measure bb0_epr_1;
if(telept_Zcorrect_bb0_1) z bb0_TO2;
if(telept_Xcorrect_bb0_1) x bb0_TO2;
// bb[0] teleported into bb0_TO2
qubit bb1_epr_1;
qubit bb1_TO2;
bit telept_Zcorrect_bb1_1;
bit telept_Xcorrect_bb1_1;
reset bb1_epr_1;
reset bb1_TO2;
h bb1_epr_1;
cx bb1_epr_1, bb1_TO2;
cx bb[1], bb1_epr_1;
h bb[1];
telept_Zcorrect_bb1_1 = measure bb[1];
telept_Xcorrect_bb1_1 = measure bb1_epr_1;
if(telept_Zcorrect_bb1_1) z bb1_TO2;
if(telept_Xcorrect_bb1_1) x bb1_TO2;
// bb[1] teleported into bb1_TO2
qubit cin0_epr_1;
qubit cin0_TO2;
bit telept_Zcorrect_cin0_1;
bit telept_Xcorrect_cin0_1;
reset cin0_epr_1;
reset cin0_TO2;
h cin0_epr_1;
cx cin0_epr_1, cin0_TO2;
cx cin[0], cin0_epr_1;
h cin[0];
telept_Zcorrect_cin0_1 = measure cin[0];
telept_Xcorrect_cin0_1 = measure cin0_epr_1;
if(telept_Zcorrect_cin0_1) z cin0_TO2;
if(telept_Xcorrect_cin0_1) x cin0_TO2;
// cin[0] teleported into cin0_TO2
qubit cout0_epr_1;
qubit cout0_TO2;
bit telept_Zcorrect_cout0_1;
bit telept_Xcorrect_cout0_1;
reset cout0_epr_1;
reset cout0_TO2;
h cout0_epr_1;
cx cout0_epr_1, cout0_TO2;
cx cout[0], cout0_epr_1;
h cout[0];
telept_Zcorrect_cout0_1 = measure cout[0];
telept_Xcorrect_cout0_1 = measure cout0_epr_1;
if(telept_Zcorrect_cout0_1) z cout0_TO2;
if(telept_Xcorrect_cout0_1) x cout0_TO2;
// cout[0] teleported into cout0_TO2
unmaj aa0_TO2, bb[0 + 1], aa[0 + 1];
unmaj cin0_TO2, bb0_TO2, aa0_TO2;
measure bb0_TO2 -> ans[0];
measure bb1_TO2 -> ans[1];
measure cout0_TO2 -> ans[2];
qubit[3] q_extra;
bit[3] c_extra;
h q_extra[0];
cx q_extra[0], q_extra[1];
cx q_extra[1], q_extra[2];
// pragma dqc.test "informational pragma for rule #99 coverage";
c_extra[0] = measure q_extra[0];
c_extra[1] = measure q_extra[1];
c_extra[2] = measure q_extra[2];