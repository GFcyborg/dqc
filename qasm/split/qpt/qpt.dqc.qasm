OPENQASM 3.1;
include "stdgates.inc";
gate pre q { }
gate post q { }
qubit q;
bit c;
reset q;
pre q;
barrier q;
/* Teleporting qubits into chunk 2:
 * q from chunk 1
 */
qubit q_epr_1;
qubit q_TO2;
bit telept_Zcorrect_q_1;
bit telept_Xcorrect_q_1;
reset q_epr_1;
reset q_TO2;
h q_epr_1;
cx q_epr_1, q_TO2;
cx q, q_epr_1;
h q;
telept_Zcorrect_q_1 = measure q;
telept_Xcorrect_q_1 = measure q_epr_1;
if(telept_Zcorrect_q_1) z q_TO2;
if(telept_Xcorrect_q_1) x q_TO2;
// q teleported into q_TO2
h q_TO2;
barrier q_TO2;
post q_TO2;
c = measure q_TO2;