OPENQASM 3.0;
include "stdgates.inc";
// DQC teleport bridge from chunk 1 to 2
h2 $0;
// DQC teleport bridge from chunk 2 to 3
cx $0, $1;
// DQC teleport bridge from chunk 3 to 4
measure $0;
// DQC teleport bridge from chunk 4 to 5
measure $1;