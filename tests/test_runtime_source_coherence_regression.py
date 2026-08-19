"""
Regression guard: circuit drawing, DAG/interaction/chunk graphs, and the
actual runtime execution must all be based on the *same* rewritten code
(the canonical `downstream_rewritten_source` computed in
`rewrite_and_analyze`) whenever "Use rewritten code" is in effect.

This specifically covers a regression where `result.split_qasm` (the source
fed to `run_runtime_counts` by the async runtime executor, and to the
circuit view for barrier coloring) was rebuilt from the always-teleporting
`dqc_qasm`, ignoring rule #11 (split-gen.teleports)'s enabled/disabled state.
Unchecking rule #11 then correctly updated the Rewritten tab and circuit
preview, but the actual runtime execution still ran the teleport-injected
qubits.
"""
from __future__ import annotations

import unittest

from app.pipeline import (
    DEFAULT_RULES,
    RULE_ID_SPLIT_GEN_TELEPORTS,
    RuleState,
    rewrite_and_analyze,
    run_runtime_counts,
    strip_internal_display_markers,
)

SOURCE = "\n".join(
    [
        "OPENQASM 3.1;",
        'include "stdgates.inc";',
        "qubit[2] q;",
        "bit[2] c;",
        "h q[0];",
        "cx q[0], q[1];",
        "measure q[0] -> c[0];",
        "measure q[1] -> c[1];",
    ]
)
SPLIT_BEFORE_CX_LINE = {6}  # splits right before "cx q[0], q[1];", so q[0] must be teleported


def _rules(*, split_gen_teleports_enabled: bool) -> list[RuleState]:
    return [
        RuleState(
            rule.rule_id,
            rule.name,
            rule.description,
            rule.rule_id != 0 and (rule.rule_id != RULE_ID_SPLIT_GEN_TELEPORTS or split_gen_teleports_enabled),
        )
        for rule in DEFAULT_RULES
    ]


class RuntimeSourceCoherenceTests(unittest.TestCase):
    def test_split_qasm_matches_displayed_rewritten_source(self) -> None:
        for enabled in (True, False):
            with self.subTest(split_gen_teleports_enabled=enabled):
                result = rewrite_and_analyze(
                    SOURCE, _rules(split_gen_teleports_enabled=enabled), SPLIT_BEFORE_CX_LINE, {},
                    shots=1, timeout_s=5, execute_runtime=False,
                )
                # split_qasm feeds both the circuit view and the async runtime
                # executor; it must be exactly the displayed Rewritten code
                # (modulo display-only markers), regardless of which rules
                # are enabled.
                self.assertEqual(result.split_qasm, strip_internal_display_markers(result.rewritten_source))

    def test_disabling_split_gen_teleports_removes_teleport_qubits_from_runtime_source(self) -> None:
        enabled_result = rewrite_and_analyze(
            SOURCE, _rules(split_gen_teleports_enabled=True), SPLIT_BEFORE_CX_LINE, {},
            shots=1, timeout_s=5, execute_runtime=False,
        )
        disabled_result = rewrite_and_analyze(
            SOURCE, _rules(split_gen_teleports_enabled=False), SPLIT_BEFORE_CX_LINE, {},
            shots=1, timeout_s=5, execute_runtime=False,
        )

        self.assertIn("_epr_", enabled_result.split_qasm)
        self.assertNotIn("_epr_", disabled_result.split_qasm)
        self.assertNotIn("Teleporting qubits", disabled_result.split_qasm)

    def test_actual_runtime_execution_honors_split_gen_teleports_toggle(self) -> None:
        # Reproduces the exact regression: run the same source fed to the
        # async runtime executor (main_window_clean._start_runtime_run) and
        # confirm the executed circuit's qubit count tracks rule #11's state,
        # instead of always including the teleport-injected qubits.
        enabled_result = rewrite_and_analyze(
            SOURCE, _rules(split_gen_teleports_enabled=True), SPLIT_BEFORE_CX_LINE, {},
            shots=4, timeout_s=10, execute_runtime=False,
        )
        disabled_result = rewrite_and_analyze(
            SOURCE, _rules(split_gen_teleports_enabled=False), SPLIT_BEFORE_CX_LINE, {},
            shots=4, timeout_s=10, execute_runtime=False,
        )

        enabled_counts, enabled_error, *_ = run_runtime_counts(enabled_result.split_qasm, {}, shots=4)
        disabled_counts, disabled_error, *_ = run_runtime_counts(disabled_result.split_qasm, {}, shots=4)

        self.assertIsNone(enabled_error, enabled_error)
        self.assertIsNone(disabled_error, disabled_error)
        enabled_width = len(next(iter(enabled_counts)))
        disabled_width = len(next(iter(disabled_counts)))
        # Teleportation injects extra classical correction bits into the
        # measured bitstring width; disabling rule #11 must shrink it back.
        self.assertGreater(enabled_width, disabled_width)


if __name__ == "__main__":
    unittest.main()
