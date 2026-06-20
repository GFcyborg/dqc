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
from .pipeline import (
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
        shots_action.setText(f"Shots: {self.shots}")
        timeout_action.setText(f"Timeout: {self.timeout_s}s")

    def _update_window_title(self) -> None:
        if self.current_file.is_file():
            title = f"DQC Split - {self.current_file.relative_to(self.workspace_root)}"
        else:
            title = "DQC Split"
        self.setWindowTitle(title)

    def _get_latest_version(self) -> None:
        versions = latest_versions_from_pypi()
        this_version = package_versions()["qiskit"]
        if versions and versions[0] > this_version:
            QMessageBox.information(self, "Updates Available", f"Qiskit {versions[0]} is available (current: {this_version})")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow(Path(__file__).resolve().parents[1])
    window.showMaximized()
    return app.exec()
