from __future__ import annotations

import concurrent.futures
import importlib
import multiprocessing
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, QRunnable, QThreadPool, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QImageReader, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QInputDialog,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from .pipeline import (
    DEFAULT_RULES,
    QCOMM_TEMPLATE_REQUIRED_IDENTIFIERS,
    RuleState,
    build_ast_graph,
    build_distributed_qasm,
    latest_versions_from_pypi,
    package_versions,
    line_is_inside_blocking_scope,
    normalize_dqc_clicked_split_line,
    original_line_rule_matches,
    AUTO_PARAM_DEFAULT_EXPR,
    read_text,
    split_points_from_source,
    split_pragma_line_numbers,
    rewrite_and_analyze,
    scan_inputs,
    smoke_test_hadamard,
    summary_text,
    run_runtime_counts,
    validate_qcomm_template,
    write_text,
)
from .widgets import CircuitView, CodeEditor, DiagnosticsView, GraphTab, HtmlCodeView, ParseTreeView, RulePanel, QiskitDagTab, ChunkDagTab, QubitInteractionTab


class ParameterDialog(QDialog):
    def __init__(self, parameters: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Runtime parameters")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._edits: dict[str, QLineEdit] = {}
        for name in parameters:
            edit = QLineEdit(AUTO_PARAM_DEFAULT_EXPR)
            self._edits[name] = edit
            form.addRow(f"Parameter ({name}) := custom value", edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict[str, str]:
        return {name: edit.text().strip() or AUTO_PARAM_DEFAULT_EXPR for name, edit in self._edits.items()}


class DiagnosticsDialog(QDialog):
    def __init__(self, report: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)
        self._browser = QTextBrowser()
        self._browser.setHtml(report)
        self._browser.setOpenExternalLinks(True)
        self._browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        layout.addWidget(self._browser)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        QTimer.singleShot(0, self._center)

    def update_report(self, report: str) -> None:
        self._browser.setHtml(report)

    def _center(self) -> None:
        target = self.parentWidget().screen() if self.parentWidget() and self.parentWidget().screen() else QApplication.primaryScreen()
        if target is None:
            return
        geometry = self.frameGeometry()
        geometry.moveCenter(target.availableGeometry().center())
        self.move(geometry.topLeft())


class ReportWorkerSignals(QObject):
    finished = Signal(object)


class ReportWorker(QRunnable):
    def __init__(self, task: Callable[[], object]) -> None:
        super().__init__()
        self._task = task
        self.signals = ReportWorkerSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit({"ok": True, "result": self._task()})
        except Exception as exc:
            self.signals.finished.emit({"ok": False, "error": str(exc)})


class TextSearchDialog(QDialog):
    findNextRequested = Signal(str, bool)
    findPreviousRequested = Signal(str, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Search text:"))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Search original and rewritten code")
        self.edit.installEventFilter(self)
        layout.addWidget(self.edit)
        self.case_insensitive = QCheckBox("Case insensitive")
        self.case_insensitive.setChecked(True)
        layout.addWidget(self.case_insensitive)
        buttons = QDialogButtonBox()
        previous_button = buttons.addButton("Previous", QDialogButtonBox.ButtonRole.ActionRole)
        next_button = buttons.addButton("Next", QDialogButtonBox.ButtonRole.ActionRole)
        close_button = buttons.addButton(QDialogButtonBox.Close)
        previous_button.clicked.connect(self._emit_previous)
        next_button.clicked.connect(self._emit_next)
        close_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _emit_next(self, _checked: bool = False) -> None:
        self.findNextRequested.emit(self.query(), self.case_insensitive.isChecked())

    def _emit_previous(self, _checked: bool = False) -> None:
        self.findPreviousRequested.emit(self.query(), self.case_insensitive.isChecked())

    def eventFilter(self, watched: QObject, event: Any) -> bool:  # noqa: N802
        if watched is self.edit and event.type() == QEvent.Type.KeyPress and event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self._emit_next()
            return True
        return super().eventFilter(watched, event)

    def query(self) -> str:
        return self.edit.text().strip()


class MainWindow(QMainWindow):
    def __init__(self, workspace_root: Path) -> None:
        super().__init__()
        self.workspace_root = workspace_root
        self.qasm_root = workspace_root / "qasm"
        self.split_root = self.qasm_root / "split"
        self.current_file = self.qasm_root / "bell_state.qasm"
        self.current_source = ""
        self.split_points: set[int] = set()
        self.parameter_bindings: dict[str, str] = {}
        self.shots = 1024
        self.timeout_s = 20
        self.distributed_nodes = 3
        self._find_query = ""
        self._find_case_insensitive = True
        self._find_matches: list[tuple[int, QWidget, QTextCursor]] = []
        self._find_index = -1
        self._parameter_prompt_pending = False
        self._parameter_prompt_open = False
        # Initialize rules: bypass (rule 0) disabled by default, all others enabled
        self.rules = [
            RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0)
            for rule in DEFAULT_RULES
        ]
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh)
        self._footer_blink_timer = QTimer(self)
        self._footer_blink_timer.setInterval(350)
        self._footer_blink_timer.timeout.connect(self._toggle_footer_visibility)
        self._footer_clear_timer = QTimer(self)
        self._footer_clear_timer.setSingleShot(True)
        self._footer_clear_timer.timeout.connect(self._clear_footer_message)
        self._runtime_state_timer = QTimer(self)
        self._runtime_state_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._runtime_state_timer.setInterval(120)
        self._runtime_state_timer.timeout.connect(self._refresh_runtime_run_state)
        self._runtime_run_token = 0
        self._runtime_run_start_monotonic: float | None = None
        self._runtime_executor: concurrent.futures.ProcessPoolExecutor | None = None
        self._runtime_future: concurrent.futures.Future[tuple[dict[str, int] | None, str | None, datetime, str, str]] | None = None
        self._runtime_future_token: int | None = None
        self._runtime_pending_result = None
        self._runtime_requested_backend = ""
        self._runtime_retry_attempted = False
        self._runtime_stopwatch_label = QLabel("")
        self._runtime_stopwatch_label.setVisible(False)
        self._runtime_stopwatch_label.setStyleSheet("font-weight: 700; color: #1f6f2a; padding-left: 8px; padding-right: 8px;")
        self._startup_graph_normalization_done = False
        self._thread_pool = QThreadPool(self)
        self._report_workers: list[ReportWorker] = []
        self._footer_label: QLabel | None = None
        self._ast_syncing = False
        self._ast_program: Any | None = None
        self._ast_source_editor: QWidget | None = None
        self.resize(1600, 1000)
        self._apply_style()
        self._build_ui()
        self._build_menus()
        self.statusBar().setSizeGripEnabled(False)
        self._update_window_title()
        self.load_file(self.current_file)
        QTimer.singleShot(0, self._apply_initial_split_sizes)
        self.showMaximized()

    @staticmethod
    def _runtime_backend_fallback_line() -> str:
        return "AER backends fallback: 1. MPS (Matrix Product State: chain of tensors); 2. default AER (monolithic state-vector)."

    @staticmethod
    def _normalize_runtime_backend_label(runtime_backend: str) -> str:
        label = (runtime_backend or "").strip().lower()
        if label == "mps":
            return "MPS"
        if label in {"monolithic", "default aer (statevector-like)", "default aer"}:
            return "monolithic"
        return "monolithic"

    def _update_window_title(self) -> None:
        self.setWindowTitle(f"DQC Quantum Workbench - {self.current_file.resolve()}")

    def _clear_footer_message(self) -> None:
        self._footer_blink_timer.stop()
        if self._footer_label is not None:
            self._footer_label.clear()
            self._footer_label.hide()

    def _toggle_footer_visibility(self) -> None:
        if self._footer_label is None or not self._footer_label.text():
            return
        self._footer_label.setVisible(not self._footer_label.isVisible())

    def _show_status_feedback(self, message: str, timeout_ms: int = 5000) -> None:
        if self._footer_label is None:
            self.statusBar().showMessage(message, timeout_ms)
            return
        self._footer_clear_timer.stop()
        self._footer_blink_timer.stop()
        self._footer_label.setText(message)
        self._footer_label.show()
        self._footer_blink_timer.start()
        self._footer_clear_timer.start(timeout_ms)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f8fbff; }
            QTabWidget::pane { border: 1px solid rgba(96, 165, 250, 0.25); border-radius: 10px; background: white; }
            QTabBar::tab { background: linear-gradient(to bottom, #e8eef7, #dbeafe); color: #0f172a; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: white; color: #1d4ed8; }
            QTabBar[dqcRewriteWarn="true"]::tab:last { color: #b91c1c; font-weight: 700; }
            QTabBar[dqcRewriteWarn="true"]::tab:last:selected { color: #b91c1c; font-weight: 700; }
            QSplitter::handle { background: rgba(96, 165, 250, 0.35); }
            QPushButton { background: linear-gradient(to bottom, #eff6ff, #dbeafe); color: #0f172a; border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 6px; padding: 6px 10px; }
            QPushButton:hover { background: linear-gradient(to bottom, #dbeafe, #bfdbfe); }
            QLabel { color: #0f172a; }
            QMenuBar { background: #f8fbff; color: #0f172a; }
            QMenuBar::item:selected { background: #dbeafe; }
            QMenu { background: white; color: #0f172a; border: 1px solid rgba(96, 165, 250, 0.25); }
            QMenu::item:selected { background: #dbeafe; }
            QPlainTextEdit, QTextBrowser, QTreeWidget { background: white; color: #0f172a; border: 1px solid rgba(96, 165, 250, 0.18); border-radius: 10px; }
            QStatusBar { background: linear-gradient(to right, #eff6ff, #f8fbff); color: #0f172a; border-top: 1px solid rgba(96, 165, 250, 0.22); }
            """
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)
        top_split = QSplitter(Qt.Horizontal)
        top_split.setChildrenCollapsible(True)
        outer_split = QSplitter(Qt.Vertical)
        outer_split.setChildrenCollapsible(True)

        self.code_tabs = QTabWidget()
        self.original_editor = CodeEditor()
        self.original_editor.textChanged.connect(self._schedule_refresh)
        self.original_editor.splitPointRequested.connect(self.toggle_split_point)
        self.original_editor.cursorPositionChanged.connect(lambda: self._sync_ast_from_editor(self.original_editor))
        self.rewritten_view = HtmlCodeView()
        self.rewritten_view.cursorPositionChanged.connect(lambda: self._sync_ast_from_editor(self.rewritten_view))
        self.rule_panel = RulePanel(self.rules)
        self.rule_panel.ruleToggled.connect(self.on_rule_toggled)
        self.rule_scroll = QScrollArea()
        self.rule_scroll.setWidgetResizable(True)
        self.rule_scroll.setWidget(self.rule_panel)
        self.code_tabs.addTab(self.original_editor, "Original")
        self.code_tabs.addTab(self.rule_scroll, "Compatibility Rules")
        self.code_tabs.addTab(self.rewritten_view, "Rewritten")
        self.code_tabs.setTabToolTip(2, "Rewritten source after applying active compatibility rules.")
        _original_tab_legend = (
            "<html><b>Original Code — Color Legend</b><br><br>"
                "<table cellspacing='0' style='width:760px;border-collapse:collapse;table-layout:fixed;'>"
                "<tr><td style='background:#fecaca;color:#b91c1c;padding:5px 10px;"
                "border-radius:3px;border-bottom:1px solid #cbd5e1;width:220px;'>&nbsp;● Red code&nbsp;</td>"
                "<td style='padding:5px 10px;border-bottom:1px solid #cbd5e1;'>"
                "Matches a rewriting rule; hover for details</td></tr>"

                "<tr><td style='color:#1d4ed8;font-weight:bold;padding:5px 10px;border-bottom:1px solid #cbd5e1;'>"
            "&nbsp;● Blue bold line number&nbsp;</td>"
                "<td style='padding:5px 10px;border-bottom:1px solid #cbd5e1;'>&nbsp;KaHyPar-suggested optimal split point</td></tr>"
                "<tr><td style='color:#64748b;padding:5px 10px;border-bottom:1px solid #cbd5e1;'>"
            "&nbsp;● Gray line number&nbsp;</td>"
                "<td style='padding:5px 10px;border-bottom:1px solid #cbd5e1;'>&nbsp;Normal line — no rule involvement</td></tr>"
                "<tr><td style='color:#b91c1c;font-weight:bold;text-decoration:underline;"
                "padding:5px 10px;'>&nbsp;bold + underlined text&nbsp;</td>"
                "<td style='padding:5px 10px;'>&nbsp;Split-pragma line, from disk or from a live right-click toggle</td></tr>"
            "</table></html>"
        )
        self.code_tabs.setTabToolTip(0, _original_tab_legend)
        self.code_tabs.currentChanged.connect(self._sync_ast_from_current_tab)
        self.code_tabs.setMinimumHeight(0)
        self.code_tabs.setMinimumWidth(0)
        self._set_rewritten_tab_fallback_warning([])

        code_shell = QWidget()
        code_layout = QVBoxLayout(code_shell)
        code_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestion_label = QLabel("Split suggestions: none yet")
        self.suggestion_label.setStyleSheet("color: #1d4ed8; font-weight: 700; text-decoration: underline;")
        code_layout.addWidget(self._make_header("Code", [("Find", self.show_find_dialog), ("Zoom +", lambda: self.zoom_active(1)), ("Zoom -", lambda: self.zoom_active(-1)), ("Reset", self.zoom_reset)], [self.suggestion_label], accent="#3b82f6", area_name="Code"))
        code_layout.addWidget(self.code_tabs)
        self.code_tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.code_tabs.tabBar().customContextMenuRequested.connect(self._show_code_tab_bom)
        code_shell.setMinimumHeight(0)
        code_shell.setMinimumWidth(0)
        code_shell.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        code_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(59,130,246,0.08), rgba(255,255,255,0.98)); border: 1px solid rgba(59,130,246,0.22); border-radius: 14px; }")

        runtime_shell = QWidget()
        runtime_layout = QVBoxLayout(runtime_shell)
        runtime_layout.setContentsMargins(0, 0, 0, 0)
        runtime_layout.addWidget(self._make_header("Runtime", [("Run now", self.run_manual), ("Shots", self.change_shots), ("Timeout", self.change_timeout), ("QPUs", self.change_distributed_nodes)], accent="#10b981", area_name="Runtime"))
        self.circuit_view = CircuitView()
        self.runtime_output = QPlainTextEdit()
        self.runtime_output.setReadOnly(True)
        self.runtime_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.runtime_output.setFont(QFont("DejaVu Sans Mono", 10))
        self.runtime_output.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        min_runtime_lines = 7
        min_runtime_height = self.runtime_output.fontMetrics().lineSpacing() * min_runtime_lines + 12
        self._runtime_output_min_height = min_runtime_height
        self.runtime_output.setMinimumHeight(self._runtime_output_min_height)

        self.runtime_split = QSplitter(Qt.Vertical)
        self.runtime_split.setChildrenCollapsible(True)
        self.runtime_split.addWidget(self.circuit_view)
        self.runtime_split.addWidget(self.runtime_output)
        self.runtime_split.setStretchFactor(0, 4)
        self.runtime_split.setStretchFactor(1, 1)
        self.runtime_split.setSizes([max(1, min_runtime_height * 4), max(1, min_runtime_height)])
        self.runtime_split.setMinimumWidth(0)
        runtime_layout.addWidget(self.runtime_split)
        runtime_shell.setMinimumHeight(0)
        runtime_shell.setMinimumWidth(0)
        runtime_shell.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        runtime_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(16,185,129,0.07), rgba(255,255,255,0.98)); border: 1px solid rgba(16,185,129,0.22); border-radius: 14px; }")

        top_split.addWidget(code_shell)
        top_split.addWidget(runtime_shell)

        graphs_shell = QWidget()
        graphs_layout = QVBoxLayout(graphs_shell)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        
        # Custom header for Graphs with checkbox positioned close to title
        graphs_header_widget = QWidget()
        graphs_header_layout = QHBoxLayout(graphs_header_widget)
        graphs_header_layout.setContentsMargins(0, 0, 0, 0)
        graphs_title = QLabel("Graphs")
        graphs_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f59e0b;")
        graphs_title.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        graphs_title.customContextMenuRequested.connect(lambda _pos: self._show_bom_dialog("Graphs"))
        graphs_header_layout.addWidget(graphs_title)
        graphs_header_layout.addStretch(1)
        self.graph_source_toggle = QCheckBox("Use rewritten code")
        self.graph_source_toggle.setChecked(True)
        self.graph_source_toggle.stateChanged.connect(self.refresh_graphs)
        self.graph_source_toggle.setStyleSheet("color: #0f172a;")
        graphs_header_layout.addWidget(self.graph_source_toggle)
        graphs_header_layout.addStretch(4)
        graphs_header_widget.setStyleSheet("QWidget { background: linear-gradient(to right, rgba(255,255,255,0.92), rgba(239,246,255,0.92)); border-bottom: 2px solid #f59e0b; border-top-left-radius: 10px; border-top-right-radius: 10px; }")
        graphs_header_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        graphs_header_widget.customContextMenuRequested.connect(lambda _pos: self._show_bom_dialog("Graphs"))
        graphs_layout.addWidget(graphs_header_widget)
        self.graph_tabs = QTabWidget()
        self.ast_tree_view = ParseTreeView()
        self.ast_tree_view.itemSelectionChanged.connect(self._sync_editor_from_ast_tree)
        self.overall_dag_view = QiskitDagTab("Overall DAG")
        self.qubit_graph_view = QubitInteractionTab("Qubit Interaction")
        self.chunk_graph_view = ChunkDagTab("Chunk Dependencies")
        self.graph_tabs.addTab(self.ast_tree_view, "AST parse-tree")
        self.graph_tabs.addTab(self.overall_dag_view, "Overall DAG")
        self.graph_tabs.addTab(self.qubit_graph_view, "Qubit Interaction")
        self.graph_tabs.addTab(self.chunk_graph_view, "Chunk Dependencies")
        self.graph_tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.graph_tabs.tabBar().customContextMenuRequested.connect(self._show_graph_tab_bom)
        self.graph_tabs.setMinimumHeight(0)
        graphs_layout.addWidget(self.graph_tabs)
        graphs_shell.setMinimumHeight(0)
        graphs_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(245,158,11,0.07), rgba(255,255,255,0.98)); border: 1px solid rgba(245,158,11,0.22); border-radius: 14px; }")

        outer_split.addWidget(top_split)
        outer_split.addWidget(graphs_shell)

        root.addWidget(outer_split)
        self._footer_label = QLabel("")
        self._footer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self._footer_label.setStyleSheet("padding: 4px 10px; color: #1e3a8a; font-weight: 700; background: rgba(219,234,254,0.7); border-radius: 8px;")
        self._footer_label.hide()
        self.statusBar().addWidget(self._footer_label, 1)
        self.statusBar().addPermanentWidget(self._runtime_stopwatch_label)
        self._top_split = top_split
        self._outer_split = outer_split
        self._runtime_actions: tuple[QAction, QAction, QAction] | None = None

    def _apply_initial_split_sizes(self) -> None:
        width = max(1, self.width())
        height = max(1, self.height())
        self._top_split.setSizes([max(1, int(width * (1 / 3))), max(1, int(width * (2 / 3)))])
        self._outer_split.setSizes([max(1, int(height * (2 / 3))), max(1, int(height * (1 / 3)))])
        runtime_total = max(1, self.runtime_split.size().height())
        output_height = max(self._runtime_output_min_height, int(runtime_total * 0.2))
        circuit_height = max(1, runtime_total - output_height)
        self.runtime_split.setSizes([circuit_height, output_height])
        # Re-apply circuit auto-fit after splitter geometry settles.
        self._schedule_circuit_refit()
        self._schedule_circuit_refit(150)
        # Reflow chunk graph after startup geometry settles, so initial load
        # uses the same layout basis as a manual file reload.
        self._schedule_chunk_graph_reflow()
        self._schedule_chunk_graph_reflow(150)

    def _schedule_circuit_refit(self, delay_ms: int = 0) -> None:
        QTimer.singleShot(max(0, delay_ms), self._refit_circuit_view)

    def _refit_circuit_view(self) -> None:
        try:
            scene = self.circuit_view.view.scene()
            if scene is None or scene.itemsBoundingRect().isNull():
                return
            self.circuit_view.view.fit_scene()
        except Exception:
            return

    def _schedule_chunk_graph_reflow(self, delay_ms: int = 0) -> None:
        QTimer.singleShot(max(0, delay_ms), self._reflow_chunk_graph_view)

    def _reflow_chunk_graph_view(self) -> None:
        try:
            view = self.chunk_graph_view.view
            if hasattr(view, "reflow_layout"):
                view.reflow_layout()
            if hasattr(view, "fit_scene"):
                view.fit_scene()
        except Exception:
            return

    def _schedule_startup_graph_normalization(self, delay_ms: int = 0) -> None:
        QTimer.singleShot(max(0, delay_ms), self._normalize_startup_graph_views)

    def _normalize_startup_graph_views(self) -> None:
        if not hasattr(self, "_latest_result"):
            return
        try:
            # Rebuild graph tabs once after the window is shown so they use
            # settled viewport/splitter geometry (same basis as manual reload).
            self.refresh_graphs()
            self._reflow_chunk_graph_view()
        except Exception:
            return

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self._startup_graph_normalization_done:
            return
        self._startup_graph_normalization_done = True
        self._schedule_startup_graph_normalization()
        self._schedule_startup_graph_normalization(150)

    def _make_header(self, title: str, left_actions: list[tuple[str, Callable[[], None]]], right_widgets: list[QWidget] | None = None, accent: str = "#3b82f6", area_name: str | None = None) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {accent};")
        bom_area = area_name or title
        label.setProperty("bomAreaName", bom_area)
        label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        label.customContextMenuRequested.connect(self._on_area_header_context_menu)
        layout.addWidget(label)
        layout.addStretch(1)
        for text, handler in left_actions:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        for widget_item in right_widgets or []:
            layout.addWidget(widget_item)
        widget.setProperty("bomAreaName", bom_area)
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(self._on_area_header_context_menu)
        widget.setStyleSheet(f"QWidget {{ background: linear-gradient(to right, rgba(255,255,255,0.92), rgba(239,246,255,0.92)); border-bottom: 2px solid {accent}; border-top-left-radius: 10px; border-top-right-radius: 10px; }}")
        return widget

    def _bom_catalog(self) -> dict[str, list[str]]:
        target_packages, _ = self._bom_spec()
        return target_packages

    def _bom_spec(self) -> tuple[dict[str, list[str]], dict[str, str]]:
        package_import_modules = {
            "PySide6": "PySide6",
            "qiskit": "qiskit",
            "qiskit-aer": "qiskit_aer",
            "qiskit-qasm3-import": "qiskit_qasm3_import",
            "openqasm3": "openqasm3",
            "antlr4-python3-runtime": "antlr4",
            "networkx": "networkx",
            "kahypar": "kahypar",
            "matplotlib": "matplotlib",
            "pylatexenc": "pylatexenc",
        }
        target_packages = {
            "Code": ["PySide6", "openqasm3", "antlr4-python3-runtime", "kahypar"],
            "Code/Original": ["PySide6", "openqasm3", "antlr4-python3-runtime", "kahypar"],
            "Code/Compatibility Rules": ["PySide6", "openqasm3", "antlr4-python3-runtime", "kahypar"],
            "Code/Rewritten": ["PySide6", "openqasm3", "antlr4-python3-runtime", "kahypar"],
            "Runtime": ["PySide6", "qiskit", "qiskit-aer", "qiskit-qasm3-import", "matplotlib", "pylatexenc"],
            "Graphs": ["PySide6", "openqasm3", "antlr4-python3-runtime", "networkx", "qiskit-qasm3-import", "matplotlib", "kahypar"],
            "Graphs/AST parse-tree": ["PySide6", "openqasm3", "antlr4-python3-runtime", "networkx", "kahypar"],
            "Graphs/Overall DAG": ["PySide6", "qiskit-qasm3-import", "networkx", "matplotlib"],
            "Graphs/Qubit Interaction": ["PySide6", "qiskit-qasm3-import", "networkx", "matplotlib"],
            "Graphs/Chunk Dependencies": ["PySide6", "networkx", "matplotlib", "kahypar"],
        }
        return target_packages, package_import_modules

    def _all_bom_packages(self) -> list[str]:
        target_packages, _ = self._bom_spec()
        ordered: list[str] = []
        for libs in target_packages.values():
            for package in libs:
                if package not in ordered:
                    ordered.append(package)
        return sorted(ordered, key=str.casefold)

    def _import_health_for_packages(self, packages: list[str]) -> dict[str, bool]:
        _, package_import_modules = self._bom_spec()
        health: dict[str, bool] = {}
        for package in packages:
            module_name = package_import_modules.get(package)
            if not module_name:
                health[package] = False
                continue
            health[package] = importlib.util.find_spec(module_name) is not None
        return health

    def _package_status_text(self, package: str, versions: dict[str, str], updates: dict[str, str]) -> str:
        version = versions.get(package, "not installed")
        latest = updates.get(package, "unavailable")
        if latest in {"unavailable", version, "not installed"}:
            status = "up-to-date" if version != "not installed" else "not installed"
        else:
            status = f"out-of-date: latest is <a href='https://pypi.org/project/{package}/{latest}/'>{latest}</a>"
        return f"<b><a href='https://pypi.org/project/{package}/'>{package}</a></b>: {version} ({status})"

    def _target_libraries(self, target: str) -> list[str]:
        catalog = self._bom_catalog()
        libs = catalog.get(target) or catalog.get(target.split("/")[0], [])
        return sorted(libs, key=str.casefold)

    def _loading_dialog_html(self, title: str, message: str) -> str:
        return f"<h2 style='margin-top:0'>{title}</h2><p>{message}</p>"

    def _error_dialog_html(self, title: str, error: str) -> str:
        return f"<h2 style='margin-top:0'>{title}</h2><p><b>Failed to collect diagnostics:</b> {error}</p>"

    def _run_report_async(self, task: Callable[[], object], on_done: Callable[[dict], None]) -> None:
        worker = ReportWorker(task)
        self._report_workers.append(worker)

        def _cleanup_and_forward(payload: dict, current: ReportWorker = worker) -> None:
            if current in self._report_workers:
                self._report_workers.remove(current)
            on_done(payload)

        worker.signals.finished.connect(_cleanup_and_forward)
        self._thread_pool.start(worker)

    def _render_bom_target_list_html(self) -> str:
        lines = ["<p><b>Bill of materials (by GUI target):</b></p>", "<ul>"]
        for target, libs in sorted(self._bom_catalog().items()):
            libs_sorted = sorted(libs, key=str.casefold)
            lines.append(f"<li><b>{target}</b>: {', '.join(libs_sorted)}</li>")
        lines.append("</ul>")
        return "".join(lines)

    def _render_import_health_html(self, packages: list[str]) -> str:
        health = self._import_health_for_packages(packages)
        lines = ["<p><b>Import health:</b></p>", "<ul>"]
        for package in packages:
            status = "ok" if health.get(package, False) else "missing"
            lines.append(f"<li>{package} import: {status}</li>")
        lines.append("</ul>")
        return "".join(lines)

    def _bom_dialog_html(self, target: str, versions: dict[str, str], updates: dict[str, str]) -> str:
        libs = self._target_libraries(target)
        lines = [f"<h2 style='margin-top:0'>{target} BoM</h2>"]
        if not libs:
            lines.append("<p>No external libraries recorded for this target.</p>")
        else:
            lines.append("<p>External libraries used by this target:</p><ul>")
            for package in libs:
                lines.append(f"<li>{self._package_status_text(package, versions, updates)}</li>")
            lines.append("</ul>")
            lines.append(self._render_import_health_html(libs))
        lines.append("<p style='color:#475569'>Tip: use Runtime -> Diagnostics for global checks and smoke tests.</p>")
        return "".join(lines)

    def _diagnostics_html(self, versions: dict[str, str], updates: dict[str, str], smoke: dict) -> str:
        packages = self._all_bom_packages()
        lines = ["<h2 style='margin-top:0'>Diagnostics</h2>", "<p>Installed packages and update status:</p>", "<ul>"]
        for package in packages:
            lines.append(f"<li>{self._package_status_text(package, versions, updates)}</li>")
        lines.append("</ul>")
        lines.append(self._render_bom_target_list_html())
        lines.append(self._render_import_health_html(packages))
        lines.append(f"<p>Smoke test (Hadamard gate, shots={self.shots}): duration {smoke['duration_s']:.3f}s, counts {smoke['counts']}</p>")
        return "".join(lines)

    def _on_area_header_context_menu(self, _pos) -> None:
        sender = self.sender()
        area_name = sender.property("bomAreaName") if sender is not None else None
        if not area_name:
            return
        self._show_bom_dialog(str(area_name))

    def _show_code_tab_bom(self, pos) -> None:
        tab_bar = self.code_tabs.tabBar()
        index = tab_bar.tabAt(pos)
        if index < 0:
            return
        self._show_bom_dialog(f"Code/{self.code_tabs.tabText(index)}")

    def _show_graph_tab_bom(self, pos) -> None:
        tab_bar = self.graph_tabs.tabBar()
        index = tab_bar.tabAt(pos)
        if index < 0:
            return
        self._show_bom_dialog(f"Graphs/{self.graph_tabs.tabText(index)}")

    def _show_bom_dialog(self, target: str) -> None:
        packages = self._all_bom_packages()
        dialog = DiagnosticsDialog(self._loading_dialog_html(f"{target} BoM", "⟳ Checking library versions and import health..."), self)

        def _task() -> dict:
            versions = package_versions(packages)
            updates = latest_versions_from_pypi(packages)
            return {"versions": versions, "updates": updates}

        def _done(payload: dict) -> None:
            if not payload.get("ok"):
                dialog.update_report(self._error_dialog_html(f"{target} BoM", str(payload.get("error", "unknown error"))))
                return
            result = payload.get("result", {})
            versions = result.get("versions", {})
            updates = result.get("updates", {})
            dialog.update_report(self._bom_dialog_html(target, versions, updates))

        self._run_report_async(_task, _done)
        dialog.exec()

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        load_action = QAction("Load file ...", self)
        load_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(load_action)
        save_action = QAction("Save split chunks", self)
        save_action.triggered.connect(self.save_split_chunks)
        file_menu.addAction(save_action)
        examples_menu = QMenu("Examples", self)
        file_menu.addMenu(examples_menu)
        examples_menu.aboutToShow.connect(lambda: self._populate_examples_menu(examples_menu, self.qasm_root))
        self._populate_examples_menu(examples_menu, self.qasm_root)

        view_menu = self.menuBar().addMenu("View")
        for text, handler in [("Zoom in", lambda: self.zoom_active(1)), ("Zoom out", lambda: self.zoom_active(-1)), ("Zoom reset", self.zoom_reset)]:
            action = QAction(text, self)
            action.triggered.connect(handler)
            view_menu.addAction(action)
        self._find_action = QAction("Find ...", self)
        self._find_action.setShortcut(QKeySequence.Find)
        self._find_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self._find_action.triggered.connect(self.show_find_dialog)
        view_menu.addAction(self._find_action)

        runtime_menu = self.menuBar().addMenu("Runtime")
        run_action = QAction("Run manually", self)
        run_action.triggered.connect(self.run_manual)
        runtime_menu.addAction(run_action)
        shots_action = QAction(f"Qiskit shots ({self.shots})", self)
        shots_action.triggered.connect(self.change_shots)
        runtime_menu.addAction(shots_action)
        timeout_action = QAction(f"Timeout ({self.timeout_s} s)", self)
        timeout_action.triggered.connect(self.change_timeout)
        runtime_menu.addAction(timeout_action)
        nodes_action = QAction(f"Distributed nodes/QPUs ({self.distributed_nodes})", self)
        nodes_action.triggered.connect(self.change_distributed_nodes)
        runtime_menu.addAction(nodes_action)
        diagnostics_action = QAction("Diagnostics", self)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        runtime_menu.addAction(diagnostics_action)
        self._runtime_actions = (shots_action, timeout_action, nodes_action)

        help_menu = self.menuBar().addMenu("Help")
        gpl_action = QAction("GPL3 Licence", self)
        gpl_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.gnu.org/licenses/gpl-3.0.en.html")))
        help_menu.addAction(gpl_action)
        bib_menu = QMenu("Bibliography", self)
        help_menu.addMenu(bib_menu)
        self._populate_bibliography_menu(bib_menu)
        qcomm_action = QAction("Q-comm Template Guide", self)
        qcomm_action.triggered.connect(self._show_qcomm_template_guide)
        help_menu.addAction(qcomm_action)

    def _populate_examples_menu(self, menu: QMenu, root: Path) -> None:
        menu.clear()
        if not root.exists():
            return
        show_all_files = root == self.split_root or self.split_root in root.parents
        for path in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if path.is_dir():
                sub = menu.addMenu(path.name)
                self._populate_examples_menu(sub, path)
            elif show_all_files or path.suffix.lower() in {".qasm", ".inc"}:
                action = QAction(path.name, self)
                action.triggered.connect(lambda checked=False, selected=path: self.load_file(selected))
                menu.addAction(action)

    def _populate_bibliography_menu(self, menu: QMenu) -> None:
        menu.clear()
        bib_file = self.workspace_root / "biblio.url"
        if not bib_file.exists():
            return
        for url in (line.strip() for line in bib_file.read_text(encoding="utf-8").splitlines() if line.strip()):
            action = QAction(url, self)
            action.triggered.connect(lambda checked=False, target=url: QDesktopServices.openUrl(QUrl(target)))
            menu.addAction(action)

    def _show_qcomm_template_guide(self) -> None:
        """Show a help dialog documenting the q-comm_template.qasm contract."""
        template_path = Path(__file__).with_name("q-comm_template.qasm")

        # Read current template and run validation
        if template_path.exists():
            template_text = template_path.read_text(encoding="utf-8")
            errors = validate_qcomm_template(template_text)
        else:
            template_text = ""
            errors = [f"Template file not found: {template_path}"]

        ident_rows = "".join(
            f"<tr>"
            f"<td style='padding:4px 10px 4px 0; font-family:monospace; white-space:nowrap; color:#1e3a8a;'><b>{ident}</b></td>"
            f"<td style='padding:4px 0;'>{desc}</td>"
            f"</tr>"
            for ident, desc in [
                ("q_SOURCE",
                 "Placeholder for the qubit being teleported.  "
                 "The line <code>qubit q_SOURCE;</code> is <em>removed</em> "
                 "during adaptation (the qubit is already declared upstream).  "
                 "Every other occurrence is replaced with the actual qubit name."),
                ("q_epr",
                 "Local EPR qubit allocated for entanglement.  "
                 "Renamed to <code>{qubit}_epr_{split_id}</code> to avoid name collisions "
                 "when multiple split points are present."),
                ("q_epr_TARGET",
                 "Remote EPR qubit (the entangled partner received by the next chunk).  "
                 "Renamed to <code>{qubit}_epr_TARGET_{split_id}</code>."),
                ("telept_Zcorrect_q",
                 "Classical bit holding the Z-basis measurement result used for correction.  "
                 "Renamed to <code>telept_Zcorrect_{qubit}_{split_id}</code>."),
                ("telept_Xcorrect_q",
                 "Classical bit holding the X-basis measurement result used for correction.  "
                 "Renamed to <code>telept_Xcorrect_{qubit}_{split_id}</code>."),
            ]
        )

        status_html: str
        if errors:
            items = "".join(f"<li style='color:#b91c1c;'>{e}</li>" for e in errors)
            status_html = (
                f"<p style='color:#b91c1c;'><b>⚠ Template validation failed "
                f"({len(errors)} error(s)):</b></p><ul>{items}</ul>"
                f"<p>Restore the missing patterns before saving the file "
                f"to ensure teleportation output is correct.</p>"
            )
        else:
            status_html = "<p style='color:#15803d;'><b>✓ Template is valid.</b></p>"

        html = f"""
<html><body style='font-family:sans-serif; font-size:13px; margin:12px;'>
<h2 style='margin-top:0;'>Q-comm Template Guide</h2>

<p>The file <code style='color:#1e3a8a;'>{template_path.name}</code>
(located at <code>{template_path}</code>) defines a single quantum teleportation
circuit in QASM 3 syntax.  Rewriting rule&nbsp;<b>#9 (Split-generated teleportations)</b>
reads this template and injects one adapted copy for <em>each qubit dependency</em>
that must cross a split-point boundary.</p>

<h3>Adaptation contract</h3>
<p>The following identifiers are required.  Do <em>not</em> rename or remove them
when editing the template; you may freely add comments, adjust gate sequences,
or reorder lines as long as these identifiers are kept:</p>

<table style='border-collapse:collapse; width:100%;'>
{ident_rows}
</table>

<h3>Required declaration line</h3>
<p>The line</p>
<pre style='background:#f1f5f9; padding:6px 10px; border-radius:4px;'>qubit q_SOURCE;</pre>
<p>must appear verbatim (leading/trailing whitespace is ignored).
It is <em>removed</em> from each adapted copy because the source qubit is
already declared in the surrounding chunk code.</p>

<h3>Name-mangling rules</h3>
<p>For a dependency qubit named <code>w</code> at split&nbsp;<code>N</code>:</p>
<ul>
  <li><code>q_epr</code> &rarr; <code>w_epr_N</code></li>
  <li><code>q_epr_TARGET</code> &rarr; <code>w_epr_TARGET_N</code></li>
  <li><code>telept_Zcorrect_q</code> &rarr; <code>telept_Zcorrect_w_N</code></li>
  <li><code>telept_Xcorrect_q</code> &rarr; <code>telept_Xcorrect_w_N</code></li>
  <li><code>q_SOURCE</code> &rarr; <code>w</code>&nbsp;(the actual qubit name)</li>
</ul>
<p>For an array element such as <code>w[1]</code> the brackets are stripped:
<code>w1_epr_N</code>, <code>telept_Zcorrect_w1_N</code>, etc.</p>

<h3>Current template status</h3>
{status_html}
</body></html>
"""

        dlg = QDialog(self)
        dlg.setWindowTitle("Q-comm Template Guide")
        dlg.resize(680, 540)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 8)

        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(True)
        browser.setHtml(html)
        layout.addWidget(browser)

        btns = QDialogButtonBox(QDialogButtonBox.Close, dlg)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        dlg.exec()

    def _schedule_refresh(self) -> None:
        self._refresh_timer.start(250)

    def _prompt_for_parameters(self, force: bool = False) -> None:
        if self._parameter_prompt_open:
            return
        self._parameter_prompt_open = True
        try:
            analysis_source = self._split_save_source()
            required = scan_inputs(analysis_source)
            if not required or (self.parameter_bindings and not force):
                return
            dialog = ParameterDialog(required, self)
            if dialog.exec() == QDialog.Accepted:
                self.parameter_bindings = dialog.values()
                self.refresh()
        finally:
            self._parameter_prompt_open = False
            self._parameter_prompt_pending = False

    def _strip_pragmas_with_mapping(self, source_text: str) -> tuple[str, dict[int, int], dict[int, int]]:
        stripped_lines: list[str] = []
        display_to_stripped: dict[int, int] = {}
        stripped_to_display: dict[int, int] = {}
        for display_line_no, line in enumerate(source_text.splitlines(), start=1):
            if line.strip().startswith("pragma dqc.v1.split"):
                continue
            stripped_line_no = len(stripped_lines) + 1
            stripped_lines.append(line)
            display_to_stripped[display_line_no] = stripped_line_no
            stripped_to_display[stripped_line_no] = display_line_no
        return "\n".join(stripped_lines), display_to_stripped, stripped_to_display

    def _clicked_line_to_split_point(self, source_text: str, clicked_line: int) -> int:
        lines = source_text.splitlines()
        if clicked_line < 1:
            return clicked_line
        stripped_count = 0
        for line_no, line in enumerate(lines, start=1):
            if line_no == clicked_line:
                return stripped_count + 1
            if not line.strip().startswith("pragma dqc.v1.split"):
                stripped_count += 1
        return stripped_count + 1

    def load_file(self, path: Path, *, preserve_parameter_bindings: bool = False, prompt_for_parameters: bool = True) -> None:
        if not path.exists():
            QMessageBox.warning(self, "Missing file", f"Cannot find {path}")
            return
        self.current_file = path
        self._update_window_title()
        self.current_source = read_text(path)
        if not preserve_parameter_bindings:
            self.parameter_bindings = {}
        self.split_points = split_points_from_source(self.current_source)
        self.original_editor.blockSignals(True)
        self.original_editor.setPlainText(self.current_source)
        self.original_editor.blockSignals(False)
        self.original_editor.update_line_number_area_width(self.original_editor.blockCount())
        self.original_editor.line_number_area.update()
        self.original_editor.setRewriteSpans([])
        self.original_editor.setPragmaLines(split_pragma_line_numbers(self.current_source))
        self.rule_panel.set_states({rule.rule_id for rule in self.rules if rule.enabled}, self._rule_bypass_enabled())
        self._refresh_timer.stop()
        self._parameter_prompt_pending = False
        self._parameter_prompt_open = False
        self._suppress_parameter_prompt = not prompt_for_parameters
        self.refresh()
        self._suppress_parameter_prompt = False

    def open_file_dialog(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Load QASM3 file", str(self.qasm_root), "QASM files (*.qasm *.dqc *.inc *.txt);;All files (*.*)")
        if selected:
            self.load_file(Path(selected))

    def toggle_split_point(self, line_no: int) -> None:
        current_display_source = self.original_editor.toPlainText()
        self.split_points = split_points_from_source(current_display_source)
        clicked_line = line_no
        line_no = self._clicked_line_to_split_point(current_display_source, line_no)
        clicked_block = self.original_editor.document().findBlockByNumber(max(0, clicked_line - 1))
        if clicked_block.isValid():
            cursor = QTextCursor(clicked_block)
            self.original_editor.setTextCursor(cursor)
        analysis_source = self._split_save_source(current_display_source)
        if line_no in self.split_points:
            self.split_points.remove(line_no)
        else:
            if line_is_inside_blocking_scope(analysis_source, line_no):
                self._show_status_feedback("Split blocked: inner scopes cannot be split.")
                return
            self.split_points.add(line_no)
        display_source = self._reconstruct_source_with_pragmas(analysis_source, self.split_points)
        self.current_source = display_source
        self._set_original_editor_text_preserve_state(display_source)
        self.refresh()

    def _reconstruct_source_with_pragmas(self, raw_source: str, split_points: set[int]) -> str:
        if not split_points:
            return raw_source
        lines = raw_source.splitlines()
        split_points_sorted = sorted(split_points)
        result_lines = []
        pragma_id = 1
        for line_no, line in enumerate(lines, start=1):
            if line_no in split_points_sorted:
                result_lines.append(f"pragma dqc.v1.split id={pragma_id}")
                pragma_id += 1
            result_lines.append(line)
        if len(lines) + 1 in split_points_sorted:
            result_lines.append(f"pragma dqc.v1.split id={pragma_id}")
        return "\n".join(result_lines)

    def on_rule_toggled(self, rule_id: int, checked: bool) -> None:
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = checked
                break
        self.rule_panel.set_states({rule.rule_id for rule in self.rules if rule.enabled}, self._rule_bypass_enabled())
        self.refresh()

    def _rule_bypass_enabled(self) -> bool:
        return any(rule.rule_id == 0 and rule.enabled for rule in self.rules)

    def rewritten_text(self) -> str:
        return self._latest_result.rewritten_source if hasattr(self, "_latest_result") else self.original_editor.toPlainText()

    def _iter_ast_nodes(self, node: Any):
        yield node
        if isinstance(node, dict):
            for value in node.values():
                yield from self._iter_ast_nodes(value)
            return
        if isinstance(node, (list, tuple, set)):
            for value in node:
                yield from self._iter_ast_nodes(value)
            return
        fields = getattr(node, "__dict__", {})
        for key, value in fields.items():
            if key.startswith("_"):
                continue
            yield from self._iter_ast_nodes(value)

    def _node_span(self, node: Any) -> Any | None:
        span = getattr(node, "span", None) or getattr(node, "_span", None)
        if span is None:
            return None
        required = ("start_line", "start_column", "end_line", "end_column")
        if not all(hasattr(span, name) for name in required):
            return None
        return span

    def _clamp_editor_pos(self, editor: QWidget, pos: int) -> int:
        return max(0, min(pos, max(0, editor.document().characterCount() - 1)))

    def _span_point_to_pos(self, editor: QWidget, line_index: int, column: int, is_end: bool = False) -> int:
        document = editor.document()
        block = document.findBlockByNumber(max(0, line_index))
        add = 1 if is_end else 0
        if not block.isValid():
            return self._clamp_editor_pos(editor, column + add)
        line_len = len(block.text())
        # Some parsers expose columns as absolute document offsets instead of line-relative columns.
        if column <= line_len + add:
            pos = block.position() + column + add
        else:
            pos = column + add
        return self._clamp_editor_pos(editor, pos)

    def _span_to_abs_range(self, editor: QWidget, span: Any) -> tuple[int, int]:
        start_line = int(getattr(span, "start_line", 1) or 1) - 1
        end_line = int(getattr(span, "end_line", 1) or 1) - 1
        start_col = int(getattr(span, "start_column", 0) or 0)
        end_col = int(getattr(span, "end_column", 0) or 0)
        start = self._span_point_to_pos(editor, start_line, start_col, is_end=False)
        end = self._span_point_to_pos(editor, end_line, end_col, is_end=True)
        if end <= start:
            end = self._clamp_editor_pos(editor, start + 1)
        return start, end

    def _node_sync_token(self, node: Any) -> str:
        node_name = getattr(node, "name", None)
        if isinstance(node_name, str):
            token = node_name.strip()
            if token:
                return token
        return ""

    def _refine_span_range_for_node(self, editor: QWidget, node: Any, start: int, end: int) -> tuple[int, int]:
        token = self._node_sync_token(node)
        if not token:
            return start, end

        text = editor.toPlainText()
        if not text:
            return start, end

        start = max(0, min(start, len(text)))
        end = max(start, min(end, len(text)))
        current = text[start:end]
        if token in current:
            return start, end

        window_radius = 512
        window_start = max(0, start - window_radius)
        window_end = min(len(text), max(end, start) + window_radius)
        window = text[window_start:window_end]

        nearest_start: int | None = None
        nearest_distance: int | None = None
        search_from = 0
        while True:
            rel_index = window.find(token, search_from)
            if rel_index < 0:
                break
            abs_index = window_start + rel_index
            distance = abs(abs_index - start)
            if nearest_start is None or nearest_distance is None or distance < nearest_distance:
                nearest_start = abs_index
                nearest_distance = distance
            search_from = rel_index + 1

        if nearest_start is None:
            return start, end
        return nearest_start, min(len(text), nearest_start + len(token))

    def _tree_node_at_cursor(self, editor: QWidget, program: Any) -> Any | None:
        cursor_pos = editor.textCursor().position()
        best_node = None
        best_size = None
        for node in self._iter_ast_nodes(program):
            span = self._node_span(node)
            if span is None:
                continue
            start, end = self._span_to_abs_range(editor, span)
            if not (start <= cursor_pos < end):
                continue
            size = end - start
            if best_node is None or (best_size is not None and size < best_size) or best_size is None:
                best_node = node
                best_size = size
        return best_node

    def _sync_ast_from_current_tab(self, index: int) -> None:
        editor = self.original_editor if index == 0 else self.rewritten_view if index == 2 else None
        if editor is None:
            return
        self._sync_ast_from_editor(editor)

    def _sync_ast_from_editor(self, editor: QWidget) -> None:
        if self._ast_syncing or self._ast_program is None:
            return
        if self._ast_source_editor is not None and editor is not self._ast_source_editor:
            return
        node = self._tree_node_at_cursor(editor, self._ast_program)
        if node is None:
            return
        self._ast_syncing = True
        try:
            self.ast_tree_view.select_node(node)
        finally:
            self._ast_syncing = False

    def _sync_editor_from_ast_tree(self) -> None:
        if self._ast_syncing:
            return
        items = self.ast_tree_view.selectedItems()
        if not items:
            return
        node = items[0].data(0, Qt.ItemDataRole.UserRole)
        span = self._node_span(node)
        if span is None:
            return
        editor = self._ast_source_editor if self._ast_source_editor is not None else self.original_editor
        self._ast_syncing = True
        try:
            start, end = self._span_to_abs_range(editor, span)
            start, end = self._refine_span_range_for_node(editor, node, start, end)
            document = editor.document()
            limit = max(0, document.characterCount() - 1)
            start = max(0, min(start, limit))
            end = max(0, min(end, limit))
            if end < start:
                end = start
            cursor = QTextCursor(document)
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            editor.setTextCursor(cursor)
            if editor is self.original_editor:
                self.code_tabs.setCurrentIndex(0)
                self.original_editor.ensureCursorVisible()
            elif editor is self.rewritten_view:
                self.code_tabs.setCurrentIndex(2)
                self.rewritten_view.ensureCursorVisible()
        finally:
            self._ast_syncing = False

    def refresh_graphs(self) -> None:
        if not hasattr(self, "_latest_result"):
            return
        
        # Determine which result to use based on checkbox state
        use_rewritten = self.graph_source_toggle.isChecked()
        
        if use_rewritten:
            # Use the rewritten code result (already computed with active rules)
            result = self._latest_result
        else:
            # Analyze original code without any rewrite rules (bypass all)
            analysis_source = self._split_save_source()
            bypass_rule = RuleState(rule_id=0, name="Bypass", description="", enabled=True)
            try:
                result = rewrite_and_analyze(analysis_source, [bypass_rule], self.split_points.copy(), self.parameter_bindings, self.shots, timeout_s=self.timeout_s, distributed_nodes=self.distributed_nodes)
                if result.parse_tree is not None:
                    result.ast_graph = build_ast_graph(result.parse_tree)
            except Exception:
                # Fall back to rewritten result if analysis fails
                result = self._latest_result
        
        self.ast_tree_view.load_tree(result.parse_tree)
        self._ast_program = result.parse_tree
        self._ast_source_editor = self.rewritten_view if use_rewritten else self.original_editor
        self._sync_ast_from_editor(self._ast_source_editor)
        circuit_issue = ""
        for issue in result.issues:
            if getattr(issue, "kind", "") != "error":
                continue
            message = str(getattr(issue, "message", "") or "")
            if "Runtime execution failed:" in message:
                circuit_issue = message.split("Runtime execution failed:", 1)[1].strip()
                break
            if "QASM parse failed:" in message:
                circuit_issue = message.split("QASM parse failed:", 1)[1].strip()
                break

        dag_graph = result.dag_graph or None
        interaction_graph = result.interaction_graph or None
        chunk_graph = result.chunk_graph or None
        chunk_flows = result.chunk_flows or []

        if hasattr(self.overall_dag_view.view, "set_circuit") and result.circuit is not None:
            try:
                self.overall_dag_view.view.set_circuit(result.circuit, self.font())
            except Exception as exc:
                message = f"Overall DAG unavailable: {exc}"
                self.overall_dag_view.set_graph(None, lambda node: str(node), empty_message=message)
        else:
            message = "No overall DAG available"
            if circuit_issue:
                message = f"Overall DAG unavailable: {circuit_issue}"
            self.overall_dag_view.set_graph(None, lambda node: str(node), empty_message=message)

        if hasattr(self.qubit_graph_view.view, "set_circuit") and result.circuit is not None:
            try:
                self.qubit_graph_view.view.set_circuit(result.circuit, self.font())
            except Exception as exc:
                message = f"Qubit interaction unavailable: {exc}"
                self.qubit_graph_view.set_graph(None, lambda node: str(node), empty_message=message)
        else:
            message = "No qubit interaction graph available"
            if circuit_issue:
                message = f"Qubit interaction unavailable: {circuit_issue}"
            self.qubit_graph_view.set_graph(None, lambda node: str(node), empty_message=message)

        if chunk_flows:
            self.chunk_graph_view.set_flows(chunk_flows, self.font())
        else:
            self.chunk_graph_view.set_graph(chunk_graph, lambda node: str(node), empty_message=result.suggestion_reason or "No chunk dependencies available")
        sorted_suggestions = sorted(result.suggested_split_points)
        suggestion_text = ", ".join(str(line) for line in sorted_suggestions) if sorted_suggestions else "none yet"
        self.suggestion_label.setText(f"Split suggestions: {suggestion_text}")

    def refresh(self) -> None:
        display_source = self.original_editor.toPlainText()
        self.current_source = display_source
        self.split_points = split_points_from_source(display_source)
        analysis_source = self._split_save_source(display_source)
        analysis_split_points = self.split_points.copy()

        active_rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.enabled) for rule in self.rules]
        needs_parameters = bool(scan_inputs(analysis_source)) and not self.parameter_bindings and not getattr(self, "_suppress_parameter_prompt", False)
        try:
            result = rewrite_and_analyze(analysis_source, active_rules, analysis_split_points, self.parameter_bindings, self.shots, timeout_s=self.timeout_s, execute_runtime=False, distributed_nodes=self.distributed_nodes)
            if result.parse_tree is not None:
                result.ast_graph = build_ast_graph(result.parse_tree)
            self._latest_result = result
            self.original_editor.setOriginalRuleMatches(original_line_rule_matches(display_source))
            self.original_editor.setRewriteSpans(result.spans)
            self.rewritten_view.set_rewrite_result(result.rewritten_source, result.spans)
            self._set_rewritten_tab_fallback_warning(result.fallback_events)
            self.original_editor.setDiagnosticLines({})
            pragma_lines = split_pragma_line_numbers(display_source)
            self.original_editor.setPragmaLines(pragma_lines)
            self.original_editor.setSplitSuggestions(set(result.suggested_split_points))
            self.original_editor.line_number_area.update()
            if bool(scan_inputs(analysis_source)) and not self.parameter_bindings and getattr(self, "_suppress_parameter_prompt", False):
                self._shutdown_runtime_executor()
                self.runtime_output.setPlainText("Saved split chunks. Parameter input is preserved for this session.")
            elif needs_parameters:
                self._shutdown_runtime_executor()
                self.runtime_output.setPlainText("Circuit preview ready. Enter parameter values to run the circuit.")
                if not self._parameter_prompt_pending and not self._parameter_prompt_open:
                    self._parameter_prompt_pending = True
                    QTimer.singleShot(0, self._prompt_for_parameters)
            else:
                if result.circuit is None:
                    self._shutdown_runtime_executor()
                    self.runtime_output.setPlainText(summary_text(result, self.shots))
                else:
                    self.runtime_output.setPlainText(
                        "Running simulation...\n"
                        f"{self._runtime_backend_fallback_line()}\n"
                        "Current AER backend: MPS"
                    )
                    self._start_runtime_run(result, preferred_backend="MPS", retry_attempted=False)
            self.circuit_view.show_circuit(result.circuit, result.split_qasm)
            self.refresh_graphs()
            self._update_runtime_menu_labels()
        except Exception as exc:
            self._shutdown_runtime_executor()
            self.runtime_output.setPlainText(f"Runtime failed: {exc}")

    def _set_rewritten_tab_fallback_warning(self, fallback_events: list[str]) -> None:
        tab_bar = self.code_tabs.tabBar()
        has_fallbacks = bool(fallback_events)
        tab_bar.setProperty("dqcRewriteWarn", has_fallbacks)
        tab_bar.style().unpolish(tab_bar)
        tab_bar.style().polish(tab_bar)

        if has_fallbacks:
            tab_bar.setTabTextColor(2, QColor("#b91c1c"))
            bullet_lines = "\n".join(f"- {entry}" for entry in fallback_events)
            tooltip = (
                "Rewritten view differs from parser/runtime input due to fallback handling:\n"
                f"{bullet_lines}"
            )
            self.code_tabs.setTabToolTip(2, tooltip)
        else:
            tab_bar.setTabTextColor(2, QColor("#0f172a"))
            self.code_tabs.setTabToolTip(2, "Rewritten source after applying active compatibility rules.")

    def _split_save_source(self, source: str | None = None) -> str:
        source = self.original_editor.toPlainText() if source is None else source
        return "\n".join(line for line in source.splitlines() if not line.strip().startswith("pragma dqc.v1.split"))

    def _set_original_editor_text_preserve_state(self, new_text: str) -> None:
        had_focus = self.original_editor.hasFocus()
        cursor = self.original_editor.textCursor()
        cursor_block = cursor.blockNumber()
        cursor_in_block = cursor.positionInBlock()
        scroll_value = self.original_editor.verticalScrollBar().value()
        horizontal_scroll = self.original_editor.horizontalScrollBar().value()

        self.original_editor.blockSignals(True)
        self.original_editor.setPlainText(new_text)
        self.original_editor.blockSignals(False)
        self.original_editor.update_line_number_area_width(self.original_editor.blockCount())
        self.original_editor.line_number_area.update()

        target_block = self.original_editor.document().findBlockByNumber(max(0, cursor_block))
        if target_block.isValid():
            target_pos = min(target_block.position() + cursor_in_block, target_block.position() + len(target_block.text()))
        else:
            target_pos = min(cursor.position(), max(0, self.original_editor.document().characterCount() - 1))
        restored = QTextCursor(self.original_editor.document())
        restored.setPosition(max(0, target_pos))
        self.original_editor.setTextCursor(restored)
        self.original_editor.verticalScrollBar().setValue(scroll_value)
        self.original_editor.horizontalScrollBar().setValue(horizontal_scroll)
        if had_focus:
            self.original_editor.setFocus()

    def _persist_split_artifacts(self) -> Path | None:
        if not self.split_points:
            return None
        raw_source = self._split_save_source()
        dqc_source, dqc_qasm = build_distributed_qasm(raw_source, self.split_points)
        target_dir = self.split_root / self.current_file.stem
        dqc_path = target_dir / f"{self.current_file.stem}.dqc"
        write_text(dqc_path, dqc_source)
        write_text(target_dir / f"{self.current_file.stem}.dqc.qasm", dqc_qasm)
        return dqc_path

    def save_split_chunks(self) -> None:
        if not self.split_points:
            return
        saved_dqc = self._persist_split_artifacts()
        if saved_dqc is None:
            return
        self.load_file(saved_dqc, preserve_parameter_bindings=True, prompt_for_parameters=False)
        QMessageBox.information(self, "Save split chunks", f"Saved split artifacts under {saved_dqc.parent}")

    def _update_runtime_menu_labels(self) -> None:
        if self._runtime_actions is None:
            return
        shots_action, timeout_action, nodes_action = self._runtime_actions
        shots_action.setText(f"Qiskit shots ({self.shots})")
        if self.timeout_s == 0:
            timeout_action.setText("Timeout (no limit)")
        else:
            timeout_action.setText(f"Timeout ({self.timeout_s} s)")
        nodes_action.setText(f"Distributed nodes/QPUs ({self.distributed_nodes})")

    def zoom_active(self, delta: int) -> None:
        widget = self.focusWidget()
        if hasattr(widget, "zoom"):
            widget.zoom(delta)
            return
        active_tab = self.code_tabs.currentWidget()
        if hasattr(active_tab, "zoom"):
            active_tab.zoom(delta)

    def zoom_reset(self) -> None:
        for widget in [self.original_editor, self.rewritten_view, self.circuit_view.view, self.overall_dag_view.view, self.qubit_graph_view.view, self.chunk_graph_view.view]:
            if hasattr(widget, "reset_zoom"):
                widget.reset_zoom()

    def _searchable_views(self) -> list[tuple[int, QWidget]]:
        return [(0, self.original_editor), (2, self.rewritten_view)]

    def _collect_matches(self, query: str, case_insensitive: bool = True) -> list[tuple[int, QWidget, QTextCursor]]:
        matches: list[tuple[int, QWidget, QTextCursor]] = []
        if not query:
            return matches
        needle = query.lower() if case_insensitive else query
        for tab_index, widget in self._searchable_views():
            text = widget.toPlainText()
            haystack = text.lower() if case_insensitive else text
            start = 0
            while True:
                match_start = haystack.find(needle, start)
                if match_start < 0:
                    break
                match_end = match_start + len(query)
                document = widget.document()
                cursor = QTextCursor(document)
                cursor.setPosition(match_start)
                cursor.setPosition(match_end, QTextCursor.MoveMode.KeepAnchor)
                matches.append((tab_index, widget, cursor))
                start = match_end if len(query) > 0 else match_start + 1
        matches.sort(key=lambda item: (item[0], item[2].selectionStart()))
        return matches

    def _select_match(self, widget: QWidget, cursor: QTextCursor) -> None:
        if widget is self.original_editor:
            self.code_tabs.setCurrentIndex(0)
            self.original_editor.setTextCursor(cursor)
            self.original_editor.ensureCursorVisible()
            return
        if widget is self.rewritten_view:
            self.code_tabs.setCurrentIndex(2)
            self.rewritten_view.setTextCursor(cursor)
            self.rewritten_view.ensureCursorVisible()

    def find_text(self, query: str, forward: bool = True, case_insensitive: bool = True) -> bool:
        query = query.strip()
        if not query:
            return False
        matches = self._collect_matches(query, case_insensitive=case_insensitive)
        if not matches:
            QMessageBox.information(self, "Find", f"No occurrence of '{query}' found in the original or rewritten code tabs.")
            return False

        if query != self._find_query or case_insensitive != self._find_case_insensitive:
            self._find_query = query
            self._find_case_insensitive = case_insensitive
            self._find_matches = matches
            self._find_index = -1

        if len(self._find_matches) != len(matches) or any(
            old[0] != new[0] or old[2].selectionStart() != new[2].selectionStart()
            for old, new in zip(self._find_matches, matches)
        ):
            self._find_matches = matches
            if self._find_index >= len(self._find_matches):
                self._find_index = -1

        next_index = 0 if forward else len(self._find_matches) - 1
        if self._find_index >= 0:
            next_index = (self._find_index + (1 if forward else -1)) % len(self._find_matches)

        self._find_index = next_index
        _, widget, cursor = self._find_matches[next_index]
        self._select_match(widget, cursor)
        return True

    def show_find_dialog(self) -> None:
        dialog = TextSearchDialog(self)
        self._find_query = ""
        self._find_case_insensitive = True
        self._find_matches = []
        self._find_index = -1
        dialog.findNextRequested.connect(lambda query, case_insensitive: self.find_text(query, forward=True, case_insensitive=case_insensitive))
        dialog.findPreviousRequested.connect(lambda query, case_insensitive: self.find_text(query, forward=False, case_insensitive=case_insensitive))
        dialog.edit.setText(self._find_query)
        dialog.edit.selectAll()
        dialog.edit.setFocus()
        dialog.exec()

    def change_shots(self) -> None:
        value, ok = QInputDialog.getInt(self, "Qiskit shots", "Shots:", self.shots, 1, 1_000_000, 1)
        if ok:
            self.shots = value
            self.refresh()

    def change_timeout(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Runtime timeout")
        layout = QVBoxLayout(dialog)
        spin = QSpinBox()
        spin.setRange(0, 3600)
        spin.setSingleStep(1)
        spin.setValue(self.timeout_s)
        layout.addWidget(QLabel("Timeout in seconds (0 = no limit):"))
        layout.addWidget(spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.timeout_s = spin.value()
            self._update_runtime_menu_labels()
            if self.timeout_s == 0:
                self.statusBar().showMessage("Runtime timeout disabled", 3000)
            else:
                self.statusBar().showMessage(f"Runtime timeout set to {self.timeout_s} seconds", 3000)

    def change_distributed_nodes(self) -> None:
        value, ok = QInputDialog.getInt(self, "Distributed nodes/QPUs", "Number of distributed QPUs:", self.distributed_nodes, 1, 8, 1)
        if not ok:
            return
        self.distributed_nodes = value
        self._update_runtime_menu_labels()
        self.statusBar().showMessage(f"Distributed nodes/QPUs set to {self.distributed_nodes}", 3000)
        self.refresh()

    def run_manual(self) -> None:
        analysis_source = self._split_save_source()
        if scan_inputs(analysis_source):
            self._prompt_for_parameters(force=True)
            return
        self.refresh()

    def _start_runtime_stopwatch(self) -> None:
        self._runtime_stopwatch_label.setVisible(True)
        self._runtime_stopwatch_label.setText("Running simulation... 00:00:00.000")

    def _stop_runtime_stopwatch(self) -> None:
        self._runtime_stopwatch_label.clear()
        self._runtime_stopwatch_label.setVisible(False)
        self._runtime_stopwatch_label.setStyleSheet("font-weight: 700; color: #1f6f2a; padding-left: 8px; padding-right: 8px;")

    def _update_runtime_stopwatch(self) -> None:
        if self._runtime_run_start_monotonic is None:
            return
        elapsed = time.perf_counter() - self._runtime_run_start_monotonic
        total_ms = max(0, int(round(elapsed * 1000.0)))
        hours, rem = divmod(total_ms, 3_600_000)
        minutes, rem = divmod(rem, 60_000)
        seconds, millis = divmod(rem, 1000)
        self._runtime_stopwatch_label.setText(f"Running simulation... {hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}")
        if self.timeout_s > 0 and elapsed >= self.timeout_s:
            self._runtime_stopwatch_label.setStyleSheet("font-weight: 700; color: #c41e3a; padding-left: 8px; padding-right: 8px;")
        else:
            self._runtime_stopwatch_label.setStyleSheet("font-weight: 700; color: #1f6f2a; padding-left: 8px; padding-right: 8px;")

    def _shutdown_runtime_executor(self) -> None:
        self._runtime_state_timer.stop()
        self._runtime_run_start_monotonic = None
        self._runtime_future = None
        self._runtime_future_token = None
        self._runtime_pending_result = None
        self._stop_runtime_stopwatch()
        executor = self._runtime_executor
        self._runtime_executor = None
        if executor is None:
            return
        try:
            processes = list(getattr(executor, "_processes", {}).values())
        except Exception:
            processes = []
        for process in processes:
            try:
                if process.is_alive():
                    process.terminate()
            except Exception:
                pass
        for process in processes:
            try:
                process.join(timeout=1)
            except Exception:
                pass
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    def _start_runtime_run(self, result, preferred_backend: str = "MPS", retry_attempted: bool = False) -> None:
        self._shutdown_runtime_executor()
        self._runtime_run_token += 1
        token = self._runtime_run_token
        self._runtime_requested_backend = preferred_backend
        self._runtime_retry_attempted = retry_attempted
        self._runtime_run_start_monotonic = time.perf_counter()
        self._start_runtime_stopwatch()
        self._runtime_state_timer.start()
        self._update_runtime_stopwatch()
        self._runtime_pending_result = result
        self._runtime_future_token = token
        self._runtime_executor = concurrent.futures.ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn"))
        self._runtime_future = self._runtime_executor.submit(
            run_runtime_counts,
            result.split_qasm,
            dict(self.parameter_bindings),
            self.shots,
            preferred_backend,
        )

    def _on_runtime_run_finished(self, token: int, counts: dict[str, int] | None, error: str | None, run_timestamp: datetime, runtime_backend: str = "", runtime_note: str = "", run_duration: float | None = None) -> None:
        if token != self._runtime_run_token:
            return
        result = self._runtime_pending_result
        self._runtime_state_timer.stop()
        if run_duration is None and self._runtime_run_start_monotonic is not None:
            run_duration = time.perf_counter() - self._runtime_run_start_monotonic
        self._runtime_run_start_monotonic = None
        self._stop_runtime_stopwatch()
        self._runtime_future = None
        self._runtime_future_token = None
        self._runtime_pending_result = None
        self._runtime_requested_backend = ""
        self._runtime_retry_attempted = False
        if result is None:
            return
        if run_duration is not None:
            result.duration_s = run_duration
        result.started_at_utc = run_timestamp.astimezone(timezone.utc)
        result.runtime_backend = runtime_backend
        result.runtime_note = runtime_note
        if error:
            self.runtime_output.setPlainText(f"{summary_text(result, self.shots)}\n\nRuntime failed: {error}")
            self._show_status_feedback("Simulation failed.")
            return
        result.counts = counts or {}
        details: list[str] = [summary_text(result, self.shots)]
        details.append(self._runtime_backend_fallback_line())
        details.append(f"Current AER backend: {self._normalize_runtime_backend_label(runtime_backend)}")
        runtime_text = "\n\n".join(details)
        runtime_text = runtime_text.replace(
            f"{self._runtime_backend_fallback_line()}\n\nCurrent AER backend:",
            f"{self._runtime_backend_fallback_line()}\nCurrent AER backend:",
        )
        self.runtime_output.setPlainText(runtime_text)
        self._show_status_feedback("Simulation complete.")

    def _refresh_runtime_run_state(self) -> None:
        if self._runtime_run_start_monotonic is None:
            return
        self._update_runtime_stopwatch()
        future = self._runtime_future
        if future is None:
            return
        if self.timeout_s > 0 and self._runtime_run_start_monotonic is not None:
            elapsed = time.perf_counter() - self._runtime_run_start_monotonic
            if elapsed >= self.timeout_s and not future.done():
                result = self._runtime_pending_result
                run_timestamp = datetime.now(timezone.utc)
                requested_backend = (self._runtime_requested_backend or "").strip().lower()
                self._shutdown_runtime_executor()
                if result is not None and requested_backend == "mps" and not self._runtime_retry_attempted:
                    self.runtime_output.setPlainText(
                        "Running simulation...\n"
                        f"{self._runtime_backend_fallback_line()}\n"
                        "Current AER backend: monolithic"
                    )
                    self._show_status_feedback("MPS timed out: retrying with monolithic backend.")
                    self._start_runtime_run(result, preferred_backend="monolithic", retry_attempted=True)
                    return
                if result is not None:
                    result.started_at_utc = run_timestamp.astimezone(timezone.utc)
                    result.duration_s = elapsed
                    self.runtime_output.setPlainText(f"{summary_text(result, self.shots)}\n\nRuntime failed: Runtime timed out after {self.timeout_s} seconds")
                    self._show_status_feedback("Simulation timed out.")
                return
        if not future.done():
            return
        token = self._runtime_future_token
        if token is None:
            return
        try:
            counts, error, run_timestamp, runtime_backend, runtime_note = future.result()
        except Exception as exc:
            counts = None
            error = str(exc)
            run_timestamp = datetime.now(timezone.utc)
            runtime_backend = ""
            runtime_note = ""
        self._on_runtime_run_finished(token, counts, error, run_timestamp, runtime_backend=runtime_backend, runtime_note=runtime_note)

    def closeEvent(self, event):  # noqa: N802
        self._shutdown_runtime_executor()
        super().closeEvent(event)

    def show_diagnostics(self) -> None:
        packages = self._all_bom_packages()
        dialog = DiagnosticsDialog(self._loading_dialog_html("Diagnostics", "⟳ Running diagnostics checks, version updates, and smoke test..."), self)

        def _task() -> dict:
            versions = package_versions(packages)
            updates = latest_versions_from_pypi(packages)
            smoke = smoke_test_hadamard(self.shots)
            return {"versions": versions, "updates": updates, "smoke": smoke}

        def _done(payload: dict) -> None:
            if not payload.get("ok"):
                dialog.update_report(self._error_dialog_html("Diagnostics", str(payload.get("error", "unknown error"))))
                return
            result = payload.get("result", {})
            versions = result.get("versions", {})
            updates = result.get("updates", {})
            smoke = result.get("smoke", {"duration_s": 0.0, "counts": {}})
            dialog.update_report(self._diagnostics_html(versions, updates, smoke))

        self._run_report_async(_task, _done)
        dialog.exec()


def launch_app() -> int:
    # Raise Qt's image read allocation limit so large rendered circuit images are accepted.
    limit_mb_text = os.environ.get("DQC_QT_IMAGE_ALLOC_MB", "1024").strip()
    try:
        QImageReader.setAllocationLimit(max(256, int(limit_mb_text)))
    except Exception:
        QImageReader.setAllocationLimit(1024)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Path(__file__).resolve().parents[1])
    window.showMaximized()
    return app.exec()