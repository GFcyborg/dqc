/*
 * quantum ripple-carry adder
 * Cuccaro et al, quant-ph/0410184
 */
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
uint[4] a_in = 1;  // a = 0001
uint[4] b_in = 15; // b = 1111
// initialize qubits
reset cin;
reset a;
reset b;
reset cout;
/* Teleporting qubits into chunk 2:
 * a[0] from chunk 1
 * a[3] from chunk 1
 * b[0] from chunk 1
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

// set input states
for uint i in [0: 3] {
  if(bool(a_in[i])) x a[i];
  if(bool(b_in[i])) x b[i];
}
// add a to b, storing result in b
majority cin[0], b[0], a[0];
for uint i in [0: 2] { majority a[i], b[i + 1], a[i + 1]; }
cx a[3], cout[0];
/* Teleporting qubits into chunk 3:
 * a[0] from chunk 2
 * b[0] from chunks 1, 2
 * b[1] from chunk 1
 * b[2] from chunk 1
 * b[3] from chunk 1
 * cin[0] from chunk 2
 * cout[0] from chunk 2
 */
qubit a0_epr_2;
qubit a0_epr_TARGET_2;
bit telept_Zcorrect_a0_2;
bit telept_Xcorrect_a0_2;
reset a0_epr_2;
reset a0_epr_TARGET_2;
h a0_epr_2;
cx a0_epr_2, a0_epr_TARGET_2;
cx a[0], a0_epr_2;
h a[0];
telept_Zcorrect_a0_2 = measure a[0];
telept_Xcorrect_a0_2 = measure a0_epr_2;
if(telept_Zcorrect_a0_2) z a0_epr_TARGET_2;
if(telept_Xcorrect_a0_2) x a0_epr_TARGET_2;
// a[0] teleported into a0_epr_TARGET_2
qubit b0_epr_2;
qubit b0_epr_TARGET_2;
bit telept_Zcorrect_b0_2;
bit telept_Xcorrect_b0_2;
reset b0_epr_2;
reset b0_epr_TARGET_2;
h b0_epr_2;
cx b0_epr_2, b0_epr_TARGET_2;
cx b[0], b0_epr_2;
h b[0];
telept_Zcorrect_b0_2 = measure b[0];
telept_Xcorrect_b0_2 = measure b0_epr_2;
if(telept_Zcorrect_b0_2) z b0_epr_TARGET_2;
if(telept_Xcorrect_b0_2) x b0_epr_TARGET_2;
// b[0] teleported into b0_epr_TARGET_2
qubit b1_epr_2;
qubit b1_epr_TARGET_2;
bit telept_Zcorrect_b1_2;
bit telept_Xcorrect_b1_2;
reset b1_epr_2;
reset b1_epr_TARGET_2;
h b1_epr_2;
cx b1_epr_2, b1_epr_TARGET_2;
cx b[1], b1_epr_2;
h b[1];
telept_Zcorrect_b1_2 = measure b[1];
telept_Xcorrect_b1_2 = measure b1_epr_2;
if(telept_Zcorrect_b1_2) z b1_epr_TARGET_2;
if(telept_Xcorrect_b1_2) x b1_epr_TARGET_2;
// b[1] teleported into b1_epr_TARGET_2
qubit b2_epr_2;
qubit b2_epr_TARGET_2;
bit telept_Zcorrect_b2_2;
bit telept_Xcorrect_b2_2;
reset b2_epr_2;
reset b2_epr_TARGET_2;
h b2_epr_2;
cx b2_epr_2, b2_epr_TARGET_2;
cx b[2], b2_epr_2;
h b[2];
telept_Zcorrect_b2_2 = measure b[2];
telept_Xcorrect_b2_2 = measure b2_epr_2;
if(telept_Zcorrect_b2_2) z b2_epr_TARGET_2;
if(telept_Xcorrect_b2_2) x b2_epr_TARGET_2;
// b[2] teleported into b2_epr_TARGET_2
qubit b3_epr_2;
qubit b3_epr_TARGET_2;
bit telept_Zcorrect_b3_2;
bit telept_Xcorrect_b3_2;
reset b3_epr_2;
reset b3_epr_TARGET_2;
h b3_epr_2;
cx b3_epr_2, b3_epr_TARGET_2;
cx b[3], b3_epr_2;
h b[3];
telept_Zcorrect_b3_2 = measure b[3];
telept_Xcorrect_b3_2 = measure b3_epr_2;
if(telept_Zcorrect_b3_2) z b3_epr_TARGET_2;
if(telept_Xcorrect_b3_2) x b3_epr_TARGET_2;
// b[3] teleported into b3_epr_TARGET_2
qubit cin0_epr_2;
qubit cin0_epr_TARGET_2;
bit telept_Zcorrect_cin0_2;
bit telept_Xcorrect_cin0_2;
reset cin0_epr_2;
reset cin0_epr_TARGET_2;
h cin0_epr_2;
cx cin0_epr_2, cin0_epr_TARGET_2;
cx cin[0], cin0_epr_2;
h cin[0];
telept_Zcorrect_cin0_2 = measure cin[0];
telept_Xcorrect_cin0_2 = measure cin0_epr_2;
if(telept_Zcorrect_cin0_2) z cin0_epr_TARGET_2;
if(telept_Xcorrect_cin0_2) x cin0_epr_TARGET_2;
// cin[0] teleported into cin0_epr_TARGET_2
qubit cout0_epr_2;
qubit cout0_epr_TARGET_2;
bit telept_Zcorrect_cout0_2;
bit telept_Xcorrect_cout0_2;
reset cout0_epr_2;
reset cout0_epr_TARGET_2;
h cout0_epr_2;
cx cout0_epr_2, cout0_epr_TARGET_2;
cx cout[0], cout0_epr_2;
h cout[0];
telept_Zcorrect_cout0_2 = measure cout[0];
telept_Xcorrect_cout0_2 = measure cout0_epr_2;
if(telept_Zcorrect_cout0_2) z cout0_epr_TARGET_2;
if(telept_Xcorrect_cout0_2) x cout0_epr_TARGET_2;
// cout[0] teleported into cout0_epr_TARGET_2
for uint i in [2: -1: 0] { unmaj a[i],b[i+1],a[i+1]; }
unmaj cin[0], b[0], a[0];
measure b[0:3] -> ans[0:3];
measure cout[0] -> ans[4];