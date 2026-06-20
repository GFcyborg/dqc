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
