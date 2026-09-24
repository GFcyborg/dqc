// from: /home/gf/.copilot/workspaces/868edba3-9e17-431c-84d0-cbf78325b27b/attachments/c8672f27-a563-4fe3-a927-cf2d7d53bb50-dqc.tex

OPENQASM 3.0;
include "stdgates.inc";
qubit[4] q;
bit[4] c;
h q[0];
h q[1];
x q[0];
x q[2];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
c[3] = measure q[3];

