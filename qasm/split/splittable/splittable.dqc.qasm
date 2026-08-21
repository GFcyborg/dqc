OPENQASM 3.0;
include "stdgates.inc";
qubit[4] q;
bit[2] c_bell;
bit[1] c_ind;
reset q[0];
reset q[1];
h q[0];
cx q[0], q[1];
barrier q[0], q[1];
c_bell[0] = measure q[0];
c_bell[1] = measure q[1];
reset q[2];
h q[2];
if (c_bell[1]) {
    x q[2];
}
if (c_bell[0]) {
    z q[2];
}
reset q[3];
h q[3];
z q[3];
/* Teleporting qubits into chunk 2:
 * q[3] from chunk 1
 */
qubit q3_epr_1;
qubit q3_TO2;
bit telept_Zcorrect_q3_1;
bit telept_Xcorrect_q3_1;
reset q3_epr_1;
reset q3_TO2;
h q3_epr_1;
cx q3_epr_1, q3_TO2;
cx q[3], q3_epr_1;
h q[3];
telept_Zcorrect_q3_1 = measure q[3];
telept_Xcorrect_q3_1 = measure q3_epr_1;
if(telept_Zcorrect_q3_1) z q3_TO2;
if(telept_Xcorrect_q3_1) x q3_TO2;
// q[3] teleported into q3_TO2
h q3_TO2;
z q3_TO2;
h q3_TO2;
c_ind[0] = measure q3_TO2;