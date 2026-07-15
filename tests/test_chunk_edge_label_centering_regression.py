from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

from PySide6.QtCore import QPointF
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QGraphicsItem, QGraphicsItemGroup, QGraphicsLineItem, QGraphicsSimpleTextItem

from app.widgets import ChunkDagView


class ChunkEdgeLabelCenteringRegressionTests(unittest.TestCase):
    @staticmethod
    def _assert_label_centered_along_edge(view: ChunkDagView, label_text: str, tolerance_px: float = 4.0) -> None:
        scene = view.scene()
        assert scene is not None

        line_items = [
            item
            for item in scene.items()
            if isinstance(item, QGraphicsLineItem) and item.toolTip() == label_text
        ]
        text_items = [
            item
            for item in scene.items()
            if isinstance(item, QGraphicsSimpleTextItem) and item.text() == label_text
        ]

        assert line_items, f"No edge line found for label: {label_text}"
        assert text_items, f"No text item found for label: {label_text}"

        line_item = line_items[0]
        text_item = text_items[0]

        line = line_item.line()
        x1, y1 = float(line.x1()), float(line.y1())
        x2, y2 = float(line.x2()), float(line.y2())
        dx = x2 - x1
        dy = y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        assert length > 1e-6

        ux = dx / length
        uy = dy / length
        center = text_item.sceneBoundingRect().center()
        proj = (float(center.x()) - x1) * ux + (float(center.y()) - y1) * uy
        midpoint_proj = length * 0.5

        assert abs(proj - midpoint_proj) <= tolerance_px

    def test_chunk_edge_label_stays_centered_when_nodes_move(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication.instance() or QApplication([])

        view = ChunkDagView()
        view.resize(900, 420)
        view.show()

        flows = [
            SimpleNamespace(
                title="Chunk 1",
                incoming_sources={},
                outgoing_targets={"q[0]": {2}},
                defined={"q[0]"},
            ),
            SimpleNamespace(
                title="Chunk 2",
                incoming_sources={"q[0]": {1}},
                outgoing_targets={},
                defined={"q[0]"},
            ),
        ]

        view.set_flows(flows, QFont("DejaVu Sans", 10), edge_labels={(1, 2): ["q[0]"]})
        for _ in range(20):
            app.processEvents()

        self._assert_label_centered_along_edge(view, "q[0]")

        scene = view.scene()
        assert scene is not None
        groups = [
            item
            for item in scene.items()
            if isinstance(item, QGraphicsItemGroup)
            and bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        ]
        assert len(groups) >= 2

        left_group = min(groups, key=lambda item: float(item.pos().x()))
        left_group.setPos(left_group.pos() + QPointF(0.0, 48.0))
        for _ in range(10):
            app.processEvents()

        self._assert_label_centered_along_edge(view, "q[0]")

        view.close()


if __name__ == "__main__":
    unittest.main()
