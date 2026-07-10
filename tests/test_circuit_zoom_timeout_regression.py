from __future__ import annotations

import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app import main_window_clean
from tests._dqc_synthesis import synthesize_dqc_file_from_qasm


class _NeverDoneFuture:
    def done(self) -> bool:
        return False


class CircuitZoomTimeoutRegressionTests(unittest.TestCase):
    def test_circuit_zoom_works_before_and_after_timeout_handling(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]

        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        def _fake_start_runtime_run(self, _result, preferred_backend="MPS", retry_attempted=False) -> None:  # noqa: ANN001
            # Keep construction fast/deterministic for UI regression checks.
            return None

        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            for _ in range(30):
                app.processEvents()

            view = window.circuit_view.view
            scene = view.scene()
            self.assertIsNotNone(scene)
            self.assertFalse(scene.itemsBoundingRect().isNull())

            # Zoom must work while a runtime is considered in progress.
            before_running_zoom = float(view.transform().m11())
            view.zoom(1)
            after_running_zoom = float(view.transform().m11())
            self.assertGreater(after_running_zoom, before_running_zoom)

            # Force timeout branch without spawning a real worker process.
            token = window._runtime_run_token + 1
            window._runtime_run_token = token
            window._runtime_future_token = token
            window._runtime_future = _NeverDoneFuture()
            window._runtime_pending_result = getattr(window, "_latest_result", None)
            window._runtime_run_start_monotonic = time.perf_counter() - (window.timeout_s + 0.5)
            window._refresh_runtime_run_state()

            for _ in range(5):
                app.processEvents()

            # Zoom must still work after timeout handling has executed.
            before_post_timeout_zoom = float(view.transform().m11())
            view.zoom(1)
            after_post_timeout_zoom = float(view.transform().m11())
            self.assertGreater(after_post_timeout_zoom, before_post_timeout_zoom)

            # Zoom must also work after the successful-finish path.
            token_ok = window._runtime_run_token + 1
            window._runtime_run_token = token_ok
            window._runtime_future_token = token_ok
            window._runtime_pending_result = getattr(window, "_latest_result", None)
            window._runtime_run_start_monotonic = time.perf_counter() - 0.1
            window._on_runtime_run_finished(
                token_ok,
                {"0": 1},
                None,
                datetime.now(timezone.utc),
                runtime_backend="MPS",
                runtime_note="",
            )

            before_success_zoom = float(view.transform().m11())
            view.zoom(1)
            after_success_zoom = float(view.transform().m11())
            self.assertGreater(after_success_zoom, before_success_zoom)

            # Regression targets reported as non-timeout but frozen for zoom-in.
            with tempfile.TemporaryDirectory() as temp_dir:
                generated_targets = []
                for relative_qasm, seed in (
                    (Path("qasm/deutsch-jozsa.qasm"), 31),
                    (Path("qasm/qft.qasm"), 37),
                ):
                    target, _ = synthesize_dqc_file_from_qasm(
                        workspace_root / relative_qasm,
                        Path(temp_dir),
                        desired_points=2,
                        seed=seed,
                    )
                    generated_targets.append(target)

                for target in generated_targets:
                    window.load_file(target)
                    for _ in range(15):
                        app.processEvents()
                    before_zoom = float(view.transform().m11())
                    view.zoom(1)
                    after_zoom = float(view.transform().m11())
                    self.assertGreater(after_zoom, before_zoom)
        finally:
            window.close()
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run


if __name__ == "__main__":
    unittest.main()
