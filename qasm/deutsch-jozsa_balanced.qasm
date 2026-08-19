//from: https://claude.ai/chat/e92cbef2-3162-4296-ab27-6b8fadd88af7

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;       // input qubits
qubit    anc;     // ancilla qubit
bit[3]   c;       // classical bit for measurements

x anc; // init ancilla: |0⟩ → |1⟩

barrier q[0], q[1], q[2], anc;

// Hadamard on all qubits
h q[0];
h q[1];
h q[2];
h anc;

barrier q[0], q[1], q[2], anc;

// Balanced oracle Uf : f(x) = x₀ ⊕ x₁ ⊕ x₂
// Phase kickback: |x⟩|−⟩ → (−1)^{f(x)} |x⟩|−⟩
cx q[0], anc;
cx q[1], anc;
cx q[2], anc;

barrier q[0], q[1], q[2], anc;

// Reverse Hadamard on input qubits
h q[0];
h q[1];
h q[2];

barrier q[0], q[1], q[2], anc;

// Measurement (only input qubits; ancilla not measured)
c = measure q; // Expected for balanced oracle: c ≠ 000  (typically 111 for this Uf)
