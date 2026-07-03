from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.pipeline import DEFAULT_RULES, RewriteSpan, RuleState, rewrite_and_analyze, split_points_from_source
from app.widgets import HtmlCodeView


class _CaptureHtmlCodeView(HtmlCodeView):
    def __init__(self) -> None:
        super().__init__()
        self.captured_html = ""

    def setHtml(self, text: str) -> None:  # noqa: N802
        self.captured_html = text
        super().setHtml(text)


class RewrittenColoringRegressionTests(unittest.TestCase):
    def test_non_teleport_rules_render_green_and_rule9_renders_orange(self) -> None:
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
                "let tmpConcat1 = q[1] ++ q[2];",
                "/* Teleporting qubits into chunk 2:",
                " * q[0] from chunk 1",
                " */",
            ]
        )
        spans = [
            RewriteSpan(1, "", "OPENQASM 3.1;", 3, "Inserted missing OPENQASM header."),
            RewriteSpan(2, "", 'include "stdgates.inc";', 4, "Inserted stdgates include."),
            RewriteSpan(3, "gate cx a, b { }", "gate my_cx a, b { }", 5, "Renamed colliding gate."),
            RewriteSpan(4, "if(c==1) {}", "if(c) {}", 6, "Rewrote bit comparison to a boolean cast."),
            RewriteSpan(5, "x q[i];", "x q[0];", 7, "Applied uint compatibility rewrite."),
            RewriteSpan(
                6,
                "my_gate(a * 2) aliased[0], q[{1, 2}][0];",
                "let tmpConcat1 = q[1] ++ q[2];\nmy_gate(a * 2) aliased[0], tmpConcat1[0];",
                8,
                "Expanded array-index set with temporary identifier for gate-operand compatibility.",
            ),
            RewriteSpan(
                7,
                "pragma dqc.v1.split id=1",
                "/* Teleporting qubits into chunk 2:\n * q[0] from chunk 1\n */",
                9,
                "split pragma rewritten into teleportation comment block",
            ),
        ]

        view.set_rewrite_result(rewritten_source, spans)
        html = view.captured_html

        # Non-teleport rewritten outputs should stay green.
        self.assertIn("<span style='color:#22c55e'>OPENQASM 3.1;</span>", html)
        self.assertIn("<span style='color:#22c55e'>include &quot;stdgates.inc&quot;;</span>", html)
        self.assertIn("<span style='color:#22c55e'>my_</span>", html)
        self.assertIn("<span style='color:#22c55e'>if(c) {}</span>", html)
        self.assertIn("<span style='color:#22c55e'>let tmpConcat1 = q[1] ++ q[2];</span>", html)

        # Split-generated teleport content should stay orange.
        self.assertIn("<span style='color:#ca8a04'>/* Teleporting qubits into chunk 2:</span>", html)
        self.assertIn("<span style='color:#ca8a04'> * q[0] from chunk 1</span>", html)

    def test_rule5_reference_stays_green_in_dqc_after_rule9_inserts_blocks(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        _app = QApplication.instance() or QApplication([])

        source = Path("qasm/split/cphase+/cphase+.dqc").read_text(encoding="utf-8")
        split_lines = split_points_from_source(source)
        rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0) for rule in DEFAULT_RULES]
        result = rewrite_and_analyze(source, rules, split_lines, {}, shots=1, timeout_s=2, execute_runtime=False)

        view = _CaptureHtmlCodeView()
        view.set_rewrite_result(result.rewritten_source, result.spans)
        html = view.captured_html

        # The usage occurrence (line 13 in original .dqc source) remains snippet-green
        # even after split-generated blocks shift line numbers in rewritten output.
        self.assertIn("<span style='color:#22c55e'>my_</span>cphase(π / 2) q[0], q[1];", html)


if __name__ == "__main__":
    unittest.main()
