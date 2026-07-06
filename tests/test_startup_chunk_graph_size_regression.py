from __future__ import annotations

import os
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app import main_window_clean


class StartupChunkGraphSizeRegressionTests(unittest.TestCase):
    @staticmethod
    def _assert_chunk_view_is_fit(view) -> None:  # noqa: ANN001
        scene_rect = view.sceneRect()
        viewport = view.viewport()
        scene_w = float(scene_rect.width())
        scene_h = float(scene_rect.height())
        view_w = float(view.width())
        view_h = float(view.height())
        assert scene_w > 0 and scene_h > 0 and view_w > 0 and view_h > 0

        fit_scale = min(view_w / scene_w, view_h / scene_h)
        current_scale = float(view.transform().m11())

        # Must be at (or very near) fit scale, not oversized.
        assert current_scale <= fit_scale * 1.06
        assert current_scale >= fit_scale * 0.80

        # Oversized initial render usually manifests as non-zero scrollbar range.
        assert view.horizontalScrollBar().maximum() == 0

    def test_startup_chunk_graph_refits_after_initial_geometry_settle(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        workspace_root = Path(__file__).resolve().parents[1]
        bell_state = workspace_root / "qasm" / "bell_state.qasm"
        self.assertTrue(bell_state.exists())

        original_start_runtime_run = main_window_clean.MainWindow._start_runtime_run

        def _fake_start_runtime_run(self, _result, preferred_backend="MPS", retry_attempted=False) -> None:  # noqa: ANN001
            return None

        main_window_clean.MainWindow._start_runtime_run = _fake_start_runtime_run

        window = main_window_clean.MainWindow(workspace_root)
        try:
            for _ in range(40):
                app.processEvents()

            chunk_view = window.chunk_graph_view.view
            self._assert_chunk_view_is_fit(chunk_view)

            # Simulate startup geometry changes (splitter settles / user resize).
            window.resize(max(900, int(window.width() * 0.78)), max(700, int(window.height() * 0.74)))
            for _ in range(30):
                app.processEvents()

            self._assert_chunk_view_is_fit(chunk_view)

            window.load_file(bell_state)
            for _ in range(30):
                app.processEvents()

            self._assert_chunk_view_is_fit(chunk_view)
        finally:
            window.close()
            main_window_clean.MainWindow._start_runtime_run = original_start_runtime_run


if __name__ == "__main__":
    unittest.main()
