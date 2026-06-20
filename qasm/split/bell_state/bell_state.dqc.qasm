// Simple Bell state circuit
OPENQASM 3;
include "stdgates.inc";

qubit[2] q;
bit[2] c;
/* Teleporting qubits into chunk 2:
 * Bell from chunk 1
 * q from chunk 1
 * state from chunk 1
 */

// Create Bell state |Φ+⟩ = (|00⟩ + |11⟩) / √2
h q[0];
cx q[0], q[1];
/* Teleporting qubits into chunk 3:
 * q from chunk 2
 */

// Measure both qubits
c = measure q;