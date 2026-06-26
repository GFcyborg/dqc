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
/* Teleporting qubits into chunk 2:
 * cin from chunk 1
 */
qubit cin_epr_1;
qubit cin_epr_TARGET_1;
bit telept_Zcorrect_cin_1;
bit telept_Xcorrect_cin_1;
reset cin_epr_1;
reset cin_epr_TARGET_1;
h cin_epr_1;
cx cin_epr_1, cin_epr_TARGET_1;
cx cin, cin_epr_1;
h cin;
telept_Zcorrect_cin_1 = measure cin;
telept_Xcorrect_cin_1 = measure cin_epr_1;
if(telept_Zcorrect_cin_1) z cin_epr_TARGET_1;
if(telept_Xcorrect_cin_1) x cin_epr_TARGET_1;
// cin teleported into cin_epr_TARGET_1
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

// set input states
for uint i in [0: 3] {
  if(bool(a_in[i])) x a[i];
  if(bool(b_in[i])) x b[i];
}
// add a to b, storing result in b
majority cin[0], b[0], a[0];
for uint i in [0: 2] { majority a[i], b[i + 1], a[i + 1]; }
cx a[3], cout[0];
for uint i in [2: -1: 0] { unmaj a[i],b[i+1],a[i+1]; }
unmaj cin[0], b[0], a[0];
measure b[0:3] -> ans[0:3];
measure cout[0] -> ans[4];