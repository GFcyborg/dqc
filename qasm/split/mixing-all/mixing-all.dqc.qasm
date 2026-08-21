OPENQASM 3.0;
include "stdgates.inc";
gate my_cphase(θ) a, b {
  U(0, 0, θ / 2) a;
  cx a, b;
  U(0, 0, -θ / 2) b;
  cx a, b;
  U(0, 0, θ / 2) b;
}
gate my_gate(a) c, t {
  gphase(a / 2);
  ry(a) c;
  cx c, t;
}
gate my_phase(a) c {
  ctrl @ inv @ gphase(a) c;
}
gate majority a, b, c {
    cx c, b;
    cx c, a;
    ccx a, b, c;
}
gate unmaj a, b, c {
    ccx a, b, c;
    cx c, a;
    cx a, b;
}
gate post q { }
qubit[2] q_bell;
bit[2] c_bell;
h q_bell[0];
cx q_bell[0], q_bell[1];
c_bell[0] = measure q_bell[0];
c_bell[1] = measure q_bell[1];
qubit[3] q_tel;
bit c_tel0;
bit c_tel1;
bit c_tel2;
reset q_tel[0];
reset q_tel[1];
reset q_tel[2];
U(0.3, 0.2, 0.1) q_tel[0];
h q_tel[1];
cx q_tel[1], q_tel[2];
barrier q_tel[0], q_tel[1], q_tel[2];
cx q_tel[0], q_tel[1];
h q_tel[0];
c_tel0 = measure q_tel[0];
c_tel1 = measure q_tel[1];
if (c_tel0) z q_tel[2];
if (c_tel1) { x q_tel[2]; }
post q_tel[2];
c_tel2 = measure q_tel[2];
reset q_tel[0];
reset q_tel[1];
my_gate(pi / 3) q_tel[0], q_tel[1];
my_phase(pi / 4 - pi / 2) q_tel[1];
qubit[4] q_qft;
bit c_qft0;
bit c_qft1;
bit c_qft2;
bit c_qft3;
reset q_qft[0];
reset q_qft[1];
reset q_qft[2];
reset q_qft[3];
h q_qft[0];
measure q_qft[0] -> c_qft0;
if (c_qft0) { rz(pi / 2) q_qft[1]; }
h q_qft[1];
measure q_qft[1] -> c_qft1;
if (c_qft0) { rz(pi / 4) q_qft[2]; }
if (c_qft1) { rz(pi / 2) q_qft[2]; }
h q_qft[2];
measure q_qft[2] -> c_qft2;
if (!c_qft0) { x q_qft[3]; }
my_cphase(pi / 2) q_qft[2], q_qft[3];
h q_qft[3];
measure q_qft[3] -> c_qft3;
qubit[4] q_dj;
bit[4] c_dj;
x q_dj[3];
h q_dj[3];
/* Teleporting qubits into chunk 2:
 * q_dj[0] from chunk 1
 * q_dj[1] from chunk 1
 * q_dj[2] from chunk 1
 * q_dj[3] from chunk 1
 */
qubit q_dj0_epr_1;
qubit q_dj0_TO2;
bit telept_Zcorrect_q_dj0_1;
bit telept_Xcorrect_q_dj0_1;
reset q_dj0_epr_1;
reset q_dj0_TO2;
h q_dj0_epr_1;
cx q_dj0_epr_1, q_dj0_TO2;
cx q_dj[0], q_dj0_epr_1;
h q_dj[0];
telept_Zcorrect_q_dj0_1 = measure q_dj[0];
telept_Xcorrect_q_dj0_1 = measure q_dj0_epr_1;
if(telept_Zcorrect_q_dj0_1) z q_dj0_TO2;
if(telept_Xcorrect_q_dj0_1) x q_dj0_TO2;
// q_dj[0] teleported into q_dj0_TO2
qubit q_dj1_epr_1;
qubit q_dj1_TO2;
bit telept_Zcorrect_q_dj1_1;
bit telept_Xcorrect_q_dj1_1;
reset q_dj1_epr_1;
reset q_dj1_TO2;
h q_dj1_epr_1;
cx q_dj1_epr_1, q_dj1_TO2;
cx q_dj[1], q_dj1_epr_1;
h q_dj[1];
telept_Zcorrect_q_dj1_1 = measure q_dj[1];
telept_Xcorrect_q_dj1_1 = measure q_dj1_epr_1;
if(telept_Zcorrect_q_dj1_1) z q_dj1_TO2;
if(telept_Xcorrect_q_dj1_1) x q_dj1_TO2;
// q_dj[1] teleported into q_dj1_TO2
qubit q_dj2_epr_1;
qubit q_dj2_TO2;
bit telept_Zcorrect_q_dj2_1;
bit telept_Xcorrect_q_dj2_1;
reset q_dj2_epr_1;
reset q_dj2_TO2;
h q_dj2_epr_1;
cx q_dj2_epr_1, q_dj2_TO2;
cx q_dj[2], q_dj2_epr_1;
h q_dj[2];
telept_Zcorrect_q_dj2_1 = measure q_dj[2];
telept_Xcorrect_q_dj2_1 = measure q_dj2_epr_1;
if(telept_Zcorrect_q_dj2_1) z q_dj2_TO2;
if(telept_Xcorrect_q_dj2_1) x q_dj2_TO2;
// q_dj[2] teleported into q_dj2_TO2
qubit q_dj3_epr_1;
qubit q_dj3_TO2;
bit telept_Zcorrect_q_dj3_1;
bit telept_Xcorrect_q_dj3_1;
reset q_dj3_epr_1;
reset q_dj3_TO2;
h q_dj3_epr_1;
cx q_dj3_epr_1, q_dj3_TO2;
cx q_dj[3], q_dj3_epr_1;
h q_dj[3];
telept_Zcorrect_q_dj3_1 = measure q_dj[3];
telept_Xcorrect_q_dj3_1 = measure q_dj3_epr_1;
if(telept_Zcorrect_q_dj3_1) z q_dj3_TO2;
if(telept_Xcorrect_q_dj3_1) x q_dj3_TO2;
// q_dj[3] teleported into q_dj3_TO2
h q_dj0_TO2;
h q_dj1_TO2;
h q_dj2_TO2;
barrier q_dj0_TO2, q_dj1_TO2, q_dj2_TO2, q_dj3_TO2;
x q_dj2_TO2;
ctrl(3) @ x q_dj0_TO2, q_dj1_TO2, q_dj2_TO2, q_dj3_TO2;
x q_dj2_TO2;
barrier q_dj0_TO2, q_dj1_TO2, q_dj2_TO2, q_dj3_TO2;
x q_dj[{0, 2}];
h q_dj0_TO2;
h q_dj1_TO2;
h q_dj2_TO2;
c_dj[0] = measure q_dj0_TO2;
c_dj[1] = measure q_dj1_TO2;
c_dj[2] = measure q_dj2_TO2;
c_dj[3] = measure q_dj3_TO2;
qubit[4] q_bv;
bit[3] c_bv;
x q_bv[3];
h q_bv[3];
h q_bv[0];
h q_bv[1];
h q_bv[2];
cx q_bv[3], q_bv[0];
cx q_bv[3], q_bv[2];
h q_bv[0];
h q_bv[1];
h q_bv[2];
c_bv[0] = measure q_bv[0];
c_bv[1] = measure q_bv[1];
c_bv[2] = measure q_bv[2];
qubit[1] cin;
qubit[2] a;
qubit[2] b;
qubit[1] cout;
bit[3] ans;
reset cin;
reset a[0];
reset a[1];
reset b[0];
reset b[1];
reset cout;
  x a[0];
  x b[0];
  x b[1];
majority cin[0], b[0], a[0];
majority a[0], b[0 + 1], a[0 + 1];
cx a[1], cout[0];
unmaj a[0], b[0 + 1], a[0 + 1];
unmaj cin[0], b[0], a[0];
measure b[0] -> ans[0];
measure b[1] -> ans[1];
measure cout[0] -> ans[2];
qubit[2] q_rb;
bit[2] c_rb;
reset q_rb[0];
reset q_rb[1];
h q_rb[0];
barrier q_rb[0], q_rb[1];
cz q_rb[0], q_rb[1];
barrier q_rb[0], q_rb[1];
s q_rb[0];
cz q_rb[0], q_rb[1];
barrier q_rb[0], q_rb[1];
/* Teleporting qubits into chunk 3:
 * q_rb[0] from chunk 2
 * q_rb[1] from chunk 2
 */
qubit q_rb0_epr_2;
qubit q_rb0_TO3;
bit telept_Zcorrect_q_rb0_2;
bit telept_Xcorrect_q_rb0_2;
reset q_rb0_epr_2;
reset q_rb0_TO3;
h q_rb0_epr_2;
cx q_rb0_epr_2, q_rb0_TO3;
cx q_rb[0], q_rb0_epr_2;
h q_rb[0];
telept_Zcorrect_q_rb0_2 = measure q_rb[0];
telept_Xcorrect_q_rb0_2 = measure q_rb0_epr_2;
if(telept_Zcorrect_q_rb0_2) z q_rb0_TO3;
if(telept_Xcorrect_q_rb0_2) x q_rb0_TO3;
// q_rb[0] teleported into q_rb0_TO3
qubit q_rb1_epr_2;
qubit q_rb1_TO3;
bit telept_Zcorrect_q_rb1_2;
bit telept_Xcorrect_q_rb1_2;
reset q_rb1_epr_2;
reset q_rb1_TO3;
h q_rb1_epr_2;
cx q_rb1_epr_2, q_rb1_TO3;
cx q_rb[1], q_rb1_epr_2;
h q_rb[1];
telept_Zcorrect_q_rb1_2 = measure q_rb[1];
telept_Xcorrect_q_rb1_2 = measure q_rb1_epr_2;
if(telept_Zcorrect_q_rb1_2) z q_rb1_TO3;
if(telept_Xcorrect_q_rb1_2) x q_rb1_TO3;
// q_rb[1] teleported into q_rb1_TO3
s q_rb0_TO3;
z q_rb0_TO3;
h q_rb0_TO3;
barrier q_rb0_TO3, q_rb1_TO3;
measure q_rb0_TO3 -> c_rb[0];
measure q_rb1_TO3 -> c_rb[1];