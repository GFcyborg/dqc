from __future__ import annotations

import os
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from app import main_window_clean


class LoadFileVisualFeedbackRegressionTests(unittest.TestCase):
    @staticmethod
    def _scene_texts(scene) -> list[str]:  # noqa: ANN001
        texts: list[str] = []
        for item in scene.items():
            if hasattr(item, "toPlainText"):
                text = str(item.toPlainText() or "").strip()
            elif hasattr(item, "text"):
                text = str(item.text() or "").strip()
            else:
                continue
            if text:
                texts.append(text)
        return texts

    def test_load_file_blanks_previous_views_and_shows_loading_feedback_before_refresh(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        target_file = workspace_root / "qasm" / "qft.qasm"
        self.assertTrue(target_file.exists())

        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        def _fake_start_runtime_run(self, _result, preferred_backend="MPS", retry_attempted=False) -> None:  # noqa: ANN001
            return None

        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run
        window = main_window_clean.MainWindow(workspace_root)
        try:
            captured: dict[str, object] = {"calls": 0}

            def _fake_refresh(self) -> None:  # noqa: ANN001
                captured["calls"] = int(captured.get("calls", 0)) + 1
                captured["runtime"] = self.runtime_output.toPlainText()
                captured["rewritten"] = self.rewritten_view.toPlainText()
                captured["circuit"] = LoadFileVisualFeedbackRegressionTests._scene_texts(self.circuit_view.view.scene())
                captured["overall"] = LoadFileVisualFeedbackRegressionTests._scene_texts(self.overall_dag_view.view.scene())
                captured["qubit"] = LoadFileVisualFeedbackRegressionTests._scene_texts(self.qubit_graph_view.view.scene())
                captured["chunk"] = LoadFileVisualFeedbackRegressionTests._scene_texts(self.chunk_graph_view.view.scene())

            window.refresh = types.MethodType(_fake_refresh, window)

            window.runtime_output.setPlainText("old runtime output")
            window.rewritten_view.set_rewrite_result("old rewritten text", [])

            window.load_file(target_file)
            for _ in range(5):
                app.processEvents()

            self.assertEqual(captured["calls"], 1)
            runtime_text = str(captured["runtime"])
            self.assertIn("Loading qft.qasm", runtime_text)
            self.assertIn("Please wait while code and graphs are prepared.", runtime_text)
            self.assertEqual(str(captured["rewritten"]), "")
        finally:
            window.close()
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run

    def test_circuit_loading_spinner_ticks_frames(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        window = main_window_clean.MainWindow(workspace_root)
        try:
            window._start_circuit_loading_indicator()
            first = window._circuit_loading_indicator.text()
            window._tick_circuit_loading_indicator()
            second = window._circuit_loading_indicator.text()
            self.assertTrue(first.startswith("Loading circuit"))
            self.assertTrue(second.startswith("Loading circuit"))
            self.assertNotEqual(first, second)
            self.assertTrue(window._circuit_loading_indicator.isVisible())
            window._stop_circuit_loading_indicator()
            app.processEvents()
            self.assertFalse(window._circuit_loading_indicator.isVisible())
        finally:
            window.close()

    def test_run_now_shows_stopwatch_immediately_before_analysis_completes(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_rewrite_and_analyze = main_window_clean.rewrite_and_analyze

        captured = {"visible_during_analysis": False}

        def _fake_rewrite_and_analyze(*args, **kwargs):  # noqa: ANN001
            captured["visible_during_analysis"] = bool(window._runtime_stopwatch_label.isVisible())
            return SimpleNamespace(
                parse_tree=None,
                rewritten_source="",
                spans=[],
                fallback_events=[],
                suggested_split_points=[],
                circuit=None,
                split_qasm="",
                issues=[],
                dag_graph=None,
                interaction_graph=None,
                chunk_graph=None,
                chunk_flows=[],
                suggestion_reason="",
            )

        main_window_clean.rewrite_and_analyze = _fake_rewrite_and_analyze
        window = main_window_clean.MainWindow(workspace_root)
        try:
            window.parameter_bindings = {"a": "0.5"}
            window.run_manual()
            for _ in range(3):
                app.processEvents()
            self.assertTrue(captured["visible_during_analysis"])
        finally:
            window.close()
            main_window_clean.rewrite_and_analyze = original_rewrite_and_analyze

    def test_parameter_accept_refresh_shows_stopwatch_immediately(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_rewrite_and_analyze = main_window_clean.rewrite_and_analyze
        original_scan_inputs = main_window_clean.scan_inputs
        original_exec = main_window_clean.ParameterDialog.exec
        original_values = main_window_clean.ParameterDialog.values

        captured = {"visible_during_analysis": False}

        def _fake_rewrite_and_analyze(*args, **kwargs):  # noqa: ANN001
            captured["visible_during_analysis"] = bool(window._runtime_stopwatch_label.isVisible())
            return SimpleNamespace(
                parse_tree=None,
                rewritten_source="",
                spans=[],
                fallback_events=[],
                suggested_split_points=[],
                circuit=None,
                split_qasm="",
                issues=[],
                dag_graph=None,
                interaction_graph=None,
                chunk_graph=None,
                chunk_flows=[],
                suggestion_reason="",
            )

        def _fake_scan_inputs(_source: str):  # noqa: ANN001
            return ["a"]

        def _fake_exec(self) -> int:  # noqa: ANN001
            return main_window_clean.QDialog.DialogCode.Accepted

        def _fake_values(self) -> dict[str, str]:  # noqa: ANN001
            return {"a": "0.5"}

        main_window_clean.rewrite_and_analyze = _fake_rewrite_and_analyze
        main_window_clean.scan_inputs = _fake_scan_inputs
        main_window_clean.ParameterDialog.exec = _fake_exec
        main_window_clean.ParameterDialog.values = _fake_values
        window = main_window_clean.MainWindow(workspace_root)
        try:
            # Exercise the actual parameter-accept flow used by parametric file loads.
            window.parameter_bindings = {}
            window._prompt_for_parameters(force=True)
            for _ in range(3):
                app.processEvents()
            self.assertTrue(captured["visible_during_analysis"])
        finally:
            window.close()
            main_window_clean.rewrite_and_analyze = original_rewrite_and_analyze
            main_window_clean.scan_inputs = original_scan_inputs
            main_window_clean.ParameterDialog.exec = original_exec
            main_window_clean.ParameterDialog.values = original_values

    def test_runtime_settings_actions_do_not_start_run(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_rewrite_and_analyze = main_window_clean.rewrite_and_analyze
        original_get_int = main_window_clean.QInputDialog.getInt
        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        calls = {"start_runtime": 0}

        def _fake_rewrite_and_analyze(*args, **kwargs):  # noqa: ANN001
            return SimpleNamespace(
                parse_tree=None,
                rewritten_source="",
                spans=[],
                fallback_events=[],
                suggested_split_points=[],
                circuit=object(),
                split_qasm="",
                issues=[],
                dag_graph=None,
                interaction_graph=None,
                chunk_graph=None,
                chunk_flows=[],
                suggestion_reason="",
            )

        def _fake_get_int(parent, title, label, value, minimum, maximum, step):  # noqa: ANN001
            if "shots" in str(title).lower():
                return value + 1, True
            if "distrib.qpus" in str(title).lower():
                return min(maximum, value + 1), True
            return value, False

        def _fake_start_runtime_run(self, result, preferred_backend="MPS", retry_attempted=False):  # noqa: ANN001
            calls["start_runtime"] += 1
            return None

        main_window_clean.rewrite_and_analyze = _fake_rewrite_and_analyze
        main_window_clean.QInputDialog.getInt = _fake_get_int
        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            calls["start_runtime"] = 0
            window.change_shots()
            window.change_distributed_nodes()
            for _ in range(5):
                app.processEvents()
            self.assertEqual(calls["start_runtime"], 0)
        finally:
            window.close()
            main_window_clean.rewrite_and_analyze = original_rewrite_and_analyze
            main_window_clean.QInputDialog.getInt = original_get_int
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run

    def test_runtime_tick_forces_stopwatch_visible_when_run_active(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        window = main_window_clean.MainWindow(workspace_root)
        try:
            # Simulate an active runtime session whose label got hidden by another path.
            window._runtime_run_start_monotonic = 1.0
            window._runtime_stopwatch_label.setVisible(False)
            original_perf_counter = main_window_clean.time.perf_counter
            main_window_clean.time.perf_counter = lambda: 2.0
            try:
                window._refresh_runtime_run_state()
            finally:
                main_window_clean.time.perf_counter = original_perf_counter

            for _ in range(2):
                app.processEvents()
            self.assertTrue(window._runtime_stopwatch_label.isVisible())
        finally:
            window.close()

    def test_change_shots_updates_labels_without_reanalysis(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        original_rewrite_and_analyze = main_window_clean.rewrite_and_analyze
        original_get_int = main_window_clean.QInputDialog.getInt
        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        calls = {"rewrite": 0, "run": 0}

        def _fake_rewrite_and_analyze(*args, **kwargs):  # noqa: ANN001
            calls["rewrite"] += 1
            return SimpleNamespace(
                parse_tree=None,
                rewritten_source="",
                spans=[],
                fallback_events=[],
                suggested_split_points=[],
                circuit=None,
                split_qasm="",
                issues=[],
                dag_graph=None,
                interaction_graph=None,
                chunk_graph=None,
                chunk_flows=[],
                suggestion_reason="",
            )

        def _fake_get_int(parent, title, label, value, minimum, maximum, step):  # noqa: ANN001
            return value + 128, True

        def _fake_start_runtime_run(self, result, preferred_backend="MPS", retry_attempted=False):  # noqa: ANN001
            calls["run"] += 1
            return None

        main_window_clean.rewrite_and_analyze = _fake_rewrite_and_analyze
        main_window_clean.QInputDialog.getInt = _fake_get_int
        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            baseline_rewrite_calls = calls["rewrite"]
            baseline_run_calls = calls["run"]
            old_shots = window.shots

            window.change_shots()
            for _ in range(3):
                app.processEvents()

            self.assertEqual(window.shots, old_shots + 128)
            self.assertEqual(calls["rewrite"], baseline_rewrite_calls)
            self.assertEqual(calls["run"], baseline_run_calls)
            self.assertIn(str(window.shots), window._runtime_shots_label())
        finally:
            window.close()
            main_window_clean.rewrite_and_analyze = original_rewrite_and_analyze
            main_window_clean.QInputDialog.getInt = original_get_int
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run

    def test_dqc_load_runtime_start_sees_stopwatch_visible(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        dqc_candidates = sorted((workspace_root / "qasm").rglob("*.dqc"))
        self.assertTrue(dqc_candidates)
        dqc_file = dqc_candidates[0]

        original_scan_inputs = main_window_clean.scan_inputs
        original_exec = main_window_clean.ParameterDialog.exec
        original_values = main_window_clean.ParameterDialog.values
        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        captured = {"visible_at_start": False, "called": 0}

        def _fake_scan_inputs(source: str):  # noqa: ANN001
            # Force prompt path for .dqc load; after dialog acceptance,
            # runtime still starts because parameter_bindings becomes non-empty.
            if "pragma dqc.v1.split" in source:
                return ["a"]
            return []

        def _fake_exec(self) -> int:  # noqa: ANN001
            return main_window_clean.QDialog.DialogCode.Accepted

        def _fake_values(self) -> dict[str, str]:  # noqa: ANN001
            return {"a": "0.5"}

        def _fake_start_runtime_run(self, result, preferred_backend="MPS", retry_attempted=False):  # noqa: ANN001
            captured["called"] += 1
            captured["visible_at_start"] = bool(self._runtime_stopwatch_label.isVisible())
            return None

        main_window_clean.scan_inputs = _fake_scan_inputs
        main_window_clean.ParameterDialog.exec = _fake_exec
        main_window_clean.ParameterDialog.values = _fake_values
        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            window.load_file(dqc_file)
            for _ in range(20):
                app.processEvents()

            self.assertGreaterEqual(captured["called"], 1)
            self.assertTrue(captured["visible_at_start"])
        finally:
            window.close()
            main_window_clean.scan_inputs = original_scan_inputs
            main_window_clean.ParameterDialog.exec = original_exec
            main_window_clean.ParameterDialog.values = original_values
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run


if __name__ == "__main__":
    unittest.main()
