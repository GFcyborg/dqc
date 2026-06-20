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
x q[1];

barrier q;

c = measure q;
