OPENQASM 3.1;
include "stdgates.inc";
const int[32] n = 3;
extern vote(bit[n]) -> bit;
def logical_meas(qubit[3] d) -> bit {
    bit[3] c;
    bit r;
    measure d -> c;
    r = vote(c);
    return r;
}
qubit[3] q;
qubit[3] a;
bit r;
// DQC teleport bridge from chunk 1 to 2
// teleport a via EPR pair and classical correction bits
// teleport logical_meas via EPR pair and classical correction bits
// teleport q via EPR pair and classical correction bits
// teleport r via EPR pair and classical correction bits
rz(pi/4) a;
cx q, a;
r = logical_meas(a);
if (r == 1) z q;