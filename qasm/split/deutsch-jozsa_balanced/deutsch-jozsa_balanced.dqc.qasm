//from: https://claude.ai/chat/e92cbef2-3162-4296-ab27-6b8fadd88af7

OPENQASM 3.0;
include "stdgates.inc";

// ── Registri ──────────────────────────────────────────────────────────────
qubit[3] q;       // q[0], q[1], q[2] : input qubits  (righe superiori)
qubit    anc;     // q[3]             : ancilla qubit  (riga inferiore)
bit[3]   c;       // registro classico per le misure

// ── Inizializzazione ancilla: |0⟩ → |1⟩ ──────────────────────────────────
x anc;

barrier q[0], q[1], q[2], anc;
/* Teleporting qubits into chunk 2:
 * anc from chunk 1
 * q[0] from chunk 1
 * q[1] from chunk 1
 * q[2] from chunk 1
 */
qubit anc_epr_1;
qubit anc_epr_TARGET_1;
bit telept_Zcorrect_anc_1;
bit telept_Xcorrect_anc_1;
reset anc_epr_1;
reset anc_epr_TARGET_1;
h anc_epr_1;
cx anc_epr_1, anc_epr_TARGET_1;
cx anc, anc_epr_1;
h anc;
telept_Zcorrect_anc_1 = measure anc;
telept_Xcorrect_anc_1 = measure anc_epr_1;
if(telept_Zcorrect_anc_1) z anc_epr_TARGET_1;
if(telept_Xcorrect_anc_1) x anc_epr_TARGET_1;
// anc teleported into anc_epr_TARGET_1
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

// ── Hadamard su tutti i qubit ─────────────────────────────────────────────
h q[0];
h q[1];
h q[2];
h anc;

barrier q[0], q[1], q[2], anc;
/* Teleporting qubits into chunk 3:
 * anc from chunk 2
 * q[0] from chunks 1, 2
 * q[1] from chunks 1, 2
 * q[2] from chunks 1, 2
 */
qubit anc_epr_2;
qubit anc_epr_TARGET_2;
bit telept_Zcorrect_anc_2;
bit telept_Xcorrect_anc_2;
reset anc_epr_2;
reset anc_epr_TARGET_2;
h anc_epr_2;
cx anc_epr_2, anc_epr_TARGET_2;
cx anc, anc_epr_2;
h anc;
telept_Zcorrect_anc_2 = measure anc;
telept_Xcorrect_anc_2 = measure anc_epr_2;
if(telept_Zcorrect_anc_2) z anc_epr_TARGET_2;
if(telept_Xcorrect_anc_2) x anc_epr_TARGET_2;
// anc teleported into anc_epr_TARGET_2
qubit q0_epr_2;
qubit q0_epr_TARGET_2;
bit telept_Zcorrect_q0_2;
bit telept_Xcorrect_q0_2;
reset q0_epr_2;
reset q0_epr_TARGET_2;
h q0_epr_2;
cx q0_epr_2, q0_epr_TARGET_2;
cx q[0], q0_epr_2;
h q[0];
telept_Zcorrect_q0_2 = measure q[0];
telept_Xcorrect_q0_2 = measure q0_epr_2;
if(telept_Zcorrect_q0_2) z q0_epr_TARGET_2;
if(telept_Xcorrect_q0_2) x q0_epr_TARGET_2;
// q[0] teleported into q0_epr_TARGET_2
qubit q1_epr_2;
qubit q1_epr_TARGET_2;
bit telept_Zcorrect_q1_2;
bit telept_Xcorrect_q1_2;
reset q1_epr_2;
reset q1_epr_TARGET_2;
h q1_epr_2;
cx q1_epr_2, q1_epr_TARGET_2;
cx q[1], q1_epr_2;
h q[1];
telept_Zcorrect_q1_2 = measure q[1];
telept_Xcorrect_q1_2 = measure q1_epr_2;
if(telept_Zcorrect_q1_2) z q1_epr_TARGET_2;
if(telept_Xcorrect_q1_2) x q1_epr_TARGET_2;
// q[1] teleported into q1_epr_TARGET_2
qubit q2_epr_2;
qubit q2_epr_TARGET_2;
bit telept_Zcorrect_q2_2;
bit telept_Xcorrect_q2_2;
reset q2_epr_2;
reset q2_epr_TARGET_2;
h q2_epr_2;
cx q2_epr_2, q2_epr_TARGET_2;
cx q[2], q2_epr_2;
h q[2];
telept_Zcorrect_q2_2 = measure q[2];
telept_Xcorrect_q2_2 = measure q2_epr_2;
if(telept_Zcorrect_q2_2) z q2_epr_TARGET_2;
if(telept_Xcorrect_q2_2) x q2_epr_TARGET_2;
// q[2] teleported into q2_epr_TARGET_2

// ── Oracolo bilanciato  Uf : f(x) = x₀ ⊕ x₁ ⊕ x₂ ───────────────────────
// Phase kickback: |x⟩|−⟩ → (−1)^{f(x)} |x⟩|−⟩
cx q[0], anc;
cx q[1], anc;
cx q[2], anc;

barrier q[0], q[1], q[2], anc;

// ── Hadamard inverso sui qubit di input ───────────────────────────────────
h q[0];
h q[1];
h q[2];

barrier q[0], q[1], q[2], anc;

// ── Misura (solo i qubit di input; anc non misurata) ─────────────────────
c = measure q;
// Atteso per oracolo bilanciato: c ≠ 000  (tipicamente 111 per questo Uf)