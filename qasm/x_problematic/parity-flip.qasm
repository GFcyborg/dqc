// from: /home/gf/.copilot/workspaces/868edba3-9e17-431c-84d0-cbf78325b27b/attachments/c8672f27-a563-4fe3-a927-cf2d7d53bb50-dqc.tex

OPENQASM 3;
include "stdgates.inc";

gate h2 a, b { h a; h b; }
def parity_flip(qubit[4] q) {
    for int i in [0:3] {
        if (i % 2 == 0) {
            x q[i];
        }
    }
}

qubit[4] q;
bit[4] c;

h2 q[0], q[1];
parity_flip(q);

for int i in [0:3] {
    measure q[i] -> c[i];
}
