from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from app import main_window_clean


class SaveSplitDumpRegressionTests(unittest.TestCase):
    def test_rewritten_text_strips_display_only_teleport_sentinel(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        window = main_window_clean.MainWindow(workspace_root)
        try:
            raw_with_marker = "\n".join(
                [
                    "/* Teleporting qubits into chunk 2:",
                    " * q[0] from chunk 1",
                    " */",
                    "cx q[0], q0_epr_1;",
                    "// <dqc:teleport-end>",
                    "x q0_epr_TARGET_1;",
                ]
            )
            window._latest_result = SimpleNamespace(rewritten_source=raw_with_marker)

            cleaned = window.rewritten_text()
            self.assertFalse(main_window_clean.contains_internal_display_markers(cleaned))
            self.assertIn("cx q[0], q0_epr_1;", cleaned)
            self.assertIn("x q0_epr_TARGET_1;", cleaned)
        finally:
            window.close()
            app.processEvents()

    def test_persisted_dqc_qasm_matches_rewritten_view(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_build_distributed_qasm = main_window_clean.build_distributed_qasm

        def _fake_build_distributed_qasm(_source: str, _split_points: set[int]):
            return "OPENQASM 3.1;\npragma dqc.v1.split id=1\nx q[0];", "SHOULD_NOT_BE_PERSISTED"

        main_window_clean.build_distributed_qasm = _fake_build_distributed_qasm
        window = main_window_clean.MainWindow(workspace_root)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                window.split_root = Path(temp_dir)
                window.current_file = workspace_root / "qasm" / "bell_state.qasm"
                raw_with_split = "\n".join(
                    [
                        "OPENQASM 3.1;",
                        'include "stdgates.inc";',
                        "qubit[2] q;",
                        "h q[0];",
                        "pragma dqc.v1.split id=1",
                        "h q[1];",
                    ]
                )
                window.current_source = raw_with_split
                window.original_editor.setPlainText(raw_with_split)
                window.split_points = {5}
                rewritten_with_marker = "\n".join(
                    [
                        "OPENQASM 3.1;",
                        'include "stdgates.inc";',
                        "qubit[2] q;",
                        "// rewritten with active rules",
                        "// <dqc:teleport-end>",
                        "h q[0];",
                    ]
                )
                expected_rewritten = "\n".join(
                    [
                        "OPENQASM 3.1;",
                        'include "stdgates.inc";',
                        "qubit[2] q;",
                        "// rewritten with active rules",
                        "h q[0];",
                    ]
                )
                window._latest_result = SimpleNamespace(rewritten_source=rewritten_with_marker)

                saved_dqc = window._persist_split_artifacts()
                self.assertIsNotNone(saved_dqc)
                qasm_dump_path = Path(saved_dqc.parent) / f"{window.current_file.stem}.dqc.qasm"
                self.assertEqual(main_window_clean.read_text(qasm_dump_path), expected_rewritten)
                self.assertFalse(main_window_clean.contains_internal_display_markers(main_window_clean.read_text(qasm_dump_path)))
        finally:
            window.close()
            main_window_clean.build_distributed_qasm = original_build_distributed_qasm
            app.processEvents()

    def test_persist_split_artifacts_raises_when_saved_dump_mismatches_rewritten(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_read_text = main_window_clean.read_text

        def _fake_read_text(path: Path) -> str:
            if str(path).endswith(".dqc.qasm"):
                return "CORRUPTED_DUMP"
            return original_read_text(path)

        main_window_clean.read_text = _fake_read_text
        window = main_window_clean.MainWindow(workspace_root)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                window.split_root = Path(temp_dir)
                window.current_file = workspace_root / "qasm" / "bell_state.qasm"
                raw_with_split = "\n".join(
                    [
                        "OPENQASM 3.1;",
                        'include "stdgates.inc";',
                        "qubit[2] q;",
                        "h q[0];",
                        "pragma dqc.v1.split id=1",
                        "h q[1];",
                    ]
                )
                window.current_source = raw_with_split
                window.original_editor.setPlainText(raw_with_split)
                window.split_points = {5}
                window._latest_result = SimpleNamespace(
                    rewritten_source="\n".join(
                        [
                            "OPENQASM 3.1;",
                            'include "stdgates.inc";',
                            "qubit[2] q;",
                            "h q[0];",
                        ]
                    )
                )

                with self.assertRaises(RuntimeError):
                    window._persist_split_artifacts()
        finally:
            window.close()
            main_window_clean.read_text = original_read_text
            app.processEvents()

    def test_persist_split_artifacts_raises_when_saved_dump_contains_sentinel(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_read_text = main_window_clean.read_text

        def _fake_read_text(path: Path) -> str:
            if str(path).endswith(".dqc.qasm"):
                return "\n".join(["OPENQASM 3.1;", "// <dqc:teleport-end>"])
            return original_read_text(path)

        main_window_clean.read_text = _fake_read_text
        window = main_window_clean.MainWindow(workspace_root)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                window.split_root = Path(temp_dir)
                window.current_file = workspace_root / "qasm" / "bell_state.qasm"
                raw_with_split = "\n".join(
                    [
                        "OPENQASM 3.1;",
                        'include "stdgates.inc";',
                        "qubit[2] q;",
                        "h q[0];",
                        "pragma dqc.v1.split id=1",
                        "h q[1];",
                    ]
                )
                window.current_source = raw_with_split
                window.original_editor.setPlainText(raw_with_split)
                window.split_points = {5}
                window._latest_result = SimpleNamespace(
                    rewritten_source="\n".join(
                        [
                            "OPENQASM 3.1;",
                            'include "stdgates.inc";',
                            "qubit[2] q;",
                            "h q[0];",
                        ]
                    )
                )

                with self.assertRaises(RuntimeError):
                    window._persist_split_artifacts()
        finally:
            window.close()
            main_window_clean.read_text = original_read_text
            app.processEvents()

    def test_rewrite_and_analyze_split_qasm_is_marker_free(self) -> None:
        source = "\n".join(
            [
                "OPENQASM 3.1;",
                'include "stdgates.inc";',
                "qubit[1] q;",
                "h q[0];",
                "x q[0];",
            ]
        )
        rules = [
            main_window_clean.RuleState(rule.rule_id, rule.name, rule.description, (rule.rule_id != 0))
            for rule in main_window_clean.DEFAULT_RULES
        ]

        result = main_window_clean.rewrite_and_analyze(source, rules, {5}, {}, shots=1, timeout_s=1, execute_runtime=False)

        self.assertFalse(main_window_clean.contains_internal_display_markers(result.split_qasm))


if __name__ == "__main__":
    unittest.main()
