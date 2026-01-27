#!/bin/sh

# new grammars from: https://github.com/openqasm/openqasm/blob/main/source/grammar/

echo "This script should be run from the same dir where it's located as it relies on relative paths."
echo "<Ctrl-C> within 10 seconds to abort ..."
sleep 10

mkdir -p bkp && \
cd bkp/ && \
wget --backups=3 \
  https://raw.githubusercontent.com/openqasm/openqasm/refs/heads/main/source/grammar/qasm3Lexer.g4 \
  https://raw.githubusercontent.com/openqasm/openqasm/refs/heads/main/source/grammar/qasm3Parser.g4 \
&& date > ../$(basename "$0")_last-run \
&& cp -fa *.g4 ../../antlr/
