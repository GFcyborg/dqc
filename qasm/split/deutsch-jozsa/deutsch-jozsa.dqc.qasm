// from: https://en.wikipedia.org/wiki/Deutsch%E2%80%93Jozsa_algorithm

OPENQASM 3.0;
include "stdgates.inc";

// 4 qubit: q[0]=q0, q[1]=q1, q[2]=q2, q[3]=ancilla/target
qubit[4] q;
bit[4] c;

barrier q;

// ── Blocco 1 : scatta per (q0=1, q1=1, q2=0) ─────────────────────────────
x q[2];                          // controllo negativo su q2
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[2];                          // ripristino q2

barrier q;

// ── Blocco 2 : scatta per (q0=0, q1=0, q2=0) ─────────────────────────────
x q[0];
x q[1];
x q[2];
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[0];
x q[1];
x q[2];

barrier q;

// ── Blocco 3 : scatta per (q0=0, q1=1, q2=0) ─────────────────────────────
x q[0];
x q[2];
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[0];
x q[2];

barrier q;

// ── Blocco 4 : scatta per (q0=1, q1=0, q2=1) ─────────────────────────────
x q[1];
ctrl(3) @ x q[0], q[1], q[2], q[3];
/* Teleporting qubits into chunk 2:
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 * q[3] from chunk 1
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
qubit q2_epr_1;
qubit q2_epr_TARGET_1;
bit telept_Zcorrect_q2_1;
bit telept_Xcorrect_q2_1;
reset q2_epr_1;
reset q2_epr_TARGET_1;
h q2_epr_1;
cx q2_epr_1, q2_epr_TARGET_1;
cx q[2], q2_epr_1;
h q[2];
telept_Zcorrect_q2_1 = measure q[2];
telept_Xcorrect_q2_1 = measure q2_epr_1;
if(telept_Zcorrect_q2_1) z q2_epr_TARGET_1;
if(telept_Xcorrect_q2_1) x q2_epr_TARGET_1;
// q[2] teleported into q2_epr_TARGET_1
qubit q3_epr_1;
qubit q3_epr_TARGET_1;
bit telept_Zcorrect_q3_1;
bit telept_Xcorrect_q3_1;
reset q3_epr_1;
reset q3_epr_TARGET_1;
h q3_epr_1;
cx q3_epr_1, q3_epr_TARGET_1;
cx q[3], q3_epr_1;
h q[3];
telept_Zcorrect_q3_1 = measure q[3];
telept_Xcorrect_q3_1 = measure q3_epr_1;
if(telept_Zcorrect_q3_1) z q3_epr_TARGET_1;
if(telept_Xcorrect_q3_1) x q3_epr_TARGET_1;
// q[3] teleported into q3_epr_TARGET_1
x q[1];

barrier q;

c = measure q;