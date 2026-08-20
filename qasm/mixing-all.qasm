/*
 * mixing-all.qasm
 * Crash-test reference example: mixes constructs/expressions borrowed from
 * every "good" example under ./qasm/ (bell_state, teleport, qft, inverseqft2,
 * deutsch-jozsa, bernstein-vazirani, adder, rb, cphase+, qiskit-example),
 * excluding anything from ./qasm/x_problematic/. It runs standalone in AER
 * with fixed numeric parameters (no user input) and no split pragmas, so it
 * should always execute smoothly and can be reloaded after every app update
 * to verify parsing/rewriting/graphing/runtime still work end-to-end.
 * Total qubit count across all sections: 2+3+4+4+4+6+2 = 25.
 */

OPENQASM 3.0;
include "stdgates.inc"; // gate library used by every section below

// --- custom gate colliding with a stdgates.inc name (exercises rule #5) ---
gate cphase(θ) a, b {
  U(0, 0, θ / 2) a;
  cx a, b; // fixed case of CX
  U(0, 0, -θ / 2) b;
  cx a, b; // fixed case of CX
  U(0, 0, θ / 2) b;
}

// --- custom gates with params/modifiers (from qiskit-example.qasm) ---
gate my_gate(a) c, t {
  gphase(a / 2);
  ry(a) c;
  cx c, t;
}

gate my_phase(a) c {
  ctrl @ inv @ gphase(a) c;
}

// --- custom multi-qubit gates (from adder.qasm) ---
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

// --- empty-body identity gate (from teleport.qasm) ---
gate post q { }

// ═════════════════════════════════════════════════════════════════════════
// Bell state (bell_state.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[2] q_bell;
bit[2] c_bell;

h q_bell[0];
cx q_bell[0], q_bell[1];
c_bell = measure q_bell; // whole-register assignment form

// ═════════════════════════════════════════════════════════════════════════
// Teleportation + modifier gates (teleport.qasm, qiskit-example.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[3] q_tel;
bit c_tel0;
bit c_tel1;
bit c_tel2;

reset q_tel; // whole-register reset
U(0.3, 0.2, 0.1) q_tel[0];
h q_tel[1];
cx q_tel[1], q_tel[2];
barrier q_tel; // whole-register barrier
cx q_tel[0], q_tel[1];
h q_tel[0];
c_tel0 = measure q_tel[0];
c_tel1 = measure q_tel[1];
if (c_tel0 == 1) z q_tel[2];      // braces optional
if (c_tel1 == 1) { x q_tel[2]; }  // braces present
post q_tel[2];
c_tel2 = measure q_tel[2];

// reuse the same register for the parametrised/modifier gates
reset q_tel[0];
reset q_tel[1];
my_gate(pi / 3) q_tel[0], q_tel[1];
my_phase(pi / 4 - pi / 2) q_tel[1];

// ═════════════════════════════════════════════════════════════════════════
// QFT-like phase kickback with bit-to-bool conditions (qft.qasm,
// inverseqft2.qasm) and the colliding custom "cphase" gate above.
// ═════════════════════════════════════════════════════════════════════════
qubit[4] q_qft;
bit c_qft0;
bit c_qft1;
bit c_qft2;
bit c_qft3;

reset q_qft;
h q_qft[0];
measure q_qft[0] -> c_qft0; // indexed arrow form
if (c_qft0 == 1) { rz(pi / 2) q_qft[1]; }
h q_qft[1];
measure q_qft[1] -> c_qft1;
if (c_qft0 == 1) { rz(pi / 4) q_qft[2]; }
if (c_qft1 == 1) { rz(pi / 2) q_qft[2]; }
h q_qft[2];
measure q_qft[2] -> c_qft2;
if (c_qft0 == 0) { x q_qft[3]; } // negated (==0) form
cphase(pi / 2) q_qft[2], q_qft[3];
h q_qft[3];
measure q_qft[3] -> c_qft3;

// ═════════════════════════════════════════════════════════════════════════
// Deutsch-Jozsa-like oracle with multi-control modifier + alias + index set
// (deutsch-jozsa.qasm, qiskit-example.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[4] q_dj; // q_dj[3] = ancilla/target
bit[4] c_dj;

let dj_pair = q_dj[0:1]; // slice alias

x q_dj[3];
h q_dj[3];
h dj_pair[0];
h dj_pair[1];
h q_dj[2];

barrier q_dj;

// oracle triggered by (q0=1, q1=1, q2=0)
x q_dj[2];                          // negative control on q2
ctrl(3) @ x q_dj[0], q_dj[1], q_dj[2], q_dj[3];
x q_dj[2];                          // revert q2

barrier q_dj;

x q_dj[{0, 2}]; // index-set broadcast

h q_dj[0];
h q_dj[1];
h q_dj[2];

c_dj[0] = measure q_dj[0];
c_dj[1] = measure q_dj[1];
c_dj[2] = measure q_dj[2];
c_dj[3] = measure q_dj[3];

// ═════════════════════════════════════════════════════════════════════════
// Bernstein-Vazirani-like fan-out with a curly-brace index-set alias
// (bernstein-vazirani.qasm, qiskit-example.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[4] q_bv; // q_bv[3] = ancilla
bit[3] c_bv;

let bv_pair = q_bv[{0, 1}]; // index-set alias

x q_bv[3];
h q_bv[3];
h bv_pair[0];
h bv_pair[1];
h q_bv[2];

cx q_bv[3], q_bv[0];
cx q_bv[3], q_bv[2];

h q_bv[0];
h q_bv[1];
h q_bv[2];

c_bv[0] = measure q_bv[0];
c_bv[1] = measure q_bv[1];
c_bv[2] = measure q_bv[2];

// ═════════════════════════════════════════════════════════════════════════
// Ripple-carry adder (2-bit), with uint counters + forward/backward for
// loops (adder.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[1] cin;
qubit[2] a;
qubit[2] b;
qubit[1] cout;
bit[3] ans;
uint[2] a_in = 1; // a = 01
uint[2] b_in = 3; // b = 11

reset cin;
reset a;
reset b;
reset cout;

for uint i in [0: 1] {
  if (bool(a_in[i])) x a[i];
  if (bool(b_in[i])) x b[i];
}

majority cin[0], b[0], a[0];
for uint i in [0: 0] { majority a[i], b[i + 1], a[i + 1]; }
cx a[1], cout[0];
for uint i in [0: -1: 0] { unmaj a[i], b[i + 1], a[i + 1]; }
unmaj cin[0], b[0], a[0];

measure b[0:1] -> ans[0:1];
measure cout[0] -> ans[2];

// ═════════════════════════════════════════════════════════════════════════
// Randomized-benchmarking-style sequence (rb.qasm)
// ═════════════════════════════════════════════════════════════════════════
qubit[2] q_rb;
bit[2] c_rb;

reset q_rb;
h q_rb[0];
barrier q_rb;
cz q_rb[0], q_rb[1];
barrier q_rb;
s q_rb[0];
cz q_rb[0], q_rb[1];
barrier q_rb;
s q_rb[0];
z q_rb[0];
h q_rb[0];
barrier q_rb;
measure q_rb -> c_rb; // whole-register arrow form
