from __future__ import annotations

import os
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog

from app import main_window_clean
from app.pipeline import scan_inputs


class ParameterPromptRegressionTests(unittest.TestCase):
    def test_parametric_file_load_prompts_once_even_with_stale_refresh(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        param_file = workspace_root / "qasm" / "split" / "qiskit-example" / "qiskit-example.dqc"
        self.assertTrue(param_file.exists())
        self.assertTrue(bool(scan_inputs(param_file.read_text(encoding="utf-8"))))

        prompt_calls = {"count": 0}
        original_exec = main_window_clean.ParameterDialog.exec
        original_values = main_window_clean.ParameterDialog.values
        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        def _fake_exec(self) -> int:  # noqa: ANN001
            prompt_calls["count"] += 1
            return QDialog.DialogCode.Accepted

        def _fake_values(self) -> dict[str, str]:  # noqa: ANN001
            return {name: "pi/2 - 1" for name in getattr(self, "_edits", {})}

        def _fake_start_runtime_run(self, _result) -> None:  # noqa: ANN001
            return None

        main_window_clean.ParameterDialog.exec = _fake_exec
        main_window_clean.ParameterDialog.values = _fake_values
        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            # Simulate an already-queued refresh from prior edits, then load a parametric file.
            window._schedule_refresh()
            window.load_file(param_file)

            for _ in range(20):
                app.processEvents()

            self.assertEqual(prompt_calls["count"], 1)
        finally:
            window.close()
            main_window_clean.ParameterDialog.exec = original_exec
            main_window_clean.ParameterDialog.values = original_values
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run


if __name__ == "__main__":
    unittest.main()
