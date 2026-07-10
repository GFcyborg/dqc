from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.pipeline import DEFAULT_RULES, RewriteSpan, RuleState, rewrite_and_analyze, split_points_from_source
from app.widgets import HtmlCodeView
from tests._dqc_synthesis import synthesize_dqc_source_from_qasm


class _CaptureHtmlCodeView(HtmlCodeView):
    def __init__(self) -> None:
        super().__init__()
        self.captured_html = ""

    def setHtml(self, text: str) -> None:  # noqa: N802
        self.captured_html = text
        super().setHtml(text)


class RewrittenColoringRegressionTests(unittest.TestCase):
    def test_non_teleport_rules_render_green_and_rule11_renders_orange(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        view = _CaptureHtmlCodeView()
        rewritten_source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "gate my_cx a, b { }",
                "if(c) {}",
                "x q[0];",
                "my_gate(a * 2) q[1], q[1];",
                "/* Teleporting qubits into chunk 2:",
                " * q[0] from chunk 1",
                " */",
            ]
        )
        spans = [
            RewriteSpan(1, "", "OPENQASM 3.1;", 3, "Inserted missing OPENQASM header."),
            RewriteSpan(2, "", 'include "stdgates.inc";', 4, "Inserted stdgates include."),
            RewriteSpan(3, "gate cx a, b { }", "gate my_cx a, b { }", 5, "Renamed colliding gate."),
            RewriteSpan(4, "if(c==1) {}", "c", 6, "Rewrote bit comparison to a boolean cast."),
            RewriteSpan(5, "x q[i];", "x q[0];", 7, "Applied uint compatibility rewrite."),
            RewriteSpan(
                6,
                "let aliased = q[1:2];",
                "",
                8,
                "Inlined and removed let alias `aliased` declaration.",
            ),
            RewriteSpan(
                6,
                "q[{1, 2}][0]",
                "q[1]",
                9,
                "Resolved chained indexing into direct element access.",
            ),
            RewriteSpan(
                8,
                "pragma dqc.v1.split id=1",
                "/* Teleporting qubits into chunk 2:\n * q[0] from chunk 1\n */",
                11,
                "split pragma rewritten into teleportation comment block",
            ),
        ]

        view.set_rewrite_result(rewritten_source, spans)
        html = view.captured_html

        # Non-teleport rewritten outputs should stay green.
        self.assertIn("<span style='color:#22c55e'>OPENQASM 3.1;</span>", html)
        self.assertIn("<span style='color:#22c55e'>include &quot;stdgates.inc&quot;;</span>", html)
        self.assertIn("<span style='color:#22c55e'>my_</span>", html)
        self.assertIn("if(<span style='color:#22c55e'>c</span>) {}", html)
        self.assertIn("my_gate(a * 2) <span style='color:#22c55e'>q[1]</span>, q[1];", html)
        self.assertNotIn("<span style='color:#22c55e'>my_gate(a * 2) q[1], q[1];</span>", html)

        # Split-generated teleport content should stay orange.
        self.assertIn("<span style='color:#ca8a04'>/* Teleporting qubits into chunk 2:</span>", html)
        self.assertIn("<span style='color:#ca8a04'> * q[0] from chunk 1</span>", html)

    def test_rule5_reference_stays_green_in_dqc_after_rule9_inserts_blocks(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        qasm_source = Path("qasm/cphase+.qasm").read_text(encoding="utf-8")
        source, _ = synthesize_dqc_source_from_qasm(qasm_source, desired_points=1, seed=29)
        split_lines = split_points_from_source(source)
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, split_lines, {}, shots=1, timeout_s=2, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        # The usage occurrence (line 13 in original .dqc source) remains snippet-green
        # even after split-generated blocks shift line numbers in rewritten output.
        self.assertIn("<span style='color:#22c55e'>my_</span>cphase(π / 2) q[0], q[1];", html)

    def test_qiskit_example_rule8_rule9_snippets_highlight_on_benchmark_lines(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/qiskit-example.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertIn("my_gate(a * 2) <span style='color:#22c55e'>q[0]</span>, <span style='color:#22c55e'>q[1]</span>;", html)
        self.assertIn("if (mid[0]) {\n  <span style='color:#22c55e'>reset q[0];</span>\n  <span style='color:#22c55e'>reset q[1];</span>", html)

    def test_rule6_highlights_if_guards_not_bit_declarations_in_teleport(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/teleport.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertNotIn("bit <span style='color:#22c55e'>c0</span>;", html)
        self.assertNotIn("bit <span style='color:#22c55e'>c1</span>;", html)
        self.assertIn("if(<span style='color:#22c55e'>c0</span>) z q[2];", html)
        self.assertIn("if(<span style='color:#22c55e'>c1</span>) { x q[2]; }", html)

    def test_rule6_highlights_inverseqft2_conditions_not_c2_declaration(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/inverseqft2.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertNotIn("bit <span style='color:#22c55e'>c2</span>;", html)
        self.assertIn("if(<span style='color:#22c55e'>c0</span>) { rz(pi / 4) q[2]; }", html)
        self.assertIn("if(<span style='color:#22c55e'>c2</span>) { rz(pi / 2) q[3]; }", html)

    def test_rule10_does_not_false_highlight_non_rewritten_qft_line(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/qft.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertNotIn("<span style='color:#22c55e'>cphase(pi / 4) q[3], q[1];</span>", html)
        self.assertIn("cphase(pi / 4) q[3], q[1];", html)

    def test_rule10_broadcast_coloring_stays_on_expansion_lines_only(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/adder.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertIn("<span style='color:#22c55e'>reset b[1];</span>", html)

        line_no = next(index + 1 for index, line in enumerate(result.rewritten_source.splitlines()) if line.strip() == "reset b[1];")
        tooltip = view._line_tooltips.get(line_no, "")
        self.assertIn("Rule 10", tooltip)
        self.assertNotIn("Rule 7", tooltip)

    def test_rule10_does_not_color_single_qubit_resets_in_qiskit_example(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/qiskit-example.qasm").read_text(encoding="utf-8")
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, set(), {}, shots=8, timeout_s=5, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        self.assertIn("while (mid == &quot;00&quot;) {\n  reset q[0];\n  reset q[1];\n  my_gate(a) q[0], q[1];", html)
        self.assertNotIn("while (mid == &quot;00&quot;) {\n  <span style='color:#22c55e'>reset q[0];</span>", html)


if __name__ == "__main__":
    unittest.main()
