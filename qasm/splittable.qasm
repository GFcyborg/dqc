// from: https://chatgpt.com/c/69fcbaa4-3438-8396-88a2-4c80a6f36df5

OPENQASM 3.0;
include "stdgates.inc";

qubit[4] q;
bit[2] c_bell;
bit[1] c_ind;

// ═════════════════════════════════════════════════════════════════════════
// CHUNK 1 — Bell-pair preparation and measurement
// ═════════════════════════════════════════════════════════════════════════
reset q[0];
reset q[1];
h q[0];
cx q[0], q[1];
barrier q[0], q[1];
c_bell[0] = measure q[0];
c_bell[1] = measure q[1];

// ═════════════════════════════════════════════════════════════════════════
// CHUNK 2 — Classically-controlled correction
// ═════════════════════════════════════════════════════════════════════════
reset q[2];

h q[2];

if (c_bell[1]) {
    x q[2];
}

if (c_bell[0]) {
    z q[2];
}

// ═════════════════════════════════════════════════════════════════════════
// CHUNK 3 — Independent step
// ═════════════════════════════════════════════════════════════════════════
reset q[3];

h q[3];
z q[3];
h q[3];
z q[3];
h q[3];

c_ind[0] = measure q[3];
