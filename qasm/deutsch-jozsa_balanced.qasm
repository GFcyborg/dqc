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

// ── Hadamard su tutti i qubit ─────────────────────────────────────────────
h q[0];
h q[1];
h q[2];
h anc;

barrier q[0], q[1], q[2], anc;

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
