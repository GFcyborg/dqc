from __future__ import annotations

import math
import re
import textwrap
from itertools import combinations
from typing import Any, Callable
from io import BytesIO

from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen, QPixmap, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat, QBrush, QPolygonF
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTextBrowser,
    QTextEdit,
    QToolTip,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


def _add_selectable_scene_text(scene: QGraphicsScene, text: str, color: QColor, font: QFont | None = None):
    item = scene.addText(text)
    if font is not None:
        item.setFont(font)
    item.setDefaultTextColor(color)
    item.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
    return item


def _wrap_scene_message(text: str, width: int = 88) -> str:
    wrapped_lines: list[str] = []
    for line in str(text).splitlines() or [str(text)]:
        if not line.strip():
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(line, width=width, break_long_words=True, break_on_hyphens=False))
    return "\n".join(wrapped_lines)


def _wire_label(wire: Any) -> str:
    register = getattr(wire, "_register", None) or getattr(wire, "register", None)
    register_name = None
    if register is not None:
        register_name = getattr(register, "name", None)
        if register_name is None and isinstance(register, (tuple, list)) and len(register) > 1:
            register_name = register[1]

    index = getattr(wire, "_index", None)
    if index is None:
        index = getattr(wire, "index", None)

    if register_name is not None and index is not None:
        return f"{register_name}{index}"
    if register_name is not None:
        return str(register_name)

    name = getattr(wire, "name", None)
    if name:
        return str(name)

    if index is not None:
        return f"{wire.__class__.__name__}{index}"

    rep = repr(wire)
    match_idx = re.search(r"(?:index|uid)\s*=\s*(\d+)", rep)
    match_reg = re.search(r"\(\s*\d+\s*,\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\)", rep)
    if match_reg and match_idx:
        return f"{match_reg.group(1)}{match_idx.group(1)}"

    if match_idx:
        typename = wire.__class__.__name__.lower()
        prefix = "qubit" if "qubit" in typename else "bit"
        return f"{prefix}{match_idx.group(1)}"

    typename = wire.__class__.__name__.lower()
    if "qubit" in typename:
        return "qubit"
    if "clbit" in typename or "bit" in typename:
        return "bit"
    return rep


def collect_multi_qubit_interactions(circuit: Any) -> tuple[list[Any], dict[tuple[int, int], dict[str, Any]]]:
    from qiskit.converters import circuit_to_dag

    dag = circuit_to_dag(circuit)
    qubits = list(getattr(dag, "qubits", []) or [])
    index_by_qubit = {qubit: index for index, qubit in enumerate(qubits)}
    interactions: dict[tuple[int, int], dict[str, Any]] = {}

    for node in dag.topological_op_nodes():
        qargs = [qubit for qubit in getattr(node, "qargs", []) or [] if qubit in index_by_qubit]
        if len(qargs) < 2:
            continue

        gate_name = getattr(node, "name", "op") or "op"
        for qubit_a, qubit_b in combinations(sorted(qargs, key=lambda qubit: index_by_qubit[qubit]), 2):
            left_index = index_by_qubit[qubit_a]
            right_index = index_by_qubit[qubit_b]
            key: tuple[int, int] = (left_index, right_index) if left_index <= right_index else (right_index, left_index)
            edge = interactions.setdefault(key, {"count": 0, "gates": set()})
            edge["count"] += 1
            edge["gates"].add(gate_name)

    return qubits, interactions


def _place_edge_label_with_spacing(
    label_item,
    scene: QGraphicsScene,
    anchor_x: float,
    anchor_y: float,
    normal_x: float,
    normal_y: float,
    existing_rects: list[QRectF],
    step: float = 14.0,
    max_attempts: int = 12,
) -> QRectF:
    base_rect = label_item.boundingRect().adjusted(-6, -4, 6, 4)
    for attempt in range(max_attempts):
        sign = -1.0 if attempt % 2 else 1.0
        magnitude = step + (attempt // 2) * step
        x = anchor_x + normal_x * magnitude * sign - base_rect.width() / 2.0
        y = anchor_y + normal_y * magnitude * sign - base_rect.height() / 2.0
        label_item.setPos(x, y)
        rect = label_item.sceneBoundingRect().adjusted(-2, -2, 2, 2)
        if not any(rect.intersects(other) for other in existing_rects):
            return rect
    label_item.setPos(anchor_x - base_rect.width() / 2.0, anchor_y - base_rect.height() / 2.0)
    return label_item.sceneBoundingRect().adjusted(-2, -2, 2, 2)


class _DraggableChunkGroup(QGraphicsItemGroup):
    def __init__(self, on_moved: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._on_moved = on_moved
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def set_move_callback(self, callback: Callable[[], None] | None) -> None:
        self._on_moved = callback

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and callable(self._on_moved):
            self._on_moved()
        return result


class ZoomableView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._scale_factor = 1.0
        self.setBackgroundBrush(QColor("#f8fbff"))

    def fit_scene(self) -> None:
        scene = self.scene()
        rect = scene.itemsBoundingRect() if scene is not None else self.sceneRect()
        if rect.isValid() and not rect.isNull():
            # Keep lateral padding tight to avoid early horizontal scrollbars in circuit/graph areas.
            margin_x = max(8.0, rect.width() * 0.03)
            margin_y = max(22.0, rect.height() * 0.12)
            fit_rect = rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
            if scene is not None:
                scene.setSceneRect(fit_rect)
            self.resetTransform()
            self.fitInView(fit_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(fit_rect.center())
            self._scale_factor = self._current_uniform_scale()

    def reset_zoom(self) -> None:
        self.resetTransform()
        self.fit_scene()

    def zoom(self, delta: int) -> None:
        factor = 1.15 if delta > 0 else 1 / 1.15
        current_scale = self._current_uniform_scale()
        fit_scale = self._compute_fit_scale()
        next_scale = current_scale * factor
        if factor < 1.0 and current_scale <= fit_scale * 1.000000001:
            return
        if factor < 1.0 and next_scale < fit_scale * 1.000000001:
            self.fit_scene()
            return
        if 0.12 <= next_scale <= 8.0:
            self.scale(factor, factor)
            self._scale_factor = self._current_uniform_scale()

    def _current_uniform_scale(self) -> float:
        try:
            scale = float(self.transform().m11())
        except Exception:
            return 1.0
        return max(1e-6, min(scale, 1e6))

    def _compute_fit_scale(self) -> float:
        scene_rect = self.sceneRect()
        if scene_rect.isNull() or not scene_rect.isValid():
            return 1.0
        view_w = self.viewport().width()
        view_h = self.viewport().height()
        scene_w = scene_rect.width()
        scene_h = scene_rect.height()
        if view_w <= 0 or view_h <= 0 or scene_w <= 0 or scene_h <= 0:
            return 1.0
        return float(max(1e-6, min(view_w / scene_w, view_h / scene_h)))

    def wheelEvent(self, event):  # noqa: N802
        self.zoom(1 if event.angleDelta().y() > 0 else -1)
        event.accept()


class _PragmaBoldHighlighter(QSyntaxHighlighter):
    """Applies bold + underline formatting to split-pragma lines in CodeEditor."""

    def __init__(self, document: Any) -> None:
        super().__init__(document)
        self._pragma_lines: set[int] = set()
        self._fmt = QTextCharFormat()
        self._fmt.setFontWeight(700)
        self._fmt.setFontUnderline(True)

    def update_pragma_lines(self, lines: set[int]) -> None:
        if lines != self._pragma_lines:
            self._pragma_lines = set(lines)
            self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        line_no = self.currentBlock().blockNumber() + 1
        if line_no in self._pragma_lines and text.strip():
            self.setFormat(0, len(text), self._fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):  # noqa: N802
        self.editor.paint_line_number_area(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        self.editor._show_original_rule_tooltip_for_y(event.position().y(), event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        self.editor._hide_original_rule_tooltip()
        super().leaveEvent(event)


class CodeEditor(QPlainTextEdit):
    splitPointRequested = Signal(int)

    _line_number_area_padding = 10
    _line_number_text_gap = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFont(QFont("DejaVu Sans Mono", 10))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.setCursorWidth(2)
        self.line_number_area = LineNumberArea(self)
        self._diagnostic_lines: dict[int, QColor] = {}
        self._suggested_lines: set[int] = set()
        self._pragma_lines: set[int] = set()
        self._rewrite_spans: list[Any] = []
        self._original_rule_matches: dict[int, list[tuple[int, str, int, int]]] = {}
        self._original_rule_tooltips: dict[int, str] = {}
        self._pragma_bold_highlighter = _PragmaBoldHighlighter(self.document())
        self._font_step = 0
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.line_number_area.setMouseTracking(True)
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return self._line_number_area_padding + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _block_count: int) -> None:
        gutter_width = self.line_number_area_width()
        self.setViewportMargins(gutter_width + self._line_number_text_gap, 0, 0, 0)
        self.line_number_area.setGeometry(0, 0, gutter_width, self.height())

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area_width(), rect.height())

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def paint_line_number_area(self, event) -> None:
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#eef2ff"))
        pragma_lines = self._actual_pragma_lines()
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_no = block_number + 1
                color = self._diagnostic_lines.get(line_no, QColor("#64748b"))
                if line_no in self._original_rule_tooltips:
                    color = QColor("#dc2626")
                elif line_no in self._suggested_lines:
                    color = QColor("#1d4ed8")
                painter.setPen(color)
                if line_no in self._suggested_lines:
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                painter.drawText(0, top, self.line_number_area_width() - 4, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, str(line_no))
                if line_no in self._suggested_lines:
                    painter.setFont(self.font())
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def setDiagnosticLines(self, diagnostics: dict[int, QColor]) -> None:
        self._diagnostic_lines = dict(diagnostics)
        self.line_number_area.update()

    def setRewriteSpans(self, spans: list[Any]) -> None:
        self._rewrite_spans = list(spans)
        self._update_extra_selections()

    def setOriginalRuleMatches(self, matches: dict[int, list[tuple[int, str, int, int]]]) -> None:
        self._original_rule_matches = {line_no: list(entries) for line_no, entries in matches.items() if entries}
        self._original_rule_tooltips = {
            line_no: "\n".join(dict.fromkeys(f"Rule {rule_id}: {name}" for rule_id, name, _, _ in entries))
            for line_no, entries in self._original_rule_matches.items()
        }
        self._update_extra_selections()
        self.line_number_area.update()

    def setSplitSuggestions(self, suggestions: set[int]) -> None:
        self._suggested_lines = set(suggestions)
        self.line_number_area.update()

    def setPragmaLines(self, pragma_lines: set[int]) -> None:
        self._pragma_lines = set(pragma_lines)
        self._update_extra_selections()
        self.line_number_area.update()

    def highlight_current_line(self) -> None:
        self._update_extra_selections()

    def _update_extra_selections(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(219, 234, 254, 180))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)

        for line_no, entries in sorted(self._original_rule_matches.items()):
            block = self.document().findBlockByNumber(line_no - 1)
            if not block.isValid():
                continue
            for rule_id, _, start, end in entries:
                if end <= start:
                    continue
                selection = QTextEdit.ExtraSelection()
                cursor = QTextCursor(block)
                block_start = block.position()
                block_end = block_start + len(block.text())
                sel_start = max(block_start, min(block_start + start, block_end))
                sel_end = max(sel_start, min(block_start + end, block_end))
                cursor.setPosition(sel_start)
                cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
                selection.cursor = cursor
                selection.format.setForeground(QColor("#b91c1c"))
                selection.format.setBackground(QColor(254, 202, 202, 170))
                selections.append(selection)

        for span in self._rewrite_spans:
            original = str(getattr(span, "original", ""))
            if not original.strip():
                continue
            line_no = int(getattr(span, "line", 0))
            block = self.document().findBlockByNumber(line_no - 1)
            if not block.isValid():
                continue
            block_text = block.text()
            needle = original.rstrip("\n")
            start = block_text.find(needle)
            if start < 0:
                stripped = needle.strip()
                if stripped:
                    start = block_text.find(stripped)
                    needle = stripped
            if start < 0 or not needle:
                continue
            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(block)
            block_start = block.position()
            block_end = block_start + len(block.text())
            sel_start = max(block_start, min(block_start + start, block_end))
            sel_end = max(sel_start, min(block_start + start + len(needle), block_end))
            cursor.setPosition(sel_start)
            cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            selection.format.setForeground(QColor("#b91c1c"))
            selection.format.setBackground(QColor(254, 202, 202, 180))
            selections.append(selection)

        self.setExtraSelections(selections)
        self._pragma_bold_highlighter.update_pragma_lines(self._actual_pragma_lines())

    def _line_number_at_y(self, y: float) -> int | None:
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= y:
            if block.isVisible() and bottom >= y:
                return block_number + 1
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
        return None

    def _show_original_rule_tooltip_for_y(self, y: float, global_pos: QPoint) -> None:
        line_no = self._line_number_at_y(y)
        if line_no is None:
            QToolTip.hideText()
            return
        tooltip = self._original_rule_tooltips.get(line_no, "")
        if tooltip:
            QToolTip.showText(global_pos + QPoint(20, 20), tooltip, self.line_number_area, self.line_number_area.rect(), 1200)
        else:
            QToolTip.hideText()

    def _hide_original_rule_tooltip(self) -> None:
        QToolTip.hideText()

    def mouseMoveEvent(self, event):  # noqa: N802
        line_no = self._line_number_at_y(event.position().y())
        tooltip = self._original_rule_tooltips.get(line_no or 0, "") if line_no is not None else ""
        if tooltip:
            QToolTip.showText(event.globalPosition().toPoint() + QPoint(20, 20), tooltip, self.viewport(), self.viewport().rect(), 1200)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        QToolTip.hideText()
        super().leaveEvent(event)

    def _actual_pragma_lines(self) -> set[int]:
        pragma_lines = set(self._pragma_lines)
        for block_index in range(self.blockCount()):
            block = self.document().findBlockByNumber(block_index)
            if block.isValid() and block.text().strip().startswith("pragma dqc.v1.split"):
                pragma_lines.add(block_index + 1)
        return pragma_lines

    def contextMenuEvent(self, event):  # noqa: N802
        cursor = self.cursorForPosition(event.pos())
        self.setTextCursor(cursor)
        self.splitPointRequested.emit(cursor.blockNumber() + 1)

    def zoom(self, delta: int) -> None:
        self._font_step += delta
        font = self.font()
        font.setPointSize(max(8, 10 + self._font_step))
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))


class HtmlCodeView(QTextBrowser):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFont(QFont("DejaVu Sans Mono", 10))
        self.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)
        self.setStyleSheet("QTextBrowser { background: #ffffff; color: #0f172a; border: none; }")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._line_tooltips: dict[int, str] = {}
        self._teleport_lines: set[int] = set()

    def set_rewrite_result(self, rewritten_source: str, spans: list[Any]) -> None:
        def _changed_fragment(original: str, rewritten: str) -> str:
            if not original or not rewritten or original == rewritten:
                return ""
            prefix = 0
            max_prefix = min(len(original), len(rewritten))
            while prefix < max_prefix and original[prefix] == rewritten[prefix]:
                prefix += 1

            suffix = 0
            max_suffix = min(len(original) - prefix, len(rewritten) - prefix)
            while suffix < max_suffix and original[len(original) - 1 - suffix] == rewritten[len(rewritten) - 1 - suffix]:
                suffix += 1

            end = len(rewritten) - suffix if suffix > 0 else len(rewritten)
            if end <= prefix:
                return ""
            return rewritten[prefix:end]

        self._line_tooltips = {}
        self._teleport_lines = set()
        tooltip_map: dict[int, list[str]] = {}
        visible_lines: set[int] = set()
        partial_highlights: dict[int, list[str]] = {}
        snippet_tooltips: dict[str, list[str]] = {}
        teleport_tooltip = "Rule 6: split pragma rewritten into teleportation comment block"
        for span in spans:
            rewritten = str(getattr(span, "rewritten", ""))
            if not rewritten.strip():
                continue
            original = str(getattr(span, "original", ""))
            line_no = int(getattr(span, "line", 0))
            if line_no < 1:
                continue
            rule_id = getattr(span, "rule_id", "?")
            message = getattr(span, "message", "")
            tooltip = f"Rule {rule_id}: {message}"
            tooltip_map.setdefault(line_no, []).append(tooltip)
            if rule_id == 7:
                partial_highlights.setdefault(line_no, []).append(rewritten.strip())
                continue
            if "\n" not in rewritten and "\n" not in original:
                fragment = _changed_fragment(original, rewritten)
                if fragment.strip():
                    partial_highlights.setdefault(line_no, []).append(fragment)
                    continue
            visible_lines.add(line_no)
            for rewritten_line in rewritten.splitlines():
                normalized = rewritten_line.strip()
                if normalized:
                    snippet_tooltips.setdefault(normalized, []).append(tooltip)
        lines = rewritten_source.splitlines()
        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]
            if line.startswith("/* Teleporting qubits into chunk "):
                while line_index < len(lines):
                    self._teleport_lines.add(line_index + 1)
                    tooltip_map.setdefault(line_index + 1, []).append(teleport_tooltip)
                    visible_lines.add(line_index + 1)
                    if lines[line_index].strip() == "*/":
                        line_index += 1
                        break
                    line_index += 1
                line_index += 1
                continue
            snippet = line.strip()
            if snippet and snippet in snippet_tooltips:
                visible_lines.add(line_index + 1)
                tooltip_map.setdefault(line_index + 1, []).extend(snippet_tooltips[snippet])
            line_index += 1

        self._line_tooltips = {
            line_no: "\n".join(dict.fromkeys(messages))
            for line_no, messages in tooltip_map.items()
        }
        self.setHtml(self._build_html(rewritten_source, visible_lines, partial_highlights))

    def _build_html(self, rewritten_source: str, visible_lines: set[int], partial_highlights: dict[int, list[str]]) -> str:
        def _highlight_snippets(line_text: str, snippets: list[str]) -> str:
            ranges: list[tuple[int, int]] = []
            seen: set[str] = set()
            for snippet in sorted(snippets, key=len, reverse=True):
                token = snippet.strip()
                if not token or token in seen:
                    continue
                seen.add(token)
                start = line_text.find(token)
                if start < 0:
                    continue
                end = start + len(token)
                if any(not (end <= left or start >= right) for left, right in ranges):
                    continue
                ranges.append((start, end))
            if not ranges:
                return self._html_escape(line_text)
            ranges.sort()
            parts: list[str] = []
            cursor = 0
            for start, end in ranges:
                if start > cursor:
                    parts.append(self._html_escape(line_text[cursor:start]))
                parts.append(f"<span style='color:#22c55e'>{self._html_escape(line_text[start:end])}</span>")
                cursor = end
            if cursor < len(line_text):
                parts.append(self._html_escape(line_text[cursor:]))
            return "".join(parts)

        lines = rewritten_source.splitlines()
        decorated: list[str] = ["<html><body style='background:#0f1117;color:#cfd7e6;'><pre style='font-family:monospace;'>"]
        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]
            if line.startswith("/* Teleporting qubits into chunk "):
                while line_index < len(lines):
                    block_line = lines[line_index]
                    escaped = self._html_escape(block_line)
                    decorated.append(f"<span style='color:#ca8a04'>{escaped}</span>")
                    line_index += 1
                    if block_line.strip() == "*/":
                        break
                continue
            line_no = line_index + 1
            escaped = self._html_escape(line)
            if line_no in self._teleport_lines:
                decorated.append(f"<span style='color:#ca8a04'>{escaped}</span>")
            elif line_no in partial_highlights:
                decorated.append(_highlight_snippets(line, partial_highlights[line_no]))
            elif line_no in visible_lines:
                decorated.append(f"<span style='color:#22c55e'>{escaped}</span>")
            else:
                decorated.append(escaped)
            line_index += 1
        decorated.append("</pre></body></html>")
        return "\n".join(decorated)

    def _html_escape(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def _tooltip_for_position(self, position: QPoint) -> str:
        cursor = self.cursorForPosition(position)
        return self._line_tooltips.get(cursor.blockNumber() + 1, "")

    def mouseMoveEvent(self, event):  # noqa: N802
        tooltip = self._tooltip_for_position(event.position().toPoint())
        if tooltip:
            QToolTip.showText(event.globalPosition().toPoint() + QPoint(20, 20), tooltip, self.viewport(), self.viewport().rect(), 1200)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        QToolTip.hideText()
        super().leaveEvent(event)

    def zoom(self, delta: int) -> None:
        if delta > 0:
            self.zoomIn(delta)
        elif delta < 0:
            self.zoomOut(abs(delta))


class RulePanel(QFrame):
    ruleToggled = Signal(int, bool)

    def __init__(self, rules: list[Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: dict[int, QCheckBox] = {}
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background: rgba(255,255,255,0.88); border: 1px solid rgba(96, 165, 250, 0.18); border-radius: 10px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        for rule in rules:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            check = QCheckBox(f"{rule.rule_id}. {rule.name}")
            check.setChecked(rule.enabled)
            if rule.rule_id == 6:
                check.setStyleSheet("color: #0f172a; font-weight: bold; text-decoration: underline;")
            else:
                check.setStyleSheet("color: #0f172a;")
            check.toggled.connect(lambda checked, rule_id=rule.rule_id: self.ruleToggled.emit(rule_id, checked))
            row_layout.addWidget(check)
            layout.addWidget(row)
            desc = QLabel(rule.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #475569; font-size: 11px;")
            layout.addWidget(desc)
            self._rows[rule.rule_id] = check
        layout.addStretch(1)

    def set_states(self, enabled_rules: set[int], bypass: bool) -> None:
        for rule_id, check in self._rows.items():
            check.blockSignals(True)
            check.setChecked(rule_id in enabled_rules)
            check.blockSignals(False)
            if bypass and rule_id != 0:
                check.setEnabled(False)
                extra = " font-weight: bold; text-decoration: underline;" if rule_id == 6 else ""
                check.setStyleSheet(f"color: #94a3b8;{extra}")
            else:
                check.setEnabled(True)
                extra = " font-weight: bold; text-decoration: underline;" if rule_id == 6 else ""
                check.setStyleSheet(f"color: #0f172a;{extra}")


class ParseTreeView(QTreeWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setHeaderLabels(["AST parse-tree"])
        self.setStyleSheet("QTreeWidget { background: #ffffff; color: #0f172a; border: none; }")
        self.setAlternatingRowColors(True)
        self._program: Any | None = None

    @property
    def program(self) -> Any | None:
        return self._program

    def load_tree(self, tree: Any | None) -> None:
        self.clear()
        self._program = tree
        if tree is None:
            self.addTopLevelItem(QTreeWidgetItem(["No parse tree available."]))
            return
        if isinstance(tree, Exception):
            self.addTopLevelItem(QTreeWidgetItem([f"Parse error: {tree}"]))
            return

        def add_item(parent: QTreeWidgetItem, node: Any, label: str = "root", owner: Any | None = None) -> None:
            bound_owner = owner if owner is not None else node
            if isinstance(node, (str, int, float, bool)) or node is None:
                leaf = QTreeWidgetItem([f"{label}: {node!r}"])
                leaf.setData(0, Qt.ItemDataRole.UserRole, bound_owner)
                parent.addChild(leaf)
                return
            item = QTreeWidgetItem([f"{label}: {type(node).__name__}"])
            item.setData(0, Qt.ItemDataRole.UserRole, node)
            parent.addChild(item)
            fields = getattr(node, "__dict__", {})
            for key, value in fields.items():
                if key.startswith("_") or key == "span":
                    continue
                if isinstance(value, (list, tuple)):
                    for index, child in enumerate(value):
                        add_item(item, child, f"{key}[{index}]", owner=node)
                else:
                    add_item(item, value, key, owner=node)

        root = QTreeWidgetItem([type(tree).__name__])
        root.setData(0, Qt.ItemDataRole.UserRole, tree)
        self.addTopLevelItem(root)
        add_item(root, tree)
        self.expandToDepth(2)

    def select_node(self, target: Any) -> None:
        if target is None:
            return

        def walk(item: QTreeWidgetItem) -> QTreeWidgetItem | None:
            if item.data(0, Qt.ItemDataRole.UserRole) is target:
                return item
            for index in range(item.childCount()):
                found = walk(item.child(index))
                if found is not None:
                    return found
            return None

        root = self.topLevelItem(0)
        if root is None:
            return
        found = walk(root)
        if found is not None:
            self.setCurrentItem(found)
            self.scrollToItem(found)


def _draw_graph(scene: QGraphicsScene, graph, label_getter: Callable[[Any], str] | None = None, empty_message: str = "No graph available") -> None:
    scene.clear()
    if graph is None or graph.number_of_nodes() == 0:
        text = _add_selectable_scene_text(
            scene,
            _wrap_scene_message(empty_message),
            QColor("#475569"),
            QFont("DejaVu Sans Mono", 11),
        )
        scene.setSceneRect(text.boundingRect().adjusted(-24, -24, 24, 24))
        return
    try:
        import networkx as nx

        pos = nx.spring_layout(graph, seed=8)
    except Exception:
        pos = {node: (index, index % 3) for index, node in enumerate(graph.nodes())}
    min_x = min(point[0] for point in pos.values())
    max_x = max(point[0] for point in pos.values())
    min_y = min(point[1] for point in pos.values())
    max_y = max(point[1] for point in pos.values())
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    scale = 520
    for left, right, data in graph.edges(data=True):
        x1, y1 = pos[left]
        x2, y2 = pos[right]
        scene.addLine((x1 - min_x) / span_x * scale, (y1 - min_y) / span_y * scale, (x2 - min_x) / span_x * scale, (y2 - min_y) / span_y * scale, QColor("#60a5fa"))
        label = data.get("label") or data.get("weight")
        if label is not None:
            mid = scene.addText(str(label))
            mid.setDefaultTextColor(QColor("#1d4ed8"))
            mid.setPos(((x1 + x2) / 2 - min_x) / span_x * scale, ((y1 + y2) / 2 - min_y) / span_y * scale)
    for node, (x, y) in pos.items():
        px = (x - min_x) / span_x * scale
        py = (y - min_y) / span_y * scale
        scene.addEllipse(px, py, 18, 18, QColor("#93c5fd"), QColor("#dbeafe"))
        label = label_getter(node) if label_getter else str(node)
        text = scene.addText(label)
        text.setDefaultTextColor(QColor("#0f172a"))
        text.setPos(px + 22, py - 4)
    scene.setSceneRect(scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))


class GraphTab(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = ZoomableView()
        self._scene = QGraphicsScene(self)
        self.view.setScene(self._scene)
        layout.addWidget(self.view)
        self.title = title

    def set_graph(self, graph, label_getter: Callable[[Any], str] | None = None, empty_message: str = "No graph available") -> None:
        _draw_graph(self._scene, graph, label_getter, empty_message)
        self.view.fit_scene()


class ChunkDagView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setBackgroundBrush(QColor("#f8fbf7"))
        self.setStyleSheet("border: 1px solid #d0d0d0;")
        self._cached_flows: list[Any] = []
        self._cached_font = QFont("DejaVu Sans", 10)
        self._reflow_in_progress = False
        self._last_reflow_viewport_size: QSize | None = None
        self._manual_chunk_positions: dict[int, QPointF] = {}

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self._cached_flows or self._reflow_in_progress:
            return
        current = self.viewport().size()
        if self._last_reflow_viewport_size is None:
            self._last_reflow_viewport_size = current
            self._render_cached_flows()
            return
        delta_w = abs(current.width() - self._last_reflow_viewport_size.width())
        delta_h = abs(current.height() - self._last_reflow_viewport_size.height())
        # Ignore tiny viewport jitter (often caused by scrollbar appearance) to keep layout stable.
        if max(delta_w, delta_h) < 24:
            return
        self._last_reflow_viewport_size = current
        self._render_cached_flows()

    def set_flows(self, flows: list[Any], font: QFont) -> None:
        if len(flows) != len(self._cached_flows):
            self._manual_chunk_positions = {}
        self._cached_flows = list(flows)
        self._cached_font = QFont(font)
        self._last_reflow_viewport_size = self.viewport().size()
        self._render_cached_flows()

    def _render_cached_flows(self) -> None:
        scene = self.scene()
        if scene is None:
            scene = QGraphicsScene(self)
            self.setScene(scene)
        scene.clear()

        self._reflow_in_progress = True
        node_font = QFont(self._cached_font)
        if node_font.pointSizeF() > 0:
            node_font.setPointSizeF(max(7.0, node_font.pointSizeF() - 2.0))
        elif node_font.pointSize() > 0:
            node_font.setPointSize(max(7, node_font.pointSize() - 2))
        else:
            node_font.setPointSize(8)

        flows = self._cached_flows

        if not flows:
            empty = scene.addSimpleText("No dependency DAG available")
            empty.setFont(node_font)
            empty.setBrush(QColor("#555555"))
            scene.setSceneRect(empty.boundingRect().adjusted(-10, -10, 10, 10))
            self._reflow_in_progress = False
            return

        base_gap = 44.0
        min_gap = 16.0
        left = 20.0
        top = 20.0

        metrics = QFontMetricsF(node_font)
        line_h = metrics.height()
        inner_pad_x = 10.0
        top_pad = 6.0
        row_gap = 4.0
        bottom_pad = 6.0
        max_text_w = 230.0

        node_specs: list[dict[str, Any]] = []
        for index, flow in enumerate(flows, 1):
            title_text = getattr(flow, "title", f"Chunk {index}")
            io_text = f"in: {len(getattr(flow, 'incoming_sources', {}))}   out: {len(getattr(flow, 'outgoing_targets', {}))}"
            summary_text = ", ".join(sorted(getattr(flow, "defined", set()))) if getattr(flow, "defined", None) else "none"
            summary_full = "declared/used: " + summary_text

            wrap_width = max(24, int(max_text_w / max(6.0, metrics.averageCharWidth())))
            summary_lines = textwrap.wrap(summary_full, width=wrap_width, break_long_words=True, break_on_hyphens=False) or [summary_full]

            text_w = max(
                metrics.horizontalAdvance(title_text),
                metrics.horizontalAdvance(io_text),
                *(metrics.horizontalAdvance(line) for line in summary_lines),
            )
            node_w = max(170.0, min(max_text_w + 2 * inner_pad_x, text_w + 2 * inner_pad_x))
            node_h = top_pad + line_h + row_gap + line_h + row_gap + (len(summary_lines) * line_h) + bottom_pad

            title_seed = sum((pos + 1) * ord(ch) for pos, ch in enumerate(title_text))
            node_specs.append(
                {
                    "index": index,
                    "title_text": title_text,
                    "io_text": io_text,
                    "summary_lines": summary_lines,
                    "node_w": node_w,
                    "node_h": node_h,
                    "seed": title_seed,
                }
            )

        viewport_h = float(max(120, self.viewport().height()))
        viewport_w = float(max(240, self.viewport().width()))
        spread_margin_y = max(6.0, min(24.0, viewport_h * 0.06))
        spread_margin_x = max(26.0, min(110.0, viewport_w * 0.14))
        max_node_h = max(spec["node_h"] for spec in node_specs)
        usable_top = top + spread_margin_y
        usable_bottom = max(usable_top + max_node_h, viewport_h - (20.0 + spread_margin_y))
        usable_span = max(0.0, usable_bottom - usable_top - max_node_h)
        slot_span = usable_span / max(1, len(node_specs) - 1)

        spread_order = sorted(node_specs, key=lambda spec: ((spec["seed"] % 7919), spec["index"]))
        rank_by_index = {spec["index"]: rank for rank, spec in enumerate(spread_order)}

        usable_left = left + spread_margin_x
        usable_right = max(usable_left, viewport_w - (20.0 + spread_margin_x))
        available_w = max(0.0, usable_right - usable_left)

        x_by_index: dict[int, float] = {}
        if len(node_specs) <= 1:
            only = node_specs[0]
            x_by_index[only["index"]] = usable_left + max(0.0, (available_w - only["node_w"]) / 2.0)
        else:
            jitter_scale = min(20.0, max(8.0, available_w / max(6.0, float(len(node_specs) * 6))))
            for slot, spec in enumerate(node_specs):
                anchor_x = usable_left + (available_w * slot / float(len(node_specs) - 1))
                jitter = (((spec["seed"] % 1000) / 1000.0) - 0.5) * jitter_scale
                x_by_index[spec["index"]] = anchor_x - (spec["node_w"] / 2.0) + jitter

            # Keep chunk order and avoid overlaps with a forward pass.
            prev_right = None
            for spec in node_specs:
                idx = spec["index"]
                x = x_by_index[idx]
                if prev_right is None:
                    x = max(usable_left, x)
                else:
                    x = max(prev_right + min_gap, x)
                x_by_index[idx] = x
                prev_right = x + spec["node_w"]

            # Pull right-to-left so the rightmost chunk stays near the viewport edge.
            next_left = usable_right
            for spec in reversed(node_specs):
                idx = spec["index"]
                x = x_by_index[idx]
                max_x = next_left - spec["node_w"]
                x = min(x, max_x)
                x_by_index[idx] = x
                next_left = x - min_gap

            # If constraints force nodes left of view, shift the whole chain right.
            leftmost = min(x_by_index[spec["index"]] for spec in node_specs)
            if leftmost < usable_left:
                shift = usable_left - leftmost
                for spec in node_specs:
                    idx = spec["index"]
                    x_by_index[idx] = x_by_index[idx] + shift

        node_items: dict[int, dict[str, Any]] = {}
        for spec in node_specs:
            index = spec["index"]
            rank = rank_by_index[index]
            if len(node_specs) <= 1:
                anchor_y = usable_top + (usable_span / 2.0)
            else:
                anchor_y = usable_top + rank * slot_span
            vertical_seed = (spec["seed"] * 37 + index * 101) % 1000
            jitter = ((vertical_seed / 1000.0) - 0.5) * min(18.0, max(6.0, slot_span * 0.35))
            y = max(usable_top, min(usable_bottom - spec["node_h"], anchor_y + jitter))
            x = x_by_index[index]
            stored_pos = self._manual_chunk_positions.get(index)
            if stored_pos is not None:
                x = float(stored_pos.x())
                y = float(stored_pos.y())

            group = _DraggableChunkGroup(None)
            scene.addItem(group)
            group.setPos(x, y)

            rect = QGraphicsRectItem(0.0, 0.0, spec["node_w"], spec["node_h"], group)
            rect.setPen(QPen(QColor("#6d8f6a")))
            rect.setBrush(QBrush(QColor("#eef6ec")))

            title = QGraphicsSimpleTextItem(spec["title_text"], group)
            title.setFont(node_font)
            title.setBrush(QColor("#223322"))
            title.setPos(inner_pad_x, top_pad)

            io = QGraphicsSimpleTextItem(spec["io_text"], group)
            io.setFont(node_font)
            io.setBrush(QColor("#345"))
            io.setPos(inner_pad_x, top_pad + line_h + row_gap)

            summary = QGraphicsSimpleTextItem("\n".join(spec["summary_lines"]), group)
            summary.setFont(node_font)
            summary.setBrush(QColor("#556"))
            summary.setPos(inner_pad_x, top_pad + (2 * line_h) + (2 * row_gap))

            group.setToolTip(spec["title_text"])
            node_items[index] = {
                "group": group,
                "w": spec["node_w"],
                "h": spec["node_h"],
            }

        edge_labels: dict[tuple[int, int], list[str]] = {}
        for index, flow in enumerate(flows, 1):
            for name, sources in getattr(flow, "incoming_sources", {}).items():
                for source in sources:
                    edge_labels.setdefault((source, index), []).append(name)

        edge_color = QColor("#2f6fff")
        edge_entries: list[dict[str, Any]] = []
        for edge_order, ((source, dest), labels) in enumerate(sorted(edge_labels.items())):
            if source not in node_items or dest not in node_items:
                continue
            line = scene.addLine(0.0, 0.0, 0.0, 0.0, QPen(edge_color))
            label_text = ", ".join(sorted(labels))
            line.setToolTip(label_text)
            label = scene.addSimpleText(label_text)
            label.setFont(node_font)
            label.setBrush(edge_color)
            edge_entries.append(
                {
                    "order": edge_order,
                    "source": source,
                    "dest": dest,
                    "line": line,
                    "label": label,
                    "label_text": label_text,
                }
            )

        def _update_chunk_edges() -> None:
            placed_label_rects: list[QRectF] = []
            for entry in edge_entries:
                source = entry["source"]
                dest = entry["dest"]
                source_item = node_items[source]
                dest_item = node_items[dest]
                src_group = source_item["group"]
                dst_group = dest_item["group"]
                src_w = float(source_item["w"])
                src_h = float(source_item["h"])
                dst_h = float(dest_item["h"])

                src_pos = src_group.pos()
                dst_pos = dst_group.pos()
                start_x = src_pos.x() + src_w
                start_y = src_pos.y() + src_h / 2.0
                end_x = dst_pos.x()
                end_y = dst_pos.y() + dst_h / 2.0

                line = entry["line"]
                line.setLine(start_x, start_y, end_x, end_y)
                line.setToolTip(entry["label_text"])

                label = entry["label"]
                line_dx = end_x - start_x
                line_dy = end_y - start_y
                line_len = math.hypot(line_dx, line_dy) or 1.0
                normal_x = -line_dy / line_len
                normal_y = line_dx / line_len
                side = -1.0 if entry["order"] % 2 else 1.0
                anchor_fraction = 0.20 if entry["order"] % 2 == 0 else 0.80
                anchor_x = start_x + line_dx * anchor_fraction
                anchor_y = start_y + line_dy * anchor_fraction
                # Keep labels very close to edges (and occasionally overlapping) for readability.
                offset = 1.5 + min(4.5, line_len * 0.012)
                anchor_x += normal_x * offset * side
                anchor_y += normal_y * offset * side
                rect = _place_edge_label_with_spacing(
                    label,
                    scene,
                    anchor_x,
                    anchor_y,
                    normal_x,
                    normal_y,
                    placed_label_rects,
                    step=5.0,
                    max_attempts=8,
                )
                placed_label_rects.append(rect)

        def _on_chunk_moved(index: int, group: QGraphicsItemGroup) -> None:
            self._manual_chunk_positions[index] = QPointF(group.pos())
            _update_chunk_edges()

        for index, node in node_items.items():
            group = node["group"]
            group.set_move_callback(lambda idx=index, grp=group: _on_chunk_moved(idx, grp))
        _update_chunk_edges()

        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
        self._reflow_in_progress = False


class QiskitDagView(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setBackgroundBrush(QColor("#f7faff"))
        self.setStyleSheet("border: 1px solid #d0d0d0;")
        self._dragging = False
        self._drag_start_pos: tuple[int, int] | None = None
        self._scroll_bar_start: tuple[int, int] | None = None
        self._user_interacted = False

    def set_message(self, message: str, font: QFont) -> None:
        scene = self.scene()
        if scene is None:
            scene = QGraphicsScene(self)
            self.setScene(scene)
        scene.clear()
        msg_font = QFont(font)
        if msg_font.pointSizeF() > 0:
            msg_font.setPointSizeF(max(11.0, msg_font.pointSizeF()))
        elif msg_font.pointSize() > 0:
            msg_font.setPointSize(max(11, msg_font.pointSize()))
        else:
            msg_font.setPointSize(11)
        text = _add_selectable_scene_text(scene, _wrap_scene_message(message), QColor("#334155"), msg_font)
        scene.setSceneRect(text.boundingRect().adjusted(-12, -12, 12, 12))
        self._user_interacted = False
        self._auto_fit()

    def set_circuit(self, circuit: Any, font: QFont) -> None:
        scene = self.scene()
        if scene is None:
            scene = QGraphicsScene(self)
            self.setScene(scene)
        scene.clear()
        try:
            from qiskit.converters import circuit_to_dag

            dag = circuit_to_dag(circuit)
        except Exception as exc:
            self.set_message(f"Qiskit DAG unavailable: {exc}", font)
            return

        qubits = list(getattr(dag, "qubits", []) or [])
        clbits = list(getattr(dag, "clbits", []) or [])
        wires = qubits + clbits
        op_nodes = list(dag.topological_op_nodes())
        if not wires:
            self.set_message("No wires available for DAG rendering", font)
            return
        if not op_nodes:
            self.set_message("No operation nodes available for DAG rendering", font)
            return

        node_font = QFont(font)
        if node_font.pointSizeF() > 0:
            node_font.setPointSizeF(max(7.0, node_font.pointSizeF() - 2.0))
        elif node_font.pointSize() > 0:
            node_font.setPointSize(max(7, node_font.pointSize() - 2))
        else:
            node_font.setPointSize(8)

        left = 96.0
        top = 34.0
        wire_gap = 42.0
        layer_gap = 140.0
        node_h = 28.0

        metrics = QFontMetricsF(node_font)
        node_widths: list[float] = [max(44.0, metrics.horizontalAdvance(getattr(node, "name", "op")) + 18.0) for node in op_nodes]

        wire_y: dict[Any, float] = {wire: top + index * wire_gap for index, wire in enumerate(wires)}
        max_node_w = max(node_widths, default=44.0)
        scene_right = left + max(1, len(op_nodes) - 1) * layer_gap + max_node_w + 40.0
        edge_pen = QPen(QColor("#2f6fff"))
        edge_pen.setWidthF(1.4)

        for wire, y in wire_y.items():
            wire_text = _wire_label(wire)
            label = scene.addSimpleText(wire_text)
            label_font = QFont(node_font)
            if wire in qubits:
                label_font.setBold(True)
                label.setBrush(QBrush(QColor("#1f5f2d")))
            else:
                label.setBrush(QBrush(QColor("#5b6d8a")))
            label.setFont(label_font)
            label.setToolTip(wire_text)
            label.setPos(10, y - label.boundingRect().height() / 2)
            wire_line = scene.addLine(left - 8, y, scene_right, y, QPen(QColor("#d7deea")))
            wire_line.setToolTip(wire_text)

        last_x: dict[Any, float] = {wire: left - 8 for wire in wires}
        for index, node in enumerate(op_nodes):
            node_w = node_widths[index]
            node_wires = list(getattr(node, "qargs", []) or []) + list(getattr(node, "cargs", []) or [])
            if not node_wires:
                continue

            x_center = left + index * layer_gap
            y_center = sum(wire_y[wire] for wire in node_wires) / len(node_wires)
            if len(node_wires) > 1:
                y_center += (index % 2) * 6.0

            node_rect = scene.addRect(
                x_center - node_w / 2,
                y_center - node_h / 2,
                node_w,
                node_h,
                QPen(QColor("#4a74b6")),
                QBrush(QColor("#e8f0ff")),
            )
            node_rect.setZValue(2)

            label = scene.addSimpleText(getattr(node, "name", "op"))
            label.setFont(node_font)
            label.setBrush(QBrush(QColor("#20304e")))
            label_rect = label.boundingRect()
            label.setPos(
                x_center - label_rect.width() / 2,
                y_center - label_rect.height() / 2,
            )
            label.setZValue(3)

            for wire in node_wires:
                start_x = last_x[wire]
                start_y = wire_y[wire]
                end_x = x_center - node_w / 2
                end_y = y_center
                angle = math.atan2(end_y - start_y, end_x - start_x)
                arrow_size = 8.0
                line_end_x = end_x - math.cos(angle) * arrow_size
                line_end_y = end_y - math.sin(angle) * arrow_size

                line = QGraphicsLineItem(start_x, start_y, line_end_x, line_end_y)
                line.setPen(edge_pen)
                scene.addItem(line)

                arrow_head = QPolygonF([
                    QPointF(end_x, end_y),
                    QPointF(
                        line_end_x - math.cos(angle - math.pi / 6) * arrow_size,
                        line_end_y - math.sin(angle - math.pi / 6) * arrow_size,
                    ),
                    QPointF(
                        line_end_x - math.cos(angle + math.pi / 6) * arrow_size,
                        line_end_y - math.sin(angle + math.pi / 6) * arrow_size,
                    ),
                ])
                arrow = QGraphicsPolygonItem(arrow_head)
                arrow.setPen(QPen(QColor("#2f6fff")))
                arrow.setBrush(QBrush(QColor("#2f6fff")))
                scene.addItem(arrow)

                last_x[wire] = x_center + node_w / 2

        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
        self._user_interacted = False
        self._auto_fit()

    def mousePressEvent(self, event: Any) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._user_interacted = True
            pos = event.position().toPoint()
            self._drag_start_pos = (pos.x(), pos.y())
            self._scroll_bar_start = (
                self.horizontalScrollBar().value(),
                self.verticalScrollBar().value(),
            )
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802
        if self._dragging and self._drag_start_pos and self._scroll_bar_start:
            pos = event.position().toPoint()
            dx = pos.x() - self._drag_start_pos[0]
            dy = pos.y() - self._drag_start_pos[1]
            self._user_interacted = True
            self.horizontalScrollBar().setValue(self._scroll_bar_start[0] - dx)
            self.verticalScrollBar().setValue(self._scroll_bar_start[1] - dy)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_start_pos = None
            self._scroll_bar_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: Any) -> None:  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._interactive_scale(factor)

    def contextMenuEvent(self, event: Any) -> None:  # noqa: N802
        menu = QMenu(self)

        def _reset_zoom() -> None:
            self._user_interacted = False
            self._auto_fit()

        menu.addAction("Reset zoom", _reset_zoom)
        menu.exec(event.globalPos())

    def resizeEvent(self, event: Any) -> None:  # noqa: N802
        super().resizeEvent(event)
        if not self._user_interacted:
            self._auto_fit()

    def _auto_fit(self) -> None:
        scene_rect = self.scene().itemsBoundingRect()
        if scene_rect.isNull():
            return
        # Keep DAG lateral padding tight so horizontal scrollbars do not appear too early when zooming.
        margin_x = max(8.0, scene_rect.width() * 0.03)
        margin_y = max(22.0, scene_rect.height() * 0.12)
        fit_rect = scene_rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
        self.scene().setSceneRect(fit_rect)
        self.resetTransform()
        self.fitInView(fit_rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.centerOn(fit_rect.center())

    def _current_uniform_scale(self) -> float:
        try:
            val = float(self.transform().m11())
        except Exception:
            return 1.0
        if not math.isfinite(val):
            return 1.0
        return max(1e-6, min(val, 1e6))

    def _compute_fit_scale(self) -> float:
        scene_rect = self.scene().itemsBoundingRect()
        if scene_rect.isNull():
            return 1.0
        view_w = self.viewport().width()
        view_h = self.viewport().height()
        scene_w = scene_rect.width()
        scene_h = scene_rect.height()
        if scene_w <= 0 or scene_h <= 0 or view_w <= 0 or view_h <= 0:
            return 1.0
        scale_w = view_w / scene_w
        scale_h = view_h / scene_h
        return float(max(1e-6, min(scale_w, scale_h)))

    def _interactive_scale(self, factor: float) -> None:
        cur = self._current_uniform_scale()
        target = cur * factor
        fit = self._compute_fit_scale()
        eps = 1e-9
        if factor < 1.0:
            if cur <= fit * (1.0 + eps):
                return
            if target <= fit * (1.0 + eps):
                self._user_interacted = False
                self._auto_fit()
                return
        self.scale(factor, factor)
        self._user_interacted = True


class MultiQubitInteractionView(QiskitDagView):
    def set_circuit(self, circuit: Any, font: QFont) -> None:
        scene = self.scene()
        if scene is None:
            scene = QGraphicsScene(self)
            self.setScene(scene)
        scene.clear()

        try:
            qubits, interactions = collect_multi_qubit_interactions(circuit)
        except Exception as exc:
            self.set_message(f"Qubit interaction graph unavailable: {exc}", font)
            return

        if not qubits:
            self.set_message("No qubits available for interaction graph rendering", font)
            return
        if not interactions:
            self.set_message("No multi-qubit interactions available", font)
            return

        node_font = QFont(font)
        if node_font.pointSizeF() > 0:
            node_font.setPointSizeF(max(11.0, node_font.pointSizeF()))
        elif node_font.pointSize() > 0:
            node_font.setPointSize(max(11, node_font.pointSize()))
        else:
            node_font.setPointSize(11)

        edge_font = QFont(font)
        if edge_font.pointSizeF() > 0:
            edge_font.setPointSizeF(max(8.0, edge_font.pointSizeF() - 3.0))
        elif edge_font.pointSize() > 0:
            edge_font.setPointSize(max(8, edge_font.pointSize() - 3))
        else:
            edge_font.setPointSize(8)

        center_x = 0.0
        center_y = 0.0
        radius = max(140.0, 42.0 * len(qubits))
        node_radius = 14.0

        node_items: dict[int, dict[str, Any]] = {}
        for index, qubit in enumerate(qubits):
            angle = (-math.pi / 2.0) + (2.0 * math.pi * index / max(1, len(qubits)))
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            group = _DraggableChunkGroup(None)
            scene.addItem(group)
            group.setPos(x, y)

            node = QGraphicsEllipseItem(-node_radius, -node_radius, node_radius * 2.0, node_radius * 2.0, group)
            node.setPen(QPen(QColor("#2b8a3e")))
            node.setBrush(QBrush(QColor("#e7f7ea")))
            node.setZValue(3)

            label = QGraphicsSimpleTextItem(_wire_label(qubit), group)
            qubit_font = QFont(node_font)
            qubit_font.setBold(True)
            label.setFont(qubit_font)
            label.setBrush(QBrush(QColor("#1f5f2d")))
            label_rect = label.boundingRect()
            label.setPos(-label_rect.width() / 2.0, node_radius + 4.0)
            label.setZValue(4)

            group.setToolTip(_wire_label(qubit))
            node_items[index] = {"group": group}

        max_count = max(int(edge["count"]) for edge in interactions.values())
        edge_base_color = QColor("#2b8a3e")
        edge_base_color.setAlpha(120)
        edge_entries: list[dict[str, Any]] = []
        for edge_order, ((left_index, right_index), edge) in enumerate(sorted(interactions.items())):
            count = int(edge["count"])
            gates = sorted(edge["gates"])
            gate_text = ", ".join(gates[:3])
            if len(gates) > 3:
                gate_text += ", ..."

            weight = 0.7 + (1.5 * count / max(1, max_count))
            edge_pen = QPen(edge_base_color)
            edge_pen.setWidthF(weight)

            line = QGraphicsLineItem(0.0, 0.0, 0.0, 0.0)
            line.setPen(edge_pen)
            label_text = f"{count}x({gate_text})" if gate_text else f"{count}x"
            line.setToolTip(label_text)
            scene.addItem(line)

            label = scene.addSimpleText(label_text)
            label.setFont(edge_font)
            label.setBrush(QBrush(edge_base_color))
            line.setZValue(1)
            label.setZValue(5)

            edge_entries.append(
                {
                    "order": edge_order,
                    "left": left_index,
                    "right": right_index,
                    "line": line,
                    "label": label,
                    "label_text": label_text,
                }
            )

        def _update_interaction_edges() -> None:
            placed_label_rects: list[QRectF] = []
            for entry in edge_entries:
                left_group = node_items[entry["left"]]["group"]
                right_group = node_items[entry["right"]]["group"]

                left_pos = left_group.pos()
                right_pos = right_group.pos()
                start_x = left_pos.x()
                start_y = left_pos.y()
                end_x = right_pos.x()
                end_y = right_pos.y()

                line = entry["line"]
                line.setLine(start_x, start_y, end_x, end_y)
                line.setToolTip(entry["label_text"])

                label = entry["label"]
                line_dx = end_x - start_x
                line_dy = end_y - start_y
                length = math.hypot(line_dx, line_dy) or 1.0
                normal_x = -line_dy / length
                normal_y = line_dx / length
                side = -1.0 if entry["order"] % 2 else 1.0
                anchor_fraction = 0.16 if entry["order"] % 2 == 0 else 0.84
                anchor_x = start_x + line_dx * anchor_fraction
                anchor_y = start_y + line_dy * anchor_fraction
                offset = 10.0 + min(24.0, length * 0.05)
                anchor_x += normal_x * offset * side
                anchor_y += normal_y * offset * side
                rect = _place_edge_label_with_spacing(
                    label,
                    scene,
                    anchor_x,
                    anchor_y,
                    normal_x,
                    normal_y,
                    placed_label_rects,
                )
                placed_label_rects.append(rect)

        for node in node_items.values():
            node["group"].set_move_callback(_update_interaction_edges)
        _update_interaction_edges()

        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-30, -30, 30, 30))
        self._user_interacted = False
        self._auto_fit()


class QiskitDagTab(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = QiskitDagView()
        layout.addWidget(self.view)
        self.title = title

    def set_graph(self, graph, label_getter: Callable[[Any], str] | None = None, empty_message: str = "No graph available") -> None:
        scene = self.view.scene()
        _draw_graph(scene, graph, label_getter, empty_message)
        self.view._user_interacted = False
        self.view._auto_fit()


class ChunkDagTab(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = ChunkDagView()
        layout.addWidget(self.view)
        self.title = title

    def set_graph(self, graph, label_getter: Callable[[Any], str] | None = None, empty_message: str = "No graph available") -> None:
        scene = self.view.scene()
        _draw_graph(scene, graph, label_getter, empty_message)
        rect = scene.itemsBoundingRect()
        if not rect.isNull():
            margin_x = max(22.0, rect.width() * 0.10)
            margin_y = max(22.0, rect.height() * 0.12)
            fit_rect = rect.adjusted(-margin_x, -margin_y, margin_x, margin_y)
            scene.setSceneRect(fit_rect)
            self.view.resetTransform()
            self.view.fitInView(fit_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.view.centerOn(fit_rect.center())

    def set_flows(self, flows: list[Any], font: QFont) -> None:
        self.view.set_flows(flows, font)


class QubitInteractionTab(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = MultiQubitInteractionView()
        layout.addWidget(self.view)
        self.title = title

    def set_graph(self, graph, label_getter: Callable[[Any], str] | None = None, empty_message: str = "No graph available") -> None:
        scene = self.view.scene()
        _draw_graph(scene, graph, label_getter, empty_message)
        self.view._user_interacted = False
        self.view._auto_fit()


class CircuitView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = ZoomableView()
        self.view.setBackgroundBrush(QColor("#eceff3"))
        self._scene = QGraphicsScene(self)
        self._scene.setBackgroundBrush(QColor("#eceff3"))
        self.view.setScene(self._scene)
        layout.addWidget(self.view)

    def show_circuit(self, circuit: Any | None) -> None:
        self._scene.clear()
        if circuit is None:
            text = _add_selectable_scene_text(
                self._scene,
                "No circuit available",
                QColor("#334155"),
                QFont("DejaVu Sans Mono", 12),
            )
            self._scene.setSceneRect(text.boundingRect().adjusted(-40, -30, 40, 30))
            self.view.fit_scene()
            return
        figure = None
        try:
            from qiskit.visualization import circuit_drawer

            figure = circuit_drawer(
                circuit,
                output="mpl",
                fold=500,
                vertical_compression="low",
                cregbundle=False,
                expr_len=60,
            )
            try:
                figure.patch.set_facecolor("#ffffff")
            except Exception:
                pass
            buffer = BytesIO()
            # Tight bbox trims the large default white margins around the circuit image.
            figure.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.04, dpi=140)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue(), "PNG")
            self._scene.addItem(QGraphicsPixmapItem(pixmap))
            self._scene.setSceneRect(self._scene.itemsBoundingRect())
            self.view.fit_scene()
        except Exception as exc:
            # Fallback to text drawer when matplotlib is unavailable.
            try:
                text_diagram = str(circuit.draw(output="text", fold=120))
                header = "Circuit rendered in text mode (matplotlib unavailable):\n\n"
                text = _add_selectable_scene_text(
                    self._scene,
                    header + text_diagram,
                    QColor("#0f172a"),
                    QFont("DejaVu Sans Mono", 10),
                )
                self._scene.setSceneRect(text.boundingRect().adjusted(-12, -12, 12, 12))
                self.view.fit_scene()
            except Exception as text_exc:
                text = _add_selectable_scene_text(
                    self._scene,
                    f"Circuit rendering failed: {exc}\n\nText fallback also failed: {text_exc}",
                    QColor("#dc2626"),
                    QFont("DejaVu Sans Mono", 10),
                )
                self._scene.setSceneRect(text.boundingRect().adjusted(-12, -12, 12, 12))
                self.view.fit_scene()
        finally:
            if figure is not None:
                try:
                    import matplotlib.pyplot as plt

                    plt.close(figure)
                except Exception:
                    pass


class DiagnosticsView(QTextBrowser):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("QTextBrowser { background: #ffffff; color: #0f172a; border: none; }")
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.setOpenExternalLinks(True)

    def set_report(self, text: str) -> None:
        self.setPlainText(text)
