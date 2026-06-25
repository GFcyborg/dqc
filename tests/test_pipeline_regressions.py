from __future__ import annotations

import unittest
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.circuit import ClassicalRegister, QuantumRegister

from app.pipeline import line_is_inside_blocking_scope, qasm_token_graph, run_runtime_counts, suggest_split_points
from app.widgets import _has_split_generated_barriers, _split_generated_barrier_ordinals, _wire_label, collect_multi_qubit_interactions


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

    def test_split_suggestion_respects_distributed_node_budget(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[3] q;",
                "bit[3] c;",
                "h q[0];",
                "cx q[0], q[1];",
                "cx q[1], q[2];",
                "measure q[0] -> c[0];",
                "measure q[1] -> c[1];",
                "measure q[2] -> c[2];",
            ]
        )

        suggested_two, _ = suggest_split_points(source, distributed_nodes=2)
        suggested_eight, _ = suggest_split_points(source, distributed_nodes=8)

        self.assertLessEqual(len(suggested_two), 1)
        self.assertLessEqual(len(suggested_eight), 7)

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

    def test_runtime_counts_supports_large_qubit_circuits_without_coupling_map_failure(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[42] q;",
                "bit[42] c;",
                "h q[0];",
                "measure q -> c;",
            ]
        )

        counts, error, _ = run_runtime_counts(source, parameter_bindings=None, shots=1)

        if error is not None:
            lowered = error.lower()
            self.assertNotIn("coupling_map", lowered)
            self.assertNotIn("greater than maximum", lowered)
        else:
            self.assertIsNotNone(counts)

    def test_runtime_counts_supports_custom_gate_definitions(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "gate majority a, b, c {",
                "  cx c, b;",
                "  cx c, a;",
                "  ccx a, b, c;",
                "}",
                "qubit[3] q;",
                "bit[3] c;",
                "majority q[0], q[1], q[2];",
                "measure q -> c;",
            ]
        )

        counts, error, _ = run_runtime_counts(source, parameter_bindings=None, shots=1)

        self.assertIsNone(error)
        self.assertIsNotNone(counts)


class GraphLabelRegressionTests(unittest.TestCase):
    def test_wire_label_uses_register_name_instead_of_uid_repr(self) -> None:
        anc = QuantumRegister(2, "anc")
        c = ClassicalRegister(1, "c")

        self.assertEqual(_wire_label(anc[1]), "anc1")
        self.assertEqual(_wire_label(c[0]), "c0")

    def test_wire_label_keeps_scalar_register_name_without_appending_zero(self) -> None:
        split_wire = QuantumRegister(1, "cout0_epr_1")[0]
        split_target_wire = QuantumRegister(1, "cout0_epr_TARGET_1")[0]

        self.assertEqual(_wire_label(split_wire), "cout0_epr_1")
        self.assertEqual(_wire_label(split_target_wire), "cout0_epr_TARGET_1")

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

    def test_detects_split_generated_barrier_signature(self) -> None:
        source_with_split_generated_barrier = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "barrier;",
                "/* Teleporting qubits into chunk 2:",
                " * q from chunk 1",
                " */",
            ]
        )
        source_without_split_generated_barrier = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "barrier q[0];",
                "h q[0];",
            ]
        )

        self.assertTrue(_has_split_generated_barriers(source_with_split_generated_barrier))
        self.assertFalse(_has_split_generated_barriers(source_without_split_generated_barrier))

    def test_detects_only_split_generated_barrier_ordinals(self) -> None:
        mixed_source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "barrier q;",
                "h q[0];",
                "barrier q;",
                "/* Teleporting qubits into chunk 2:",
                " * q from chunk 1",
                " */",
                "barrier q;",
                "/* Teleporting qubits into chunk 3:",
                " * q from chunk 2",
                " */",
            ]
        )

        self.assertEqual(_split_generated_barrier_ordinals(mixed_source), {2, 3})


if __name__ == "__main__":
    unittest.main()