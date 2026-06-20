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
/* Teleporting qubits into chunk 2:
 * Blocco from chunk 1
 * barrier from chunk 1
 * ctrl from chunk 1
 * per from chunk 1
 * q from chunk 1
 * q0 from chunk 1
 * q1 from chunk 1
 * q2 from chunk 1
 * scatta from chunk 1
 * x from chunk 1
 */

// ── Blocco 2 : scatta per (q0=0, q1=0, q2=0) ─────────────────────────────
x q[0];
x q[1];
x q[2];
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[0];
x q[1];
x q[2];

barrier q;
/* Teleporting qubits into chunk 3:
 * Blocco from chunk 2
 * barrier from chunk 2
 * ctrl from chunk 2
 * per from chunk 2
 * q from chunk 2
 * q0 from chunk 2
 * q1 from chunk 2
 * q2 from chunk 2
 * scatta from chunk 2
 * x from chunk 2
 */

// ── Blocco 3 : scatta per (q0=0, q1=1, q2=0) ─────────────────────────────
x q[0];
x q[2];
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[0];
x q[2];

barrier q;
/* Teleporting qubits into chunk 4:
 * Blocco from chunk 3
 * barrier from chunk 3
 * ctrl from chunk 3
 * per from chunk 3
 * q from chunk 3
 * q0 from chunk 3
 * q1 from chunk 3
 * q2 from chunk 3
 * scatta from chunk 3
 * x from chunk 3
 */

// ── Blocco 4 : scatta per (q0=1, q1=0, q2=1) ─────────────────────────────
x q[1];
ctrl(3) @ x q[0], q[1], q[2], q[3];
x q[1];

barrier q;
/* Teleporting qubits into chunk 5:
 * q from chunk 4
 */

c = measure q;