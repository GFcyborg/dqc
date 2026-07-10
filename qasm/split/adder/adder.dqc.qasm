OPENQASM 3.1;
include "stdgates.inc";
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
qubit[1] cin;
qubit[4] a;
qubit[4] b;
qubit[1] cout;
bit[5] ans;
reset cin;
reset a[0];
reset a[1];
reset a[2];
reset a[3];
reset b[0];
reset b[1];
reset b[2];
reset b[3];
reset cout;
  x a[0];
  x b[0];
  x b[1];
  x b[2];
  x b[3];
/* Teleporting qubits into chunk 2:
 * a[0] from chunk 1
 * a[1] from chunk 1
 * a[2] from chunk 1
 * a[3] from chunk 1
 * b[0] from chunk 1
 * b[1] from chunk 1
 * b[2] from chunk 1
 * b[3] from chunk 1
 * cin[0] from chunk 1
 * cout[0] from chunk 1
 */
qubit a0_epr_1;
qubit a0_epr_TARGET_1;
bit telept_Zcorrect_a0_1;
bit telept_Xcorrect_a0_1;
reset a0_epr_1;
reset a0_epr_TARGET_1;
h a0_epr_1;
cx a0_epr_1, a0_epr_TARGET_1;
cx a[0], a0_epr_1;
h a[0];
telept_Zcorrect_a0_1 = measure a[0];
telept_Xcorrect_a0_1 = measure a0_epr_1;
if(telept_Zcorrect_a0_1) z a0_epr_TARGET_1;
if(telept_Xcorrect_a0_1) x a0_epr_TARGET_1;
// a[0] teleported into a0_epr_TARGET_1
qubit a1_epr_1;
qubit a1_epr_TARGET_1;
bit telept_Zcorrect_a1_1;
bit telept_Xcorrect_a1_1;
reset a1_epr_1;
reset a1_epr_TARGET_1;
h a1_epr_1;
cx a1_epr_1, a1_epr_TARGET_1;
cx a[1], a1_epr_1;
h a[1];
telept_Zcorrect_a1_1 = measure a[1];
telept_Xcorrect_a1_1 = measure a1_epr_1;
if(telept_Zcorrect_a1_1) z a1_epr_TARGET_1;
if(telept_Xcorrect_a1_1) x a1_epr_TARGET_1;
// a[1] teleported into a1_epr_TARGET_1
qubit a2_epr_1;
qubit a2_epr_TARGET_1;
bit telept_Zcorrect_a2_1;
bit telept_Xcorrect_a2_1;
reset a2_epr_1;
reset a2_epr_TARGET_1;
h a2_epr_1;
cx a2_epr_1, a2_epr_TARGET_1;
cx a[2], a2_epr_1;
h a[2];
telept_Zcorrect_a2_1 = measure a[2];
telept_Xcorrect_a2_1 = measure a2_epr_1;
if(telept_Zcorrect_a2_1) z a2_epr_TARGET_1;
if(telept_Xcorrect_a2_1) x a2_epr_TARGET_1;
// a[2] teleported into a2_epr_TARGET_1
qubit a3_epr_1;
qubit a3_epr_TARGET_1;
bit telept_Zcorrect_a3_1;
bit telept_Xcorrect_a3_1;
reset a3_epr_1;
reset a3_epr_TARGET_1;
h a3_epr_1;
cx a3_epr_1, a3_epr_TARGET_1;
cx a[3], a3_epr_1;
h a[3];
telept_Zcorrect_a3_1 = measure a[3];
telept_Xcorrect_a3_1 = measure a3_epr_1;
if(telept_Zcorrect_a3_1) z a3_epr_TARGET_1;
if(telept_Xcorrect_a3_1) x a3_epr_TARGET_1;
// a[3] teleported into a3_epr_TARGET_1
qubit b0_epr_1;
qubit b0_epr_TARGET_1;
bit telept_Zcorrect_b0_1;
bit telept_Xcorrect_b0_1;
reset b0_epr_1;
reset b0_epr_TARGET_1;
h b0_epr_1;
cx b0_epr_1, b0_epr_TARGET_1;
cx b[0], b0_epr_1;
h b[0];
telept_Zcorrect_b0_1 = measure b[0];
telept_Xcorrect_b0_1 = measure b0_epr_1;
if(telept_Zcorrect_b0_1) z b0_epr_TARGET_1;
if(telept_Xcorrect_b0_1) x b0_epr_TARGET_1;
// b[0] teleported into b0_epr_TARGET_1
qubit b1_epr_1;
qubit b1_epr_TARGET_1;
bit telept_Zcorrect_b1_1;
bit telept_Xcorrect_b1_1;
reset b1_epr_1;
reset b1_epr_TARGET_1;
h b1_epr_1;
cx b1_epr_1, b1_epr_TARGET_1;
cx b[1], b1_epr_1;
h b[1];
telept_Zcorrect_b1_1 = measure b[1];
telept_Xcorrect_b1_1 = measure b1_epr_1;
if(telept_Zcorrect_b1_1) z b1_epr_TARGET_1;
if(telept_Xcorrect_b1_1) x b1_epr_TARGET_1;
// b[1] teleported into b1_epr_TARGET_1
qubit b2_epr_1;
qubit b2_epr_TARGET_1;
bit telept_Zcorrect_b2_1;
bit telept_Xcorrect_b2_1;
reset b2_epr_1;
reset b2_epr_TARGET_1;
h b2_epr_1;
cx b2_epr_1, b2_epr_TARGET_1;
cx b[2], b2_epr_1;
h b[2];
telept_Zcorrect_b2_1 = measure b[2];
telept_Xcorrect_b2_1 = measure b2_epr_1;
if(telept_Zcorrect_b2_1) z b2_epr_TARGET_1;
if(telept_Xcorrect_b2_1) x b2_epr_TARGET_1;
// b[2] teleported into b2_epr_TARGET_1
qubit b3_epr_1;
qubit b3_epr_TARGET_1;
bit telept_Zcorrect_b3_1;
bit telept_Xcorrect_b3_1;
reset b3_epr_1;
reset b3_epr_TARGET_1;
h b3_epr_1;
cx b3_epr_1, b3_epr_TARGET_1;
cx b[3], b3_epr_1;
h b[3];
telept_Zcorrect_b3_1 = measure b[3];
telept_Xcorrect_b3_1 = measure b3_epr_1;
if(telept_Zcorrect_b3_1) z b3_epr_TARGET_1;
if(telept_Xcorrect_b3_1) x b3_epr_TARGET_1;
// b[3] teleported into b3_epr_TARGET_1
qubit cin0_epr_1;
qubit cin0_epr_TARGET_1;
bit telept_Zcorrect_cin0_1;
bit telept_Xcorrect_cin0_1;
reset cin0_epr_1;
reset cin0_epr_TARGET_1;
h cin0_epr_1;
cx cin0_epr_1, cin0_epr_TARGET_1;
cx cin[0], cin0_epr_1;
h cin[0];
telept_Zcorrect_cin0_1 = measure cin[0];
telept_Xcorrect_cin0_1 = measure cin0_epr_1;
if(telept_Zcorrect_cin0_1) z cin0_epr_TARGET_1;
if(telept_Xcorrect_cin0_1) x cin0_epr_TARGET_1;
// cin[0] teleported into cin0_epr_TARGET_1
qubit cout0_epr_1;
qubit cout0_epr_TARGET_1;
bit telept_Zcorrect_cout0_1;
bit telept_Xcorrect_cout0_1;
reset cout0_epr_1;
reset cout0_epr_TARGET_1;
h cout0_epr_1;
cx cout0_epr_1, cout0_epr_TARGET_1;
cx cout[0], cout0_epr_1;
h cout[0];
telept_Zcorrect_cout0_1 = measure cout[0];
telept_Xcorrect_cout0_1 = measure cout0_epr_1;
if(telept_Zcorrect_cout0_1) z cout0_epr_TARGET_1;
if(telept_Xcorrect_cout0_1) x cout0_epr_TARGET_1;
// cout[0] teleported into cout0_epr_TARGET_1
majority cin[0], b[0], a[0];
majority a[0], b[0 + 1], a[0 + 1];
majority a[1], b[1 + 1], a[1 + 1];
majority a[2], b[2 + 1], a[2 + 1];
// pragma xxx
cx a[3], cout[0];
unmaj a[2],b[2+1],a[2+1];
unmaj a[1],b[1+1],a[1+1];
unmaj a[0],b[0+1],a[0+1];
// pragma xxx
unmaj cin[0], b[0], a[0];
measure b[0] -> ans[0];
measure b[1] -> ans[1];
measure b[2] -> ans[2];
measure b[3] -> ans[3];
measure cout[0] -> ans[4];