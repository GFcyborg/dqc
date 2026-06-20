OPENQASM 3.0;
include "stdgates.inc";
h $0;
cx $0, $1;
measure $0;
measure $1;
