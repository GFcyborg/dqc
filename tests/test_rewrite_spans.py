from __future__ import annotations

import re
import unittest

from pathlib import Path

from app.pipeline import DEFAULT_RULES, RuleState, build_distributed_qasm, normalize_dqc_clicked_split_line, ordered_active_rule_ids, original_line_rule_matches, rewrite_and_analyze, rewrite_comments_and_blanks, split_points_from_source, substitute_inputs


class RewriteSpanTests(unittest.TestCase):
    def test_split_generated_teleportations_rule_is_present(self) -> None:
        rule_names = {rule.rule_id: rule.name for rule in DEFAULT_RULES}

        self.assertIn(8, rule_names)
        self.assertEqual(rule_names[8], "Split-generated teleportations")
        self.assertIn(6, rule_names)
        self.assertEqual(rule_names[6], "Bit-to-bool Cast")
        self.assertIn(7, rule_names)
        self.assertEqual(rule_names[7], "Uint Workaround")

    def test_rule_eight_is_listed_last_in_default_rules(self) -> None:
        self.assertEqual(DEFAULT_RULES[-1].rule_id, 8)

    def test_default_rule_ids_are_contiguous(self) -> None:
        self.assertEqual([rule.rule_id for rule in DEFAULT_RULES], list(range(len(DEFAULT_RULES))))

    def test_active_rules_are_processed_in_numeric_order(self) -> None:
        rules = [
            RuleState(8, "Split-generated teleportations", "", True),
            RuleState(7, "Uint Workaround", "", True),
            RuleState(6, "Bit-to-bool Cast", "", True),
            RuleState(1, "Drop comments", "", True),
        ]
        self.assertEqual(ordered_active_rule_ids(rules), [1, 6, 7, 8])

    def test_comment_drop_records_visible_and_invisible_spans(self) -> None:
        spans = []
        rewritten = rewrite_comments_and_blanks(["x q[0]; // keep this comment"], True, False, spans)

        self.assertEqual(rewritten, ["x q[0];"])
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].rule_id, 1)
        self.assertIn("keep this comment", spans[0].original)
        self.assertEqual(spans[0].rewritten, "")

    def test_rewrite_and_analyze_preserves_comment_drops_and_insertions(self) -> None:
        source = "\n".join([
            "qubit[1] q;",
            "x q[0]; // keep this comment",
        ])
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=1, timeout_s=1)

        self.assertTrue(result.rewritten_source.startswith('OPENQASM 3.1;\ninclude "stdgates.inc";'))
        self.assertTrue(any(span.rule_id == 1 and span.rewritten == "" for span in result.spans))
        self.assertTrue(any(span.rule_id in {3, 4} and span.rewritten for span in result.spans))

    def test_rewrite_and_analyze_returns_counts_for_teleport_example(self) -> None:
        source = Path("qasm/teleport+.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, True) for rule in DEFAULT_RULES if rule.rule_id != 0]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=1024, timeout_s=10)

        self.assertTrue(result.counts)
        self.assertIn("Measurement outcomes:", __import__("app.pipeline", fromlist=["summary_text"]).summary_text(result, 1024))

    def test_split_pragmas_are_inserted_before_the_split_line(self) -> None:
        raw_source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "x q[0];",
        ])

        dqc_source, dqc_qasm = build_distributed_qasm(raw_source, {4})
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(raw_source, rules, {4}, {}, shots=1, timeout_s=1)

        self.assertEqual(
            dqc_source.splitlines(),
            ["OPENQASM 3.1;", "include \"stdgates.inc\";", "qubit[1] q;", "pragma dqc.v1.split id=1", "x q[0];"],
        )
        self.assertIn("/* Teleporting qubits into chunk 2:", dqc_qasm)
        self.assertRegex(dqc_qasm, r"barrier(?:\s+[^;]+)?;\n/\* Teleporting qubits into chunk 2:")
        self.assertRegex(dqc_qasm, r"\*/\n(?:.*\n)*?barrier(?:\s+[^;]+)?;")
        self.assertIn("qubit q_SOURCE;", dqc_qasm)
        self.assertIn("* q from chunk 1", dqc_qasm)
        self.assertIn("/* Teleporting qubits into chunk 2:", result.rewritten_source)
        self.assertRegex(result.rewritten_source, r"barrier(?:\s+[^;]+)?;\n/\* Teleporting qubits into chunk 2:")
        self.assertRegex(result.rewritten_source, r"\*/\n(?:.*\n)*?barrier(?:\s+[^;]+)?;")
        self.assertIn("qubit q_SOURCE;", result.rewritten_source)
        self.assertIn("* q from chunk 1", result.rewritten_source)
        self.assertEqual(normalize_dqc_clicked_split_line(dqc_source, 4), 4)
        self.assertEqual(normalize_dqc_clicked_split_line(dqc_source, 5), 4)

    def test_split_points_are_derived_from_loaded_dqc_pragmas(self) -> None:
        dqc_source = "\n".join([
            "OPENQASM 3.1;",
            "qubit[1] q;",
            "pragma dqc.v1.split id=1",
            "x q[0];",
        ])

        self.assertEqual(split_points_from_source(dqc_source), {3})

        restored_source, _ = build_distributed_qasm("\n".join([
            "OPENQASM 3.1;",
            "qubit[1] q;",
            "x q[0];",
        ]), split_points_from_source(dqc_source))

        self.assertEqual(
            restored_source.splitlines(),
            ["OPENQASM 3.1;", "qubit[1] q;", "pragma dqc.v1.split id=1", "x q[0];"],
        )

    def test_original_rule_matches_include_split_pragma_as_rule_eight(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "qubit[1] q;",
            "pragma dqc.v1.split id=1",
            "x q[0];",
        ])

        matches = original_line_rule_matches(source)

        self.assertIn(3, matches)
        self.assertTrue(any(rule_id == 8 for rule_id, _, _, _ in matches[3]))

    def test_rule_eight_remaps_split_points_through_header_and_include_insertion(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "qubit[1] q;",
            "x q[0];",
        ])
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]

        result = rewrite_and_analyze(source, rules, {3}, {}, shots=1, timeout_s=1)

        self.assertIn("/* Teleporting qubits into chunk 2:", result.rewritten_source)
        self.assertIn("* q from chunk 1", result.rewritten_source)

    def test_disabled_rule_eight_keeps_pragma_visible_but_runtime_handles_it(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "bit[1] c;",
            "h q[0];",
            "measure q[0] -> c[0];",
        ])
        split_before_lines = {5}
        rules = [
            RuleState(rule.rule_id, rule.name, rule.description, (rule.rule_id != 0 and rule.rule_id != 8))
            for rule in DEFAULT_RULES
        ]

        result = rewrite_and_analyze(source, rules, split_before_lines, {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertIn("pragma dqc.v1.split id=1", result.rewritten_source)
        self.assertFalse(any(issue.kind == "error" and "Runtime execution failed" in issue.message for issue in result.issues))
        self.assertTrue(any("removed" in issue.message and "pragma" in issue.message for issue in result.issues))
        self.assertIsNotNone(result.circuit)

    def test_generic_pragma_does_not_break_circuit_preview(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "bit[1] c;",
            "pragma vendor.custom this should be ignored by qiskit path",
            "h q[0];",
            "measure q[0] -> c[0];",
        ])
        rules = [
            RuleState(rule.rule_id, rule.name, rule.description, (rule.rule_id != 0 and rule.rule_id != 8))
            for rule in DEFAULT_RULES
        ]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertIn("pragma vendor.custom", result.rewritten_source)
        self.assertIsNotNone(result.circuit)
        self.assertTrue(any("removed" in issue.message and "pragma" in issue.message for issue in result.issues))

    def test_generic_pragma_does_not_break_runtime_execution(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "bit[1] c;",
            "pragma vendor.custom runtime pragma should be ignored by qiskit path",
            "h q[0];",
            "measure q[0] -> c[0];",
        ])
        rules = [
            RuleState(rule.rule_id, rule.name, rule.description, (rule.rule_id != 0 and rule.rule_id != 8))
            for rule in DEFAULT_RULES
        ]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=2, execute_runtime=True)

        self.assertIn("pragma vendor.custom", result.rewritten_source)
        self.assertIsNotNone(result.circuit)
        self.assertTrue(result.counts)
        self.assertFalse(any(issue.kind == "error" and "Runtime execution failed" in issue.message for issue in result.issues))
        self.assertTrue(any("removed" in issue.message and "pragma" in issue.message for issue in result.issues))

    def test_bit_to_bool_cast_rewrites_scalar_and_array_element_conditions(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "bit c;",
            "bit[2] mid;",
            "if(c==1) {}",
            "if(mid[0] == 0) {}",
        ])
        rules = [RuleState(rule.rule_id, rule.name, rule.description, True) for rule in DEFAULT_RULES if rule.rule_id != 0]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=1, timeout_s=1)

        self.assertIn("if(c) {}", result.rewritten_source)
        self.assertIn("if(!mid[0]) {}", result.rewritten_source)
        self.assertTrue(any(span.rule_id == 6 and "boolean cast" in span.message for span in result.spans))

    def test_original_line_rule_matches_reports_plural_rule_references(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "bit c;",
            "if(c==1) {} // trailing comment",
            "gate cx a, b { }",
            "",
        ])

        matches = original_line_rule_matches(source)

        self.assertIn(4, matches)
        self.assertTrue(any(rule_id == 1 and source.splitlines()[3][start:end] == "// trailing comment" for rule_id, _, start, end in matches[4]))
        self.assertTrue(any(rule_id == 6 and source.splitlines()[3][start:end] == "c==1" for rule_id, _, start, end in matches[4]))
        self.assertIn(5, matches)
        self.assertTrue(any(rule_id == 5 and source.splitlines()[4][start:end] == "cx" for rule_id, _, start, end in matches[5]))
        self.assertIn(6, matches)
        self.assertTrue(any(rule_id == 2 for rule_id, _, _, _ in matches[6]))

    def test_rename_colliding_cphase_definition_and_references(self) -> None:
        source = Path("qasm/cphase+.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, True) for rule in DEFAULT_RULES if rule.rule_id != 0]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertIn("gate my_cphase(θ) a, b", result.rewritten_source)
        self.assertIn("my_cphase(π / 2) q[0], q[1];", result.rewritten_source)
        self.assertTrue(any(span.rule_id == 5 and "my_cphase" in span.rewritten for span in result.spans))

    def test_original_rule5_marks_definition_and_reference_occurrences(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[2] q;",
            "gate cx a, b { }",
            "cx q[0], q[1];",
        ])

        matches = original_line_rule_matches(source)

        self.assertIn(4, matches)
        self.assertTrue(any(rule_id == 5 and source.splitlines()[3][start:end] == "cx" for rule_id, _, start, end in matches[4]))
        self.assertIn(5, matches)
        self.assertTrue(any(rule_id == 5 and source.splitlines()[4][start:end] == "cx" for rule_id, _, start, end in matches[5]))

    def test_missing_input_defaults_to_pi_over_2_minus_1(self) -> None:
        source = "\n".join([
            "OPENQASM 3.0;",
            "include \"stdgates.inc\";",
            "input float[64] a;",
            "qubit[1] q;",
            "rx(a) q[0];",
        ])

        rewritten = substitute_inputs(source, {})

        self.assertIn("const float[64] a = pi/2 - 1;", rewritten)

    def test_qiskit_example_parses_and_runs_with_default_parameter(self) -> None:
        source = Path("qasm/qiskit-example.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]

        preview = rewrite_and_analyze(source, rules, set(), {}, shots=64, timeout_s=5, execute_runtime=False)
        self.assertIsNotNone(preview.circuit)
        self.assertEqual(getattr(preview.circuit, "num_parameters", 0), 1)

        result = rewrite_and_analyze(source, rules, set(), {"a": "pi/2 - 1"}, shots=64, timeout_s=5, execute_runtime=True)
        self.assertEqual(getattr(result.circuit, "num_parameters", 0), 0)
        self.assertTrue(result.counts)

    def test_adder_uint_workaround_rewrites_and_runs(self) -> None:
        source = Path("qasm/adder.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]

        preview = rewrite_and_analyze(source, rules, set(), {}, shots=32, timeout_s=10, execute_runtime=False)
        self.assertNotIn("uint", preview.rewritten_source)
        self.assertNotIn("for uint", preview.rewritten_source)
        self.assertNotIn("for int", preview.rewritten_source)
        self.assertIn("x a[0];", preview.rewritten_source)
        self.assertIn("x b[0];", preview.rewritten_source)
        self.assertIsNotNone(preview.circuit)
        self.assertTrue(any(span.rule_id == 7 for span in preview.spans))

        result = rewrite_and_analyze(source, rules, set(), {}, shots=32, timeout_s=10, execute_runtime=True)
        self.assertIsNotNone(result.circuit)
        self.assertTrue(result.counts)

    def test_uint_unroll_spans_include_visible_rewritten_lines(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[2] q;",
            "uint[2] a_in = 1;",
            "for uint i in [0: 1] { if(bool(a_in[i])) x q[i]; }",
        ])
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        unroll_spans = [span for span in result.spans if span.rule_id == 7 and "Unrolled uint loop" in span.message]
        self.assertTrue(unroll_spans)
        self.assertTrue(any(span.rewritten.strip() for span in unroll_spans))
        self.assertIn("x q[0];", result.rewritten_source)

    def test_uint_rule_does_not_match_uint_inside_comments(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "// uint in comment only",
            "qubit[1] q; /* uint in block comment */",
            "x q[0];",
        ])

        matches = original_line_rule_matches(source)

        self.assertTrue(any(rule_id == 1 for rule_id, _, _, _ in matches[3]))
        self.assertFalse(any(rule_id == 7 for rule_id, _, _, _ in matches[3]))
        self.assertTrue(any(rule_id == 1 for rule_id, _, _, _ in matches[4]))
        self.assertFalse(any(rule_id == 7 for rule_id, _, _, _ in matches[4]))

    def test_uint_rule_does_not_rewrite_comment_only_uint_mentions(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "// uint value in comment",
            "qubit[1] q;",
            "x q[0];",
        ])
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]

        result = rewrite_and_analyze(source, rules, set(), {}, shots=1, timeout_s=1, execute_runtime=False)

        uint_spans = [span for span in result.spans if span.rule_id == 7]
        self.assertFalse(uint_spans)

    def test_active_rules_apply_in_numeric_order_even_if_input_order_is_shuffled(self) -> None:
        source = "\n".join([
            "qubit[1] q;",
            "",
            "x q[0]; // trailing",
        ])
        rules_shuffled = [
            RuleState(rule_id=4, name="Inject stdgates", description="", enabled=True),
            RuleState(rule_id=2, name="Drop blank lines", description="", enabled=True),
            RuleState(rule_id=1, name="Drop comments", description="", enabled=True),
            RuleState(rule_id=3, name="Inject OPENQASM 3.1", description="", enabled=True),
        ]

        result = rewrite_and_analyze(source, rules_shuffled, set(), {}, shots=1, timeout_s=1, execute_runtime=False)

        expected = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "x q[0];",
        ])
        self.assertEqual(result.rewritten_source, expected)

    def test_chunk_dependencies_track_cross_chunk_variable_use(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "bit[1] c;",
            "h q[0];",
            "measure q[0] -> c[0];",
            "x q[0];",
        ])
        split_before_lines = {7}
        rules = [RuleState(rule.rule_id, rule.name, rule.description, True) for rule in DEFAULT_RULES if rule.rule_id != 0]

        result = rewrite_and_analyze(source, rules, split_before_lines, {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertTrue(result.chunk_flows)
        self.assertEqual(len(result.chunk_flows), 2)
        first_flow = result.chunk_flows[0]
        second_flow = result.chunk_flows[1]
        self.assertIn("q", first_flow.outgoing_targets)
        self.assertIn(2, first_flow.outgoing_targets["q"])
        self.assertIn("q", second_flow.incoming_sources)
        self.assertIn(1, second_flow.incoming_sources["q"])
        self.assertIsNotNone(result.chunk_graph)
        self.assertTrue(result.chunk_graph.has_edge(1, 2))

    def test_rule6_teleport_comments_match_chunk_flow_dependencies(self) -> None:
        source = "\n".join([
            "OPENQASM 3.1;",
            "include \"stdgates.inc\";",
            "qubit[1] q;",
            "qubit[1] anc;",
            "h q[0];",
            "x anc[0];",
            "x q[0];",
        ])
        split_before_lines = {6, 7}
        rules = [RuleState(rule.rule_id, rule.name, rule.description, True) for rule in DEFAULT_RULES if rule.rule_id != 0]

        result = rewrite_and_analyze(source, rules, split_before_lines, {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertEqual(len(result.chunk_flows), 3)
        chunk2 = result.chunk_flows[1]
        chunk3 = result.chunk_flows[2]
        self.assertIn("anc", chunk2.incoming_sources)
        self.assertIn(1, chunk2.incoming_sources["anc"])
        self.assertIn("q", chunk3.incoming_sources)
        self.assertIn(1, chunk3.incoming_sources["q"])

        rewritten = result.rewritten_source
        self.assertGreaterEqual(len(re.findall(r"barrier(?:\s+[^;]+)?;\n/\* Teleporting qubits into chunk", rewritten)), 2)
        self.assertGreaterEqual(len(re.findall(r"\*/\n(?:.*\n)*?barrier(?:\s+[^;]+)?;", rewritten)), 2)
        self.assertGreaterEqual(rewritten.count("qubit q_SOURCE;"), 2)
        self.assertIn("/* Teleporting qubits into chunk 2:", rewritten)
        self.assertIn("* anc from chunk 1", rewritten)
        self.assertIn("/* Teleporting qubits into chunk 3:", rewritten)
        self.assertIn("* q from chunk 1", rewritten)

        self.assertTrue(result.chunk_graph.has_edge(1, 2))
        self.assertTrue(result.chunk_graph.has_edge(1, 3))


if __name__ == "__main__":
    unittest.main()