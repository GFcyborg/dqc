// quantum teleportation example
OPENQASM 3; // Version statement is optional
include "stdgates.inc";
qubit q; //q0
qubit a; //q1
qubit b; //q2
bit cq;
bit ca;
bit cb;
// optional post-rotation for state tomography
// empty gate body => identity gate
gate post q { }
reset q;
reset a;
reset b;
U(0.3, 0.2, 0.1) q;
h a;
cx a, b;
barrier q,a,b;

cx q, a;
h q;
cq = measure q;
ca = measure a;
if(cq==1) z b;
if(ca==1) { x b; }  // braces optional in this case
post b;
cb = measure b;
