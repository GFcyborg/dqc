from __future__ import annotations

import unittest

from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister, QuantumRegister

from app.pipeline import line_is_inside_blocking_scope, qasm_token_graph, suggest_split_points
from app.widgets import _wire_label, collect_multi_qubit_interactions


class PipelineRegressionTests(unittest.TestCase):
    def test_split_guard_blocks_only_inner_scope_line(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[1] q;",
                "gate myg a {",
                "  x a;",
                "}",
                "myg q[0];",
            ]
        )

        self.assertTrue(line_is_inside_blocking_scope(source, 5))
        self.assertFalse(line_is_inside_blocking_scope(source, 7))

    def test_split_suggestion_prefers_multi_qubit_or_control_flow_lines(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[2] q;",
                "bit c;",
                "cx q[0], q[1];",
                "if(c == 1) x q[0];",
            ]
        )

        suggested, reason = suggest_split_points(source, max_points=3)

        self.assertIn(5, suggested)
        self.assertIn("line", reason)

    def test_token_graph_ignores_split_and_teleport_comment_lines(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[2] q;",
                "h q[0];",
                "pragma dqc.v1.split id=1",
                "/* Teleporting qubits into chunk 2:",
                " * q from chunk 1",
                " */",
                "cx q[0], q[1];",
            ]
        )

        dag, interaction, chunk_graph = qasm_token_graph(source)

        dag_labels = [data.get("label", "") for _, data in dag.nodes(data=True)]
        self.assertFalse(any("Teleporting qubits" in label for label in dag_labels))
        self.assertFalse(any("pragma dqc.v1.split" in label for label in dag_labels))
        self.assertGreaterEqual(len(interaction.nodes()), 1)
        self.assertGreaterEqual(len(chunk_graph.edges()), 1)


class GraphLabelRegressionTests(unittest.TestCase):
    def test_wire_label_uses_register_name_instead_of_uid_repr(self) -> None:
        anc = QuantumRegister(2, "anc")
        c = ClassicalRegister(1, "c")

        self.assertEqual(_wire_label(anc[1]), "anc1")
        self.assertEqual(_wire_label(c[0]), "c0")

    def test_multi_qubit_interaction_counts_and_gate_names(self) -> None:
        anc = QuantumRegister(2, "anc")
        qc = QuantumCircuit(anc)
        qc.cx(anc[0], anc[1])
        qc.cz(anc[0], anc[1])

        qubits, interactions = collect_multi_qubit_interactions(qc)

        self.assertEqual(len(qubits), 2)
        self.assertIn((0, 1), interactions)
        self.assertEqual(interactions[(0, 1)]["count"], 2)
        self.assertEqual(interactions[(0, 1)]["gates"], {"cx", "cz"})


if __name__ == "__main__":
    unittest.main()