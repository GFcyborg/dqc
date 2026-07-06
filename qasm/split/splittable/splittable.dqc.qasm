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
/* Teleporting qubits into chunk 2:
 * q[2] from chunk 1
 * q[3] from chunk 1
 */
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
/* Teleporting qubits into chunk 3:
 * q[3] from chunk 2
 */
qubit q3_epr_2;
qubit q3_epr_TARGET_2;
bit telept_Zcorrect_q3_2;
bit telept_Xcorrect_q3_2;
reset q3_epr_2;
reset q3_epr_TARGET_2;
h q3_epr_2;
cx q3_epr_2, q3_epr_TARGET_2;
cx q[3], q3_epr_2;
h q[3];
telept_Zcorrect_q3_2 = measure q[3];
telept_Xcorrect_q3_2 = measure q3_epr_2;
if(telept_Zcorrect_q3_2) z q3_epr_TARGET_2;
if(telept_Xcorrect_q3_2) x q3_epr_TARGET_2;
// q[3] teleported into q3_epr_TARGET_2
h q[3];
z q[3];
/* Teleporting qubits into chunk 4:
 * q[3] from chunk 3
 */
qubit q3_epr_3;
qubit q3_epr_TARGET_3;
bit telept_Zcorrect_q3_3;
bit telept_Xcorrect_q3_3;
reset q3_epr_3;
reset q3_epr_TARGET_3;
h q3_epr_3;
cx q3_epr_3, q3_epr_TARGET_3;
cx q[3], q3_epr_3;
h q[3];
telept_Zcorrect_q3_3 = measure q[3];
telept_Xcorrect_q3_3 = measure q3_epr_3;
if(telept_Zcorrect_q3_3) z q3_epr_TARGET_3;
if(telept_Xcorrect_q3_3) x q3_epr_TARGET_3;
// q[3] teleported into q3_epr_TARGET_3
h q[3];

c_ind[0] = measure q[3];