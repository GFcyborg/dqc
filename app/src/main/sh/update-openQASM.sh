#!/bin/sh

echo "This script should be run from the same dir where it's located as it relies on relative paths."
echo "<Ctrl-C> within 10 seconds to abort ..."
sleep 10

# new grammars from: https://github.com/openqasm/openqasm/blob/main/source/grammar/
mkdir -p bkp && \
  cd bkp/ && \
  wget --backups=3 \
    https://raw.githubusercontent.com/openqasm/openqasm/refs/heads/main/source/grammar/qasm3Lexer.g4 \
    https://raw.githubusercontent.com/openqasm/openqasm/refs/heads/main/source/grammar/qasm3Parser.g4 \
  && date > ../$(basename "$0")_last-run \
  && cp -fa *.g4 ../../antlr/
cd ..

# new OpenQASM examples from: https://github.com/openqasm/openqasm/tree/main/examples
git clone --depth 1 --filter=blob:none --sparse https://github.com/openqasm/openqasm.git tmp && \
  git -C tmp sparse-checkout set examples && \
  mkdir -p ../openqasm/examples && \
  cp -fa tmp/examples/ ../openqasm/
rm -rf tmp    # cleanup git noise
