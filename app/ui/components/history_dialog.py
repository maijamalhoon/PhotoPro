"""
PhotoPro Print History Dialog
Displays past print sessions stored in the local SQLite database.
"""
from app.database.db import DatabaseManager

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
        QTableWidgetItem, QHeaderView, QPushButton, QLabel
    )
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QDialog: pass

class HistoryDialog(QDialog):
    """Modal dialog displaying recent print jobs."""

    def __init__(self, db: DatabaseManager, parent=None):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("PhotoPro - Print History")
        self.resize(650, 400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Recent Print and Export Jobs")
        title.setStyleSheet("font-weight: 600; font-size: 15px; color: #18181B; margin-bottom: 8px;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Photo Name", "Paper", "Size", "Copies", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self._load_data()

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

    def _load_data(self):
        records = self.db.get_print_history(limit=100)
        self.table.setRowCount(len(records))

        for row, rec in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get("photo_name", "Untitled")))
            self.table.setItem(row, 2, QTableWidgetItem(rec.get("paper_size", "")))
            self.table.setItem(row, 3, QTableWidgetItem(rec.get("photo_size", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(rec.get("copies", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(rec.get("status", "completed")))
