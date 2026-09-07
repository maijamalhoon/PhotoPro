"""
PhotoPro Settings Configuration Dialog
Allows photo shop operators to configure hardware acceleration, defaults, and enhancement strengths.
"""
from typing import Optional
from app.config.settings import AppSettings
from app.database.db import DatabaseManager

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QSlider, QSpinBox, QCheckBox, QPushButton, QGroupBox, QFormLayout
    )
    from PySide6.QtCore import Qt
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QDialog: pass

class SettingsDialog(QDialog):
    """Modal dialog for editing application preferences."""

    def __init__(self, db: DatabaseManager, current_settings: AppSettings, parent=None):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__(parent)
        self.db = db
        self.settings = current_settings
        self.setWindowTitle("PhotoPro - Application Settings")
        self.setFixedWidth(460)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 1. Defaults Group
        defaults_box = QGroupBox("Print & Format Defaults")
        form1 = QFormLayout(defaults_box)

        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["4R", "A4"])
        self.paper_combo.setCurrentText(self.settings.default_paper)
        form1.addRow("Default Paper Size:", self.paper_combo)

        self.size_combo = QComboBox()
        self.size_combo.addItem("Passport Size (35×45 mm)", "passport")
        self.size_combo.addItem("Smaller Size (30×40 mm)", "smaller")
        idx = 0 if self.settings.default_photo_size == "passport" else 1
        self.size_combo.setCurrentIndex(idx)
        form1.addRow("Default Photo Size:", self.size_combo)

        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["white", "blue", "grey", "original"])
        self.bg_combo.setCurrentText(self.settings.default_background)
        form1.addRow("Default Background:", self.bg_combo)

        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 60)
        self.copies_spin.setValue(self.settings.default_copies)
        form1.addRow("Default Copies:", self.copies_spin)

        layout.addWidget(defaults_box)

        # 2. Enhancement & AI Settings
        ai_box = QGroupBox("Automated Enhancement & Retouching")
        form2 = QFormLayout(ai_box)

        self.auto_retouch_cb = QCheckBox("Enable Conservative Blemish & Pimple Cleanup")
        self.auto_retouch_cb.setChecked(self.settings.auto_skin_retouch)
        form2.addRow(self.auto_retouch_cb)

        self.retouch_slider = QSlider(Qt.Orientation.Horizontal)
        self.retouch_slider.setRange(10, 90)
        self.retouch_slider.setValue(self.settings.retouch_strength)
        self.retouch_label = QLabel(f"{self.settings.retouch_strength}%")
        self.retouch_slider.valueChanged.connect(lambda v: self.retouch_label.setText(f"{v}%"))

        slider_row = QHBoxLayout()
        slider_row.addWidget(self.retouch_slider)
        slider_row.addWidget(self.retouch_label)
        form2.addRow("Retouch Strength:", slider_row)

        self.face_bright_cb = QCheckBox("Adaptive Face Brightness Lift")
        self.face_bright_cb.setChecked(self.settings.face_brightness_lift)
        form2.addRow(self.face_bright_cb)

        self.color_grade_cb = QCheckBox("Natural Portrait Color Grading & Contrast")
        self.color_grade_cb.setChecked(self.settings.color_grading)
        form2.addRow(self.color_grade_cb)

        self.sharpen_cb = QCheckBox("Clarity & Unsharp Mask Detail Enhancement")
        self.sharpen_cb.setChecked(self.settings.unsharp_mask)
        form2.addRow(self.sharpen_cb)

        layout.addWidget(ai_box)

        # 3. Hardware & Output Quality
        perf_box = QGroupBox("Performance & Export")
        form3 = QFormLayout(perf_box)

        self.hw_combo = QComboBox()
        self.hw_combo.addItem("Automatic (Detect DirectML / CUDA / CPU)", "auto")
        self.hw_combo.addItem("CPU Fallback (Standard Office PC)", "cpu")
        self.hw_combo.addItem("DirectML (Windows GPU Acceleration)", "directml")
        self.hw_combo.addItem("CUDA (NVIDIA High-Performance)", "cuda")
        for i in range(self.hw_combo.count()):
            if self.hw_combo.itemData(i) == self.settings.hardware_acceleration:
                self.hw_combo.setCurrentIndex(i)
                break
        form3.addRow("Hardware Mode:", self.hw_combo)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(75, 100)
        self.quality_spin.setValue(self.settings.export_quality)
        form3.addRow("JPEG Export Quality (%):", self.quality_spin)

        layout.addWidget(perf_box)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setProperty("class", "primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def _save(self):
        if not HAVE_QT: return
        self.settings.default_paper = self.paper_combo.currentText()
        self.settings.default_photo_size = self.size_combo.currentData()
        self.settings.default_background = self.bg_combo.currentText()
        self.settings.default_copies = self.copies_spin.value()
        self.settings.auto_skin_retouch = self.auto_retouch_cb.isChecked()
        self.settings.retouch_strength = self.retouch_slider.value()
        self.settings.face_brightness_lift = self.face_bright_cb.isChecked()
        self.settings.color_grading = self.color_grade_cb.isChecked()
        self.settings.unsharp_mask = self.sharpen_cb.isChecked()
        self.settings.hardware_acceleration = self.hw_combo.currentData()
        self.settings.export_quality = self.quality_spin.value()

        self.db.save_settings(self.settings)
        self.accept()
