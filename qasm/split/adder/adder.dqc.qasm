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
/* Teleporting qubits into chunk 2:
 * no shared qubits from chunk 1
 */
qubit[4] a;
qubit[4] b;
qubit[1] cout;
/* Teleporting qubits into chunk 3:
 * a[0] from chunk 2
 * a[1] from chunk 2
 * a[2] from chunk 2
 * a[3] from chunk 2
 * b[0] from chunk 2
 * b[1] from chunk 2
 * b[2] from chunk 2
 * b[3] from chunk 2
 * cin from chunk 1
 * cout from chunk 2
 */
qubit a0_epr_2;
qubit a0_TO3;
bit telept_Zcorrect_a0_2;
bit telept_Xcorrect_a0_2;
reset a0_epr_2;
reset a0_TO3;
h a0_epr_2;
cx a0_epr_2, a0_TO3;
cx a[0], a0_epr_2;
h a[0];
telept_Zcorrect_a0_2 = measure a[0];
telept_Xcorrect_a0_2 = measure a0_epr_2;
if(telept_Zcorrect_a0_2) z a0_TO3;
if(telept_Xcorrect_a0_2) x a0_TO3;
// a[0] teleported into a0_TO3
qubit a1_epr_2;
qubit a1_TO3;
bit telept_Zcorrect_a1_2;
bit telept_Xcorrect_a1_2;
reset a1_epr_2;
reset a1_TO3;
h a1_epr_2;
cx a1_epr_2, a1_TO3;
cx a[1], a1_epr_2;
h a[1];
telept_Zcorrect_a1_2 = measure a[1];
telept_Xcorrect_a1_2 = measure a1_epr_2;
if(telept_Zcorrect_a1_2) z a1_TO3;
if(telept_Xcorrect_a1_2) x a1_TO3;
// a[1] teleported into a1_TO3
qubit a2_epr_2;
qubit a2_TO3;
bit telept_Zcorrect_a2_2;
bit telept_Xcorrect_a2_2;
reset a2_epr_2;
reset a2_TO3;
h a2_epr_2;
cx a2_epr_2, a2_TO3;
cx a[2], a2_epr_2;
h a[2];
telept_Zcorrect_a2_2 = measure a[2];
telept_Xcorrect_a2_2 = measure a2_epr_2;
if(telept_Zcorrect_a2_2) z a2_TO3;
if(telept_Xcorrect_a2_2) x a2_TO3;
// a[2] teleported into a2_TO3
qubit a3_epr_2;
qubit a3_TO3;
bit telept_Zcorrect_a3_2;
bit telept_Xcorrect_a3_2;
reset a3_epr_2;
reset a3_TO3;
h a3_epr_2;
cx a3_epr_2, a3_TO3;
cx a[3], a3_epr_2;
h a[3];
telept_Zcorrect_a3_2 = measure a[3];
telept_Xcorrect_a3_2 = measure a3_epr_2;
if(telept_Zcorrect_a3_2) z a3_TO3;
if(telept_Xcorrect_a3_2) x a3_TO3;
// a[3] teleported into a3_TO3
qubit b0_epr_2;
qubit b0_TO3;
bit telept_Zcorrect_b0_2;
bit telept_Xcorrect_b0_2;
reset b0_epr_2;
reset b0_TO3;
h b0_epr_2;
cx b0_epr_2, b0_TO3;
cx b[0], b0_epr_2;
h b[0];
telept_Zcorrect_b0_2 = measure b[0];
telept_Xcorrect_b0_2 = measure b0_epr_2;
if(telept_Zcorrect_b0_2) z b0_TO3;
if(telept_Xcorrect_b0_2) x b0_TO3;
// b[0] teleported into b0_TO3
qubit b1_epr_2;
qubit b1_TO3;
bit telept_Zcorrect_b1_2;
bit telept_Xcorrect_b1_2;
reset b1_epr_2;
reset b1_TO3;
h b1_epr_2;
cx b1_epr_2, b1_TO3;
cx b[1], b1_epr_2;
h b[1];
telept_Zcorrect_b1_2 = measure b[1];
telept_Xcorrect_b1_2 = measure b1_epr_2;
if(telept_Zcorrect_b1_2) z b1_TO3;
if(telept_Xcorrect_b1_2) x b1_TO3;
// b[1] teleported into b1_TO3
qubit b2_epr_2;
qubit b2_TO3;
bit telept_Zcorrect_b2_2;
bit telept_Xcorrect_b2_2;
reset b2_epr_2;
reset b2_TO3;
h b2_epr_2;
cx b2_epr_2, b2_TO3;
cx b[2], b2_epr_2;
h b[2];
telept_Zcorrect_b2_2 = measure b[2];
telept_Xcorrect_b2_2 = measure b2_epr_2;
if(telept_Zcorrect_b2_2) z b2_TO3;
if(telept_Xcorrect_b2_2) x b2_TO3;
// b[2] teleported into b2_TO3
qubit b3_epr_2;
qubit b3_TO3;
bit telept_Zcorrect_b3_2;
bit telept_Xcorrect_b3_2;
reset b3_epr_2;
reset b3_TO3;
h b3_epr_2;
cx b3_epr_2, b3_TO3;
cx b[3], b3_epr_2;
h b[3];
telept_Zcorrect_b3_2 = measure b[3];
telept_Xcorrect_b3_2 = measure b3_epr_2;
if(telept_Zcorrect_b3_2) z b3_TO3;
if(telept_Xcorrect_b3_2) x b3_TO3;
// b[3] teleported into b3_TO3
qubit cin_epr_2;
qubit cin_TO3;
bit telept_Zcorrect_cin_2;
bit telept_Xcorrect_cin_2;
reset cin_epr_2;
reset cin_TO3;
h cin_epr_2;
cx cin_epr_2, cin_TO3;
cx cin, cin_epr_2;
h cin;
telept_Zcorrect_cin_2 = measure cin;
telept_Xcorrect_cin_2 = measure cin_epr_2;
if(telept_Zcorrect_cin_2) z cin_TO3;
if(telept_Xcorrect_cin_2) x cin_TO3;
// cin teleported into cin_TO3
qubit cout_epr_2;
qubit cout_TO3;
bit telept_Zcorrect_cout_2;
bit telept_Xcorrect_cout_2;
reset cout_epr_2;
reset cout_TO3;
h cout_epr_2;
cx cout_epr_2, cout_TO3;
cx cout, cout_epr_2;
h cout;
telept_Zcorrect_cout_2 = measure cout;
telept_Xcorrect_cout_2 = measure cout_epr_2;
if(telept_Zcorrect_cout_2) z cout_TO3;
if(telept_Xcorrect_cout_2) x cout_TO3;
// cout teleported into cout_TO3
bit[5] ans;
reset cin_TO3;
reset a0_TO3;
reset a1_TO3;
reset a2_TO3;
reset a3_TO3;
reset b0_TO3;
reset b1_TO3;
reset b2_TO3;
reset b3_TO3;
reset cout_TO3;
  x a0_TO3;
  x b0_TO3;
  x b1_TO3;
  x b2_TO3;
  x b3_TO3;
/* Teleporting qubits into chunk 4:
 * a0_TO3 from chunks 2, 3
 * a1_TO3 from chunks 2, 3
 * a2_TO3 from chunks 2, 3
 * a3_TO3 from chunks 2, 3
 * b0_TO3 from chunks 2, 3
 * b1_TO3 from chunks 2, 3
 * b2_TO3 from chunks 2, 3
 * b3_TO3 from chunks 2, 3
 * cin[0] from chunk 3
 * cout[0] from chunk 3
 */
qubit a0_TO3_epr_3;
qubit a0_TO3_TO4;
bit telept_Zcorrect_a0_TO3_3;
bit telept_Xcorrect_a0_TO3_3;
reset a0_TO3_epr_3;
reset a0_TO3_TO4;
h a0_TO3_epr_3;
cx a0_TO3_epr_3, a0_TO3_TO4;
cx a0_TO3, a0_TO3_epr_3;
h a0_TO3;
telept_Zcorrect_a0_TO3_3 = measure a0_TO3;
telept_Xcorrect_a0_TO3_3 = measure a0_TO3_epr_3;
if(telept_Zcorrect_a0_TO3_3) z a0_TO3_TO4;
if(telept_Xcorrect_a0_TO3_3) x a0_TO3_TO4;
// a0_TO3 teleported into a0_TO3_TO4
qubit a1_TO3_epr_3;
qubit a1_TO3_TO4;
bit telept_Zcorrect_a1_TO3_3;
bit telept_Xcorrect_a1_TO3_3;
reset a1_TO3_epr_3;
reset a1_TO3_TO4;
h a1_TO3_epr_3;
cx a1_TO3_epr_3, a1_TO3_TO4;
cx a1_TO3, a1_TO3_epr_3;
h a1_TO3;
telept_Zcorrect_a1_TO3_3 = measure a1_TO3;
telept_Xcorrect_a1_TO3_3 = measure a1_TO3_epr_3;
if(telept_Zcorrect_a1_TO3_3) z a1_TO3_TO4;
if(telept_Xcorrect_a1_TO3_3) x a1_TO3_TO4;
// a1_TO3 teleported into a1_TO3_TO4
qubit a2_TO3_epr_3;
qubit a2_TO3_TO4;
bit telept_Zcorrect_a2_TO3_3;
bit telept_Xcorrect_a2_TO3_3;
reset a2_TO3_epr_3;
reset a2_TO3_TO4;
h a2_TO3_epr_3;
cx a2_TO3_epr_3, a2_TO3_TO4;
cx a2_TO3, a2_TO3_epr_3;
h a2_TO3;
telept_Zcorrect_a2_TO3_3 = measure a2_TO3;
telept_Xcorrect_a2_TO3_3 = measure a2_TO3_epr_3;
if(telept_Zcorrect_a2_TO3_3) z a2_TO3_TO4;
if(telept_Xcorrect_a2_TO3_3) x a2_TO3_TO4;
// a2_TO3 teleported into a2_TO3_TO4
qubit a3_TO3_epr_3;
qubit a3_TO3_TO4;
bit telept_Zcorrect_a3_TO3_3;
bit telept_Xcorrect_a3_TO3_3;
reset a3_TO3_epr_3;
reset a3_TO3_TO4;
h a3_TO3_epr_3;
cx a3_TO3_epr_3, a3_TO3_TO4;
cx a3_TO3, a3_TO3_epr_3;
h a3_TO3;
telept_Zcorrect_a3_TO3_3 = measure a3_TO3;
telept_Xcorrect_a3_TO3_3 = measure a3_TO3_epr_3;
if(telept_Zcorrect_a3_TO3_3) z a3_TO3_TO4;
if(telept_Xcorrect_a3_TO3_3) x a3_TO3_TO4;
// a3_TO3 teleported into a3_TO3_TO4
qubit b0_TO3_epr_3;
qubit b0_TO3_TO4;
bit telept_Zcorrect_b0_TO3_3;
bit telept_Xcorrect_b0_TO3_3;
reset b0_TO3_epr_3;
reset b0_TO3_TO4;
h b0_TO3_epr_3;
cx b0_TO3_epr_3, b0_TO3_TO4;
cx b0_TO3, b0_TO3_epr_3;
h b0_TO3;
telept_Zcorrect_b0_TO3_3 = measure b0_TO3;
telept_Xcorrect_b0_TO3_3 = measure b0_TO3_epr_3;
if(telept_Zcorrect_b0_TO3_3) z b0_TO3_TO4;
if(telept_Xcorrect_b0_TO3_3) x b0_TO3_TO4;
// b0_TO3 teleported into b0_TO3_TO4
qubit b1_TO3_epr_3;
qubit b1_TO3_TO4;
bit telept_Zcorrect_b1_TO3_3;
bit telept_Xcorrect_b1_TO3_3;
reset b1_TO3_epr_3;
reset b1_TO3_TO4;
h b1_TO3_epr_3;
cx b1_TO3_epr_3, b1_TO3_TO4;
cx b1_TO3, b1_TO3_epr_3;
h b1_TO3;
telept_Zcorrect_b1_TO3_3 = measure b1_TO3;
telept_Xcorrect_b1_TO3_3 = measure b1_TO3_epr_3;
if(telept_Zcorrect_b1_TO3_3) z b1_TO3_TO4;
if(telept_Xcorrect_b1_TO3_3) x b1_TO3_TO4;
// b1_TO3 teleported into b1_TO3_TO4
qubit b2_TO3_epr_3;
qubit b2_TO3_TO4;
bit telept_Zcorrect_b2_TO3_3;
bit telept_Xcorrect_b2_TO3_3;
reset b2_TO3_epr_3;
reset b2_TO3_TO4;
h b2_TO3_epr_3;
cx b2_TO3_epr_3, b2_TO3_TO4;
cx b2_TO3, b2_TO3_epr_3;
h b2_TO3;
telept_Zcorrect_b2_TO3_3 = measure b2_TO3;
telept_Xcorrect_b2_TO3_3 = measure b2_TO3_epr_3;
if(telept_Zcorrect_b2_TO3_3) z b2_TO3_TO4;
if(telept_Xcorrect_b2_TO3_3) x b2_TO3_TO4;
// b2_TO3 teleported into b2_TO3_TO4
qubit b3_TO3_epr_3;
qubit b3_TO3_TO4;
bit telept_Zcorrect_b3_TO3_3;
bit telept_Xcorrect_b3_TO3_3;
reset b3_TO3_epr_3;
reset b3_TO3_TO4;
h b3_TO3_epr_3;
cx b3_TO3_epr_3, b3_TO3_TO4;
cx b3_TO3, b3_TO3_epr_3;
h b3_TO3;
telept_Zcorrect_b3_TO3_3 = measure b3_TO3;
telept_Xcorrect_b3_TO3_3 = measure b3_TO3_epr_3;
if(telept_Zcorrect_b3_TO3_3) z b3_TO3_TO4;
if(telept_Xcorrect_b3_TO3_3) x b3_TO3_TO4;
// b3_TO3 teleported into b3_TO3_TO4
qubit cin0_epr_3;
qubit cin0_TO4;
bit telept_Zcorrect_cin0_3;
bit telept_Xcorrect_cin0_3;
reset cin0_epr_3;
reset cin0_TO4;
h cin0_epr_3;
cx cin0_epr_3, cin0_TO4;
cx cin[0], cin0_epr_3;
h cin[0];
telept_Zcorrect_cin0_3 = measure cin[0];
telept_Xcorrect_cin0_3 = measure cin0_epr_3;
if(telept_Zcorrect_cin0_3) z cin0_TO4;
if(telept_Xcorrect_cin0_3) x cin0_TO4;
// cin[0] teleported into cin0_TO4
qubit cout0_epr_3;
qubit cout0_TO4;
bit telept_Zcorrect_cout0_3;
bit telept_Xcorrect_cout0_3;
reset cout0_epr_3;
reset cout0_TO4;
h cout0_epr_3;
cx cout0_epr_3, cout0_TO4;
cx cout[0], cout0_epr_3;
h cout[0];
telept_Zcorrect_cout0_3 = measure cout[0];
telept_Xcorrect_cout0_3 = measure cout0_epr_3;
if(telept_Zcorrect_cout0_3) z cout0_TO4;
if(telept_Xcorrect_cout0_3) x cout0_TO4;
// cout[0] teleported into cout0_TO4
majority cin0_TO4, b0_TO3_TO4, a0_TO3_TO4;
majority a0_TO3_TO4, b[0 + 1], a[0 + 1];
majority a1_TO3_TO4, b[1 + 1], a[1 + 1];
majority a2_TO3_TO4, b[2 + 1], a[2 + 1];
cx a3_TO3_TO4, cout0_TO4;
unmaj a2_TO3_TO4,b[2+1],a[2+1];
unmaj a1_TO3_TO4,b[1+1],a[1+1];
unmaj a0_TO3_TO4,b[0+1],a[0+1];
unmaj cin0_TO4, b0_TO3_TO4, a0_TO3_TO4;
measure b0_TO3_TO4 -> ans[0];
measure b1_TO3_TO4 -> ans[1];
measure b2_TO3_TO4 -> ans[2];
measure b3_TO3_TO4 -> ans[3];
measure cout0_TO4 -> ans[4];