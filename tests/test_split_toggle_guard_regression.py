from __future__ import annotations

import os
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app import main_window_clean
from app.pipeline import split_points_from_source


class SplitToggleGuardRegressionTests(unittest.TestCase):
    def test_existing_split_can_be_removed_even_if_guard_blocks_insertions(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        window = main_window_clean.MainWindow(workspace_root)

        original_guard = main_window_clean.line_is_inside_blocking_scope
        try:
            source = "\n".join(
                [
                    "OPENQASM 3.1;",
                    'include "stdgates.inc";',
                    "qubit[1] q;",
                    "pragma dqc.v1.split id=1",
                    "x q[0];",
                ]
            )
            window.current_source = source
            window.original_editor.setPlainText(source)
            window.split_points = split_points_from_source(source)
            self.assertEqual(window.split_points, {4})

            def _always_block(_src: str, _line: int) -> bool:
                return True

            main_window_clean.line_is_inside_blocking_scope = _always_block

            # Click on the pragma line to untoggle/remove it.
            window.toggle_split_point(4)
            for _ in range(5):
                app.processEvents()

            updated = window.original_editor.toPlainText()
            self.assertNotIn("pragma dqc.v1.split", updated)
            self.assertEqual(window.split_points, set())
        finally:
            main_window_clean.line_is_inside_blocking_scope = original_guard
            window.close()


if __name__ == "__main__":
    unittest.main()
