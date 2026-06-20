from __future__ import annotations

import importlib
from pathlib import Path
from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont
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
            self.original_editor.setSplitSuggestions(set(result.suggested_split_points))
            # Reconstruct source with pragmas: remove existing pragmas and inject based on split_points
            raw_source = self._split_save_source()  # Remove all pragmas
            display_source = self._reconstruct_source_with_pragmas(raw_source)  # Add pragmas at split_points
            pragma_lines = split_pragma_line_numbers(display_source)
            self.current_source = display_source  # Update current_source to reflect reconstructed version
            pragma_lines = split_pragma_line_numbers(display_source)
            self.current_source = display_source  # Update current_source to reflect reconstructed version
            display_source = self._reconstruct_source_with_pragmas(raw_source)  # Add pragmas at split_points
            pragma_lines = split_pragma_line_numbers(display_source)
            self.current_source = display_source  # Update current_source to reflect reconstructed version
    DEFAULT_RULES,
    RuleState,
    build_ast_graph,
    build_distributed_qasm,
    latest_versions_from_pypi,
    package_versions,
    normalize_dqc_clicked_split_line,
    read_text,
    split_pragma_line_numbers,
    rewrite_and_analyze,
    scan_inputs,
    smoke_test_hadamard,
    summary_text,
    write_text,
)
from .widgets import CircuitView, CodeEditor, DiagnosticsView, GraphTab, HtmlCodeView, ParseTreeView, RulePanel, QiskitDagTab, ChunkDagTab


class ParameterDialog(QDialog):
    def __init__(self, parameters: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Runtime parameters")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._edits: dict[str, QLineEdit] = {}
        for name in parameters:
            edit = QLineEdit("0")
            self._edits[name] = edit
            form.addRow(name, edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict[str, str]:
        return {name: edit.text().strip() or "0" for name, edit in self._edits.items()}


class DiagnosticsDialog(QDialog):
    def __init__(self, report: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(report)
        browser.setOpenExternalLinks(True)
        browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        QTimer.singleShot(0, self._center)

    def _center(self) -> None:
        target = self.parentWidget().screen() if self.parentWidget() and self.parentWidget().screen() else QApplication.primaryScreen()
        if target is None:
            return
        geometry = self.frameGeometry()
        geometry.moveCenter(target.availableGeometry().center())
        self.move(geometry.topLeft())


class TextSearchDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Search text:"))
        self.edit = QLineEdit()
        layout.addWidget(self.edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def query(self) -> str:
        return self.edit.text().strip()


class MainWindow(QMainWindow):
    def __init__(self, workspace_root: Path) -> None:
        super().__init__()
        self.workspace_root = workspace_root
        self.qasm_root = workspace_root / "qasm"
        self.split_root = workspace_root / "qasm.split"
        self.current_file = self.qasm_root / "bell_state.qasm"
        self.current_source = ""
        self.split_points: set[int] = set()
        self.parameter_bindings: dict[str, str] = {}
        self.shots = 1024
        self.timeout_s = 10
        # Initialize rules: bypass (rule 0) disabled by default, all others enabled
        self.rules = [
            RuleState(rule.rule_id, rule.name, rule.description, rule.rule_id != 0)
            for rule in DEFAULT_RULES
        ]
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh)
        self.resize(1600, 1000)
        self._apply_style()
        self._build_ui()
        self._build_menus()
        self._update_window_title()
        self.load_file(self.current_file)
        QTimer.singleShot(0, self._apply_initial_split_sizes)
        self.showMaximized()

    def _update_window_title(self) -> None:
        self.setWindowTitle(f"DQC Quantum Workbench - {self.current_file.resolve()}")

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f8fbff; }
            QTabWidget::pane { border: 1px solid rgba(96, 165, 250, 0.25); border-radius: 10px; background: white; }
            QTabBar::tab { background: linear-gradient(to bottom, #e8eef7, #dbeafe); color: #0f172a; padding: 8px 12px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: white; color: #1d4ed8; }
            QSplitter::handle { background: rgba(96, 165, 250, 0.35); }
            QPushButton { background: linear-gradient(to bottom, #eff6ff, #dbeafe); color: #0f172a; border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 6px; padding: 6px 10px; }
            QPushButton:hover { background: linear-gradient(to bottom, #dbeafe, #bfdbfe); }
            QLabel { color: #0f172a; }
            QMenuBar { background: #f8fbff; color: #0f172a; }
            QMenuBar::item:selected { background: #dbeafe; }
            QMenu { background: white; color: #0f172a; border: 1px solid rgba(96, 165, 250, 0.25); }
            QMenu::item:selected { background: #dbeafe; }
            QPlainTextEdit, QTextBrowser, QTreeWidget { background: white; color: #0f172a; border: 1px solid rgba(96, 165, 250, 0.18); border-radius: 10px; }
            """
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)
        top_split = QSplitter(Qt.Horizontal)
        top_split.setChildrenCollapsible(False)
        outer_split = QSplitter(Qt.Vertical)
        outer_split.setChildrenCollapsible(False)

        self.code_tabs = QTabWidget()
        self.original_editor = CodeEditor()
        self.original_editor.textChanged.connect(self._schedule_refresh)
        self.original_editor.splitPointRequested.connect(self.toggle_split_point)
        self.rewritten_view = HtmlCodeView()
        self.rule_panel = RulePanel(self.rules)
        self.rule_panel.ruleToggled.connect(self.on_rule_toggled)
        self.code_tabs.addTab(self.original_editor, "Original")
        self.code_tabs.addTab(self.rule_panel, "Compatibility Rules")
        self.code_tabs.addTab(self.rewritten_view, "Rewritten")

        code_shell = QWidget()
        code_layout = QVBoxLayout(code_shell)
        code_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestion_label = QLabel("Split suggestions: none yet")
        self.suggestion_label.setStyleSheet("color: #1d4ed8; font-weight: 600;")
        code_layout.addWidget(self._make_header("Code", [("Find", self.show_find_dialog), ("Zoom +", lambda: self.zoom_active(1)), ("Zoom -", lambda: self.zoom_active(-1)), ("Reset", self.zoom_reset)], [self.suggestion_label], accent="#3b82f6"))
        code_layout.addWidget(self.code_tabs)
        code_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(59,130,246,0.08), rgba(255,255,255,0.98)); border: 1px solid rgba(59,130,246,0.22); border-radius: 14px; }")

        runtime_shell = QWidget()
        runtime_layout = QVBoxLayout(runtime_shell)
        runtime_layout.setContentsMargins(0, 0, 0, 0)
        runtime_layout.addWidget(self._make_header("Runtime", [("Run now", self.run_manual), ("Shots", self.change_shots), ("Timeout", self.change_timeout)], accent="#10b981"))
        self.circuit_view = CircuitView()
        self.runtime_output = QPlainTextEdit()
        self.runtime_output.setReadOnly(True)
        self.runtime_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.runtime_output.setFont(QFont("DejaVu Sans Mono", 10))
        self.runtime_output.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        runtime_layout.addWidget(self.circuit_view, 4)
        runtime_layout.addWidget(self.runtime_output, 1)
        runtime_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(16,185,129,0.07), rgba(255,255,255,0.98)); border: 1px solid rgba(16,185,129,0.22); border-radius: 14px; }")

        top_split.addWidget(code_shell)
        top_split.addWidget(runtime_shell)

        graphs_shell = QWidget()
        graphs_layout = QVBoxLayout(graphs_shell)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_source_toggle = QCheckBox("Use rewritten code")
        self.graph_source_toggle.setChecked(True)
        self.graph_source_toggle.stateChanged.connect(self.refresh_graphs)
        graphs_layout.addWidget(self._make_header("Graphs", [], [self.graph_source_toggle], accent="#f59e0b"))
        self.graph_tabs = QTabWidget()
        self.ast_tree_view = ParseTreeView()
        self.overall_dag_view = QiskitDagTab("Overall DAG")
        self.qubit_graph_view = GraphTab("Qubit Interaction")
        self.chunk_graph_view = ChunkDagTab("Chunk Dependencies")
        self.graph_tabs.addTab(self.ast_tree_view, "AST parse-tree")
        self.graph_tabs.addTab(self.overall_dag_view, "Overall DAG")
        self.graph_tabs.addTab(self.qubit_graph_view, "Qubit Interaction")
        self.graph_tabs.addTab(self.chunk_graph_view, "Chunk Dependencies")
        graphs_layout.addWidget(self.graph_tabs)
        graphs_shell.setStyleSheet("QWidget { background: linear-gradient(to bottom, rgba(245,158,11,0.07), rgba(255,255,255,0.98)); border: 1px solid rgba(245,158,11,0.22); border-radius: 14px; }")

        outer_split.addWidget(top_split)
        outer_split.addWidget(graphs_shell)

        root.addWidget(outer_split)
        self._top_split = top_split
        self._outer_split = outer_split
        self._runtime_actions: tuple[QAction, QAction] | None = None

    def _apply_initial_split_sizes(self) -> None:
        width = max(1, self.width())
        height = max(1, self.height())
        self._top_split.setSizes([max(1, int(width * 0.2)), max(1, int(width * 0.8))])
        self._outer_split.setSizes([max(1, height // 2), max(1, height // 2)])

    def _make_header(self, title: str, left_actions: list[tuple[str, Callable[[], None]]], right_widgets: list[QWidget] | None = None, accent: str = "#3b82f6") -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {accent};")
        layout.addWidget(label)
        layout.addStretch(1)
        for text, handler in left_actions:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        for widget_item in right_widgets or []:
            layout.addWidget(widget_item)
        widget.setStyleSheet(f"QWidget {{ background: linear-gradient(to right, rgba(255,255,255,0.92), rgba(239,246,255,0.92)); border-bottom: 2px solid {accent}; border-top-left-radius: 10px; border-top-right-radius: 10px; }}")
        return widget

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
        self._populate_examples_menu(examples_menu, self.qasm_root)

        view_menu = self.menuBar().addMenu("View")
        for text, handler in [("Zoom in", lambda: self.zoom_active(1)), ("Zoom out", lambda: self.zoom_active(-1)), ("Zoom reset", self.zoom_reset), ("Find ...", self.show_find_dialog)]:
            action = QAction(text, self)
            action.triggered.connect(handler)
            view_menu.addAction(action)

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
        diagnostics_action = QAction("Diagnostics", self)
        diagnostics_action.triggered.connect(self.show_diagnostics)
        runtime_menu.addAction(diagnostics_action)
        self._runtime_actions = (shots_action, timeout_action)

        help_menu = self.menuBar().addMenu("Help")
        gpl_action = QAction("GPL3 Licence", self)
        gpl_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.gnu.org/licenses/gpl-3.0.en.html")))
        help_menu.addAction(gpl_action)
        bib_menu = QMenu("Bibliography", self)
        help_menu.addMenu(bib_menu)
        self._populate_bibliography_menu(bib_menu)

    def _populate_examples_menu(self, menu: QMenu, root: Path) -> None:
        menu.clear()
        if not root.exists():
            return
        for path in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if path.is_dir():
                sub = menu.addMenu(path.name)
                self._populate_examples_menu(sub, path)
            elif path.suffix.lower() in {".qasm", ".inc"}:
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

    def _schedule_refresh(self) -> None:
        self._refresh_timer.start(250)

    def load_file(self, path: Path) -> None:
        if not path.exists():
            QMessageBox.warning(self, "Missing file", f"Cannot find {path}")
            return
        self.current_file = path
        self._update_window_title()
        self.current_source = read_text(path)
        self.parameter_bindings = {}
        self.split_points = split_pragma_line_numbers(self.current_source)
        self.original_editor.blockSignals(True)
        self.original_editor.setPlainText(self.current_source)
        self.original_editor.blockSignals(False)
        self.original_editor.setRewriteSpans([])
        self.original_editor.setPragmaLines(self.split_points)
        self.rule_panel.set_states({rule.rule_id for rule in self.rules if rule.enabled}, self._rule_bypass_enabled())
        self.refresh()

    def open_file_dialog(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(self, "Load QASM3 file", str(self.workspace_root), "QASM files (*.qasm *.dqc *.inc *.txt);;All files (*.*)")
        if selected:
            self.load_file(Path(selected))

    def toggle_split_point(self, line_no: int) -> None:
        line_no = normalize_dqc_clicked_split_line(self.original_editor.toPlainText(), line_no)
        if line_no in self.split_points:
            self.split_points.remove(line_no)
        else:
            self.split_points.add(line_no)
        self.refresh()

    def _reconstruct_source_with_pragmas(self, raw_source: str) -> str:
        """Reconstruct source by injecting pragmas at split_point lines."""
        if not self.split_points:
            return raw_source
        
        # Build new source with pragmas injected
        lines = raw_source.splitlines()
        split_points_sorted = sorted(self.split_points)
        result_lines = []
        
        for line_no, line in enumerate(lines, start=1):
            result_lines.append(line)
            # Insert pragma after this line if it's a split point
            if line_no in split_points_sorted:
                result_lines.append("pragma dqc.v1.split")
        
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

    def refresh_graphs(self) -> None:
        if not hasattr(self, "_latest_result"):
            return
        result = self._latest_result
        if result.parse_tree is not None:
            self.ast_tree_view.load_tree(result.parse_tree)
        dag_graph = result.dag_graph or None
        interaction_graph = result.interaction_graph or None
        chunk_graph = result.chunk_graph or None
        # Prefer circuit-based DAG rendering when available
        if hasattr(self.overall_dag_view.view, "set_circuit") and result.circuit is not None:
            try:
                self.overall_dag_view.view.set_circuit(result.circuit, self.font())
            except Exception:
                self.overall_dag_view.set_graph(dag_graph, lambda node: dag_graph.nodes[node].get("label", str(node)) if dag_graph is not None else str(node), empty_message="No overall DAG available")
        else:
            self.overall_dag_view.set_graph(dag_graph, lambda node: dag_graph.nodes[node].get("label", str(node)) if dag_graph is not None else str(node), empty_message="No overall DAG available")
        self.qubit_graph_view.set_graph(interaction_graph, lambda node: str(node), empty_message="No qubit interaction graph available")
        self.chunk_graph_view.set_graph(chunk_graph, lambda node: str(node), empty_message=result.suggestion_reason or "No chunk dependencies available")
        suggestion_text = ", ".join(str(line) for line in result.suggested_split_points) if result.suggested_split_points else "none yet"
        self.suggestion_label.setText(f"Split suggestions: {suggestion_text}")

    def refresh(self) -> None:
        source = self.original_editor.toPlainText()
        self.current_source = source
        
        # When pragmas exist in the source, we need to adjust split_points for analysis
        # because split_points may contain pragma line numbers that need to be mapped
        analysis_source = source
        analysis_split_points = self.split_points.copy()
        
        if "pragma dqc.v1.split" in source:
            # Strip pragmas for analysis and remap split_points
            pragma_lines = set()
            stripped_lines = []
            line_mapping = {}  # maps stripped line number to original line number
            
            for orig_line_no, line in enumerate(source.splitlines(), start=1):
                if line.strip().startswith("pragma dqc.v1.split"):
                    pragma_lines.add(orig_line_no)
                else:
                    stripped_line_no = len(stripped_lines) + 1
                    line_mapping[stripped_line_no] = orig_line_no
                    stripped_lines.append(line)
            
            analysis_source = "\n".join(stripped_lines)
            
            # Remap split_points to stripped coordinate system
            remapped_split_points = set()
            for orig_point in self.split_points:
                if orig_point not in pragma_lines:
                    # Find which stripped line corresponds to this original line
                    for stripped_no, orig_no in line_mapping.items():
                        if orig_no == orig_point:
                            remapped_split_points.add(stripped_no)
                            break
                else:
                    # pragma line is a split point - remap to the line after it
                    # Find the stripped line number that comes after this pragma
                    for stripped_no, orig_no in line_mapping.items():
                        if orig_no > orig_point:
                            remapped_split_points.add(stripped_no)
                            break
            
            analysis_split_points = remapped_split_points
        
        active_rules = [RuleState(rule.rule_id, rule.name, rule.description, rule.enabled) for rule in self.rules]
        if scan_inputs(analysis_source) and not self.parameter_bindings:
            dialog = ParameterDialog(scan_inputs(analysis_source), self)
            if dialog.exec() == QDialog.Accepted:
                self.parameter_bindings = dialog.values()
        try:
            result = rewrite_and_analyze(analysis_source, active_rules, analysis_split_points, self.parameter_bindings, self.shots, timeout_s=self.timeout_s)
            if result.parse_tree is not None:
                result.ast_graph = build_ast_graph(result.parse_tree)
            self._latest_result = result
            self.original_editor.setRewriteSpans(result.spans)
            self.rewritten_view.set_rewrite_result(result.rewritten_source, result.spans)
            diagnostics = {span.line: QColor("#f59e0b") for span in result.spans}
            diagnostics.update({issue.line: QColor("#ef4444") for issue in result.issues})
            self.original_editor.setDiagnosticLines(diagnostics)
    def _split_save_source(self) -> str:
        source = self.original_editor.toPlainText()
        return "\n".join(line for line in source.splitlines() if not line.strip().startswith("pragma dqc.v1.split"))

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
        self.load_file(saved_dqc)
        QMessageBox.information(self, "Save split chunks", f"Saved split artifacts under {saved_dqc.parent}")

    def _update_runtime_menu_labels(self) -> None:
        if self._runtime_actions is None:
            return
        shots_action, timeout_action = self._runtime_actions
        shots_action.setText(f"Qiskit shots ({self.shots})")
        timeout_action.setText(f"Timeout ({self.timeout_s} s)")

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

    def show_find_dialog(self) -> None:
        dialog = TextSearchDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        query = dialog.query()
        if not query:
            return
        if self.original_editor.find(query):
            self.code_tabs.setCurrentIndex(0)
            self.original_editor.setFocus()
            return
        if self.rewritten_view.find(query):
            self.code_tabs.setCurrentIndex(2)
            self.rewritten_view.setFocus()
            return
        QMessageBox.information(self, "Find", f"No occurrence of '{query}' found in the original or rewritten code tabs.")

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
        spin.setRange(1, 3600)
        spin.setSingleStep(1)
        spin.setValue(self.timeout_s)
        layout.addWidget(QLabel("Timeout in seconds:"))
        layout.addWidget(spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.timeout_s = spin.value()
            self._update_runtime_menu_labels()

    def run_manual(self) -> None:
        self.refresh()

    def show_diagnostics(self) -> None:
        versions = package_versions()
        updates = latest_versions_from_pypi(versions.keys())
        smoke = smoke_test_hadamard(self.shots)
        lines = ["<h2 style='margin-top:0'>Diagnostics</h2>", "<p>Installed packages and update status:</p>", "<ul>"]
        for name, version in versions.items():
            latest = updates.get(name, "unavailable")
            if latest in {"unavailable", version}:
                status = "up-to-date"
            else:
                status = f"out-of-date: latest is <a href='https://pypi.org/project/{name}/{latest}/'>{latest}</a>"
            lines.append(f"<li><b>{name}</b>: {version} ({status})</li>")
        lines.append("</ul>")
        matplotlib_ok = importlib.util.find_spec("matplotlib") is not None
        pylatexenc_ok = importlib.util.find_spec("pylatexenc") is not None
        lines.append("<p><b>Import health:</b></p>")
        lines.append("<ul>")
        lines.append(f"<li>matplotlib import: {'ok' if matplotlib_ok else 'missing'}</li>")
        lines.append(f"<li>pylatexenc import: {'ok' if pylatexenc_ok else 'missing'}</li>")
        lines.append("</ul>")
        lines.append(f"<p>Smoke test (shots={self.shots}): duration {smoke['duration_s']:.3f}s, counts {smoke['counts']}</p>")
        DiagnosticsDialog("".join(lines), self).exec()


def launch_app() -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Path(__file__).resolve().parents[1])
    window.showMaximized()
    return app.exec()