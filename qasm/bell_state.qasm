// Simple Bell state circuit
OPENQASM 3;
include "stdgates.inc";

qubit[2] q;
bit[2] c;

// Create Bell state |Φ+⟩ = (|00⟩ + |11⟩) / √2
h q[0];
cx q[0], q[1];

// Measure both qubits
c = measure q;
