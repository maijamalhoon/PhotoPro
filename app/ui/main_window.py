"""
PhotoPro Main Desktop Application Window
Integrates sidebar, crop controls, background selector, before/after view,
300 DPI sheet layout, native Windows printing, and batch processing.
"""
import os
import logging
from typing import Optional, List
import numpy as np

from app.config.constants import (
    DPI, PAPERS, PHOTO_SIZES, PRESET_COLORS, DEFAULT_MODEL_PATH
)
from app.config.settings import AppSettings
from app.database.db import DatabaseManager
from app.core.pipeline import PhotoProPipeline, PipelineResult
from app.core.batch_processor import BatchProcessor, BatchJob
from app.export.exporter import ImageExporter
from app.printing.printer_service import PrinterService
from app.ui.styles import WINDOWS_STYLE
from app.ui.components.before_after_view import BeforeAfterView
from app.ui.components.photo_canvas import PhotoCanvas
from app.ui.components.sheet_preview import SheetPreview
from app.ui.components.settings_dialog import SettingsDialog
from app.ui.components.history_dialog import HistoryDialog

logger = logging.getLogger(__name__)

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QPushButton, QLabel, QFileDialog, QMessageBox, QTabWidget,
        QSlider, QSpinBox, QColorDialog, QProgressBar, QFrame,
        QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QIcon
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QMainWindow: pass

class MainWindow(QMainWindow):
    """Main application window for PhotoPro Windows Desktop."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__()

        self.setWindowTitle("PhotoPro - Professional Passport Photo Studio")
        self.resize(1260, 840)
        self.setStyleSheet(WINDOWS_STYLE)

        # Core Engines
        self.db = DatabaseManager()
        self.settings = self.db.load_settings()
        self.pipeline = PhotoProPipeline(model_path=model_path)
        self.batch_processor = BatchProcessor(self.pipeline)

        # State Variables
        self.current_image_path: Optional[str] = None
        self.current_image_rgb: Optional[np.ndarray] = None
        self.current_result: Optional[PipelineResult] = None
        self.current_paper: str = self.settings.default_paper
        self.current_size: str = self.settings.default_photo_size
        self.current_bg_mode: str = self.settings.default_background
        self.current_custom_color: tuple = (31, 111, 178)
        self.current_copies: int = self.settings.default_copies

        # Fine-tune overrides
        self.manual_brightness: int = 0
        self.manual_contrast: int = 0
        self.manual_saturation: int = 0

        self._init_ui()
        self._setup_batch_callbacks()

    def _init_ui(self):
        root_widget = QWidget(self)
        self.setCentralWidget(root_widget)

        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Main Content Split (Controls on left, Viewports on right)
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # Left Control Column (Scrollable)
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFixedWidth(380)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_panel = self._build_controls_panel()
        controls_scroll.setWidget(controls_panel)
        content_layout.addWidget(controls_scroll)

        # Right Stage Column (Tabs: Before/After, Sheet Preview, Batch Queue)
        stage_panel = self._build_stage_panel()
        content_layout.addWidget(stage_panel, stretch=1)

        root_layout.addWidget(content_area, stretch=1)

        # Bottom Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready. Select or drag a photo to begin.")

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("sidebarFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(6)

        # Logo / Title
        brand_label = QLabel("PhotoPro")
        brand_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #2563EB; margin-bottom: 2px;")
        sub_label = QLabel("Photo Shop Suite")
        sub_label.setStyleSheet("font-size: 11px; color: #71717A; margin-bottom: 18px;")
        layout.addWidget(brand_label)
        layout.addWidget(sub_label)

        # Navigation Buttons
        btn_new = QPushButton("New Photo")
        btn_new.setProperty("class", "navBtn active")
        btn_new.clicked.connect(self._open_single_file_dialog)
        layout.addWidget(btn_new)

        btn_batch = QPushButton("Batch Photos")
        btn_batch.setProperty("class", "navBtn")
        btn_batch.clicked.connect(self._open_batch_files_dialog)
        layout.addWidget(btn_batch)

        btn_history = QPushButton("Print History")
        btn_history.setProperty("class", "navBtn")
        btn_history.clicked.connect(self._show_history)
        layout.addWidget(btn_history)

        btn_settings = QPushButton("Settings")
        btn_settings.setProperty("class", "navBtn")
        btn_settings.clicked.connect(self._show_settings)
        layout.addWidget(btn_settings)

        layout.addStretch()

        # Offline Ready Badge
        badge = QLabel("OFFLINE ENGINE READY\n300 DPI Calibrated")
        badge.setStyleSheet(
            "background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; "
            "border-radius: 6px; padding: 6px; font-size: 10px; font-weight: 600; text-align: center;"
        )
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(badge)

        return frame

    def _build_controls_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Step: Photo Import Box
        import_card = QFrame()
        import_card.setProperty("class", "panelCard")
        import_layout = QVBoxLayout(import_card)

        head1 = QLabel("1. SELECT PHOTO")
        head1.setProperty("class", "sectionHeader")
        import_layout.addWidget(head1)

        self.btn_select_file = QPushButton("Open Customer Photo…")
        self.btn_select_file.setProperty("class", "primaryBtn")
        self.btn_select_file.clicked.connect(self._open_single_file_dialog)
        import_layout.addWidget(self.btn_select_file)

        self.lbl_filename = QLabel("No photo loaded")
        self.lbl_filename.setStyleSheet("color: #71717A; font-size: 11px;")
        import_layout.addWidget(self.lbl_filename)

        layout.addWidget(import_card)

        # 2. Step: Photo Size (Passport 35x45 vs Smaller 30x40)
        size_card = QFrame()
        size_card.setProperty("class", "panelCard")
        size_layout = QVBoxLayout(size_card)

        head2 = QLabel("2. PASSPORT PHOTO FORMAT")
        head2.setProperty("class", "sectionHeader")
        size_layout.addWidget(head2)

        size_btn_row = QHBoxLayout()
        self.btn_size_passport = QPushButton("Passport · 35×45 mm")
        self.btn_size_passport.setProperty("class", "chipBtn")
        self.btn_size_passport.setCheckable(True)
        self.btn_size_passport.setChecked(self.current_size == "passport")
        self.btn_size_passport.clicked.connect(lambda: self._set_photo_size("passport"))
        size_btn_row.addWidget(self.btn_size_passport)

        self.btn_size_smaller = QPushButton("Small · 30×40 mm")
        self.btn_size_smaller.setProperty("class", "chipBtn")
        self.btn_size_smaller.setCheckable(True)
        self.btn_size_smaller.setChecked(self.current_size == "smaller")
        self.btn_size_smaller.clicked.connect(lambda: self._set_photo_size("smaller"))
        size_btn_row.addWidget(self.btn_size_smaller)

        size_layout.addLayout(size_btn_row)
        layout.addWidget(size_card)

        # 3. Step: Background Color
        bg_card = QFrame()
        bg_card.setProperty("class", "panelCard")
        bg_layout = QVBoxLayout(bg_card)

        head3 = QLabel("3. BACKGROUND REPLACEMENT")
        head3.setProperty("class", "sectionHeader")
        bg_layout.addWidget(head3)

        bg_row = QHBoxLayout()
        self.bg_btns = {}
        for key in ["white", "blue", "grey", "original"]:
            btn = QPushButton(key.capitalize())
            btn.setProperty("class", "chipBtn")
            btn.setCheckable(True)
            btn.setChecked(self.current_bg_mode == key)
            btn.clicked.connect(lambda checked, k=key: self._set_bg_mode(k))
            bg_row.addWidget(btn)
            self.bg_btns[key] = btn

        self.btn_custom_color = QPushButton("Custom…")
        self.btn_custom_color.setProperty("class", "chipBtn")
        self.btn_custom_color.setCheckable(True)
        self.btn_custom_color.clicked.connect(self._pick_custom_color)
        bg_row.addWidget(self.btn_custom_color)
        self.bg_btns["custom"] = self.btn_custom_color

        bg_layout.addLayout(bg_row)
        layout.addWidget(bg_card)

        # 4. Step: Paper Size (4R vs A4) & Number of Copies
        sheet_card = QFrame()
        sheet_card.setProperty("class", "panelCard")
        sheet_layout = QVBoxLayout(sheet_card)

        head4 = QLabel("4. SHEET & PRINT COPIES")
        head4.setProperty("class", "sectionHeader")
        sheet_layout.addWidget(head4)

        paper_row = QHBoxLayout()
        self.btn_paper_4r = QPushButton("4R (6×4 in)")
        self.btn_paper_4r.setProperty("class", "chipBtn")
        self.btn_paper_4r.setCheckable(True)
        self.btn_paper_4r.setChecked(self.current_paper == "4R")
        self.btn_paper_4r.clicked.connect(lambda: self._set_paper("4R"))
        paper_row.addWidget(self.btn_paper_4r)

        self.btn_paper_a4 = QPushButton("A4 (210×297 mm)")
        self.btn_paper_a4.setProperty("class", "chipBtn")
        self.btn_paper_a4.setCheckable(True)
        self.btn_paper_a4.setChecked(self.current_paper == "A4")
        self.btn_paper_a4.clicked.connect(lambda: self._set_paper("A4"))
        paper_row.addWidget(self.btn_paper_a4)
        sheet_layout.addLayout(paper_row)

        copies_row = QHBoxLayout()
        copies_row.addWidget(QLabel("Quantity:"))
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 60)
        self.copies_spin.setValue(self.current_copies)
        self.copies_spin.valueChanged.connect(self._on_copies_changed)
        copies_row.addWidget(self.copies_spin)

        btn_max_copies = QPushButton("Fill Max")
        btn_max_copies.clicked.connect(self._fill_max_copies)
        copies_row.addWidget(btn_max_copies)
        sheet_layout.addLayout(copies_row)

        layout.addWidget(sheet_card)

        # 5. Step: Manual Fine-Tune Overrides (Collapsible)
        tune_card = QFrame()
        tune_card.setProperty("class", "panelCard")
        tune_layout = QVBoxLayout(tune_card)

        head5 = QLabel("5. MANUAL FINE-TUNING")
        head5.setProperty("class", "sectionHeader")
        tune_layout.addWidget(head5)

        # Brightness
        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("Brightness:"))
        self.slider_bright = QSlider(Qt.Orientation.Horizontal)
        self.slider_bright.setRange(-40, 40)
        self.slider_bright.setValue(0)
        self.slider_bright.valueChanged.connect(self._on_fine_tune_changed)
        b_row.addWidget(self.slider_bright)
        tune_layout.addLayout(b_row)

        # Contrast
        c_row = QHBoxLayout()
        c_row.addWidget(QLabel("Contrast:"))
        self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
        self.slider_contrast.setRange(-40, 40)
        self.slider_contrast.setValue(0)
        self.slider_contrast.valueChanged.connect(self._on_fine_tune_changed)
        c_row.addWidget(self.slider_contrast)
        tune_layout.addLayout(c_row)

        # Reset button
        btn_reset_tune = QPushButton("Reset Adjustments")
        btn_reset_tune.clicked.connect(self._reset_fine_tune)
        tune_layout.addWidget(btn_reset_tune)

        layout.addWidget(tune_card)
        layout.addStretch()

        return panel

    def _build_stage_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Top Tabs (Single Before/After vs Full 300 DPI Sheet vs Batch Queue)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #E4E4E7;
                color: #52525B;
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #2563EB;
            }
        """)

        # Tab 1: Single View & Before/After Comparison
        tab_single = QWidget()
        tab_single_layout = QVBoxLayout(tab_single)
        tab_single_layout.setContentsMargins(12, 12, 12, 12)

        self.before_after_view = BeforeAfterView()
        tab_single_layout.addWidget(self.before_after_view, stretch=1)

        toggle_row = QHBoxLayout()
        btn_toggle_mode = QPushButton("Toggle Split / Side View")
        btn_toggle_mode.clicked.connect(self.before_after_view.toggle_original)
        toggle_row.addWidget(btn_toggle_mode)
        toggle_row.addStretch()
        tab_single_layout.addLayout(toggle_row)

        self.tabs.addTab(tab_single, "Portrait Enhancement (Before / After)")

        # Tab 2: 300 DPI Print Sheet
        tab_sheet = QWidget()
        tab_sheet_layout = QVBoxLayout(tab_sheet)
        tab_sheet_layout.setContentsMargins(12, 12, 12, 12)

        self.sheet_preview = SheetPreview()
        tab_sheet_layout.addWidget(self.sheet_preview, stretch=1)

        self.tabs.addTab(tab_sheet, "Print Sheet Preview (4R / A4)")

        # Tab 3: Batch Queue
        tab_batch = QWidget()
        tab_batch_layout = QVBoxLayout(tab_batch)
        tab_batch_layout.setContentsMargins(12, 12, 12, 12)

        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(4)
        self.batch_table.setHorizontalHeaderLabels(["Photo File", "Status", "Progress", "Result"])
        self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tab_batch_layout.addWidget(self.batch_table, stretch=1)

        batch_actions = QHBoxLayout()
        self.btn_run_batch = QPushButton("Start Batch Processing")
        self.btn_run_batch.setProperty("class", "primaryBtn")
        self.btn_run_batch.clicked.connect(self._run_batch)
        batch_actions.addWidget(self.btn_run_batch)

        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 100)
        self.batch_progress.setValue(0)
        batch_actions.addWidget(self.batch_progress)

        tab_batch_layout.addLayout(batch_actions)
        self.tabs.addTab(tab_batch, "Batch Processing Queue")

        layout.addWidget(self.tabs, stretch=1)

        # Bottom Action Bar
        action_card = QFrame()
        action_card.setProperty("class", "panelCard")
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(10, 10, 10, 10)

        # Export Buttons
        self.btn_export_jpg = QPushButton("Export JPG (300 DPI)")
        self.btn_export_jpg.clicked.connect(self._export_jpg)
        action_layout.addWidget(self.btn_export_jpg)

        self.btn_export_png = QPushButton("Export PNG")
        self.btn_export_png.clicked.connect(self._export_png)
        action_layout.addWidget(self.btn_export_png)

        self.btn_export_pdf = QPushButton("Export PDF")
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        action_layout.addWidget(self.btn_export_pdf)

        action_layout.addStretch()

        # Master Print Action
        self.btn_print = QPushButton("Print Sheet…")
        self.btn_print.setProperty("class", "primaryBtn")
        self.btn_print.clicked.connect(self._print_sheet)
        action_layout.addWidget(self.btn_print)

        layout.addWidget(action_card)
        return panel

    # --- Event Handlers & Core Processing ---
    def _open_single_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Customer Photo", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if file_path:
            self.load_photo(file_path)

    def load_photo(self, file_path: str):
        try:
            self.current_image_path = file_path
            self.lbl_filename.setText(os.path.basename(file_path))
            self.current_image_rgb = PhotoProPipeline.load_image_rgb(file_path)
            self._process_and_update()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Image", f"Could not load image:\n{e}")

    def _process_and_update(self):
        if self.current_image_rgb is None:
            return

        self.status_bar.showMessage("Processing photo (face detection, background removal, 300 DPI layout)…")

        try:
            self.current_result = self.pipeline.process_photo(
                image_rgb=self.current_image_rgb,
                settings=self.settings,
                photo_size_key=self.current_size,
                bg_mode=self.current_bg_mode,
                custom_color=self.current_custom_color,
                manual_brightness=self.manual_brightness,
                manual_contrast=self.manual_contrast,
                manual_saturation=self.manual_saturation,
                paper_key=self.current_paper,
                copies=self.current_copies
            )

            # Update Before / After comparison
            self.before_after_view.set_images(
                self.current_result.original_rgb,
                self.current_result.single_photo_rgb
            )

            # Update Sheet Preview
            if self.current_result.sheet_rgb is not None:
                self.sheet_preview.set_sheet(self.current_result.sheet_rgb)

            face_msg = "Face detected" if self.current_result.landmarks else "Framed"
            p_format = PHOTO_SIZES.get(self.current_size, PHOTO_SIZES["passport"])
            msg = (
                f"300 DPI Ready · {face_msg} · "
                f"{p_format.name} · {self.current_paper} ({self.current_copies} copies) · "
                f"Processed in {self.current_result.processing_time_ms:.1f}ms"
            )
            self.status_bar.showMessage(msg)

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self.status_bar.showMessage(f"Processing error: {e}")

    def _set_photo_size(self, size_key: str):
        self.current_size = size_key
        self.btn_size_passport.setChecked(size_key == "passport")
        self.btn_size_smaller.setChecked(size_key == "smaller")
        self._process_and_update()

    def _set_bg_mode(self, mode: str):
        self.current_bg_mode = mode
        for k, btn in self.bg_btns.items():
            btn.setChecked(k == mode)
        self._process_and_update()

    def _pick_custom_color(self):
        color = QColorDialog.getColor(QColor(31, 111, 178), self, "Select Studio Background Color")
        if color.isValid():
            self.current_custom_color = (color.red(), color.green(), color.blue())
            self._set_bg_mode("custom")

    def _set_paper(self, paper_key: str):
        self.current_paper = paper_key
        self.btn_paper_4r.setChecked(paper_key == "4R")
        self.btn_paper_a4.setChecked(paper_key == "A4")
        self._process_and_update()

    def _on_copies_changed(self, val: int):
        self.current_copies = val
        self._process_and_update()

    def _fill_max_copies(self):
        max_cap = self.pipeline.sheet_generator.calculate_max_capacity(
            self.current_paper, self.current_size
        )
        self.copies_spin.setValue(max_cap)

    def _on_fine_tune_changed(self):
        self.manual_brightness = self.slider_bright.value()
        self.manual_contrast = self.slider_contrast.value()
        self._process_and_update()

    def _reset_fine_tune(self):
        self.slider_bright.setValue(0)
        self.slider_contrast.setValue(0)
        self.manual_brightness = 0
        self.manual_contrast = 0
        self._process_and_update()

    # --- Export Actions ---
    def _export_jpg(self):
        if not self.current_result or self.current_result.sheet_rgb is None:
            QMessageBox.information(self, "No Photo", "Please load and process a photo first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export 300 DPI Sheet JPG", "PhotoPro-Sheet.jpg", "JPEG (*.jpg)")
        if path:
            ImageExporter.export_jpg(self.current_result.sheet_rgb, path, quality=self.settings.export_quality)
            self.db.log_print_job(
                photo_name=os.path.basename(self.current_image_path or "Export"),
                paper_size=self.current_paper,
                photo_size=self.current_size,
                copies=self.current_copies,
                status="exported_jpg"
            )
            QMessageBox.information(self, "Exported", f"Successfully saved 300 DPI JPG to:\n{path}")

    def _export_png(self):
        if not self.current_result or self.current_result.sheet_rgb is None:
            QMessageBox.information(self, "No Photo", "Please load and process a photo first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Lossless PNG", "PhotoPro-Sheet.png", "PNG (*.png)")
        if path:
            ImageExporter.export_png(self.current_result.sheet_rgb, path)
            QMessageBox.information(self, "Exported", f"Successfully saved lossless PNG to:\n{path}")

    def _export_pdf(self):
        if not self.current_result or self.current_result.sheet_rgb is None:
            QMessageBox.information(self, "No Photo", "Please load and process a photo first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Print-Ready PDF", "PhotoPro-Sheet.pdf", "PDF (*.pdf)")
        if path:
            ImageExporter.export_pdf(self.current_result.sheet_rgb, path, paper_key=self.current_paper)
            self.db.log_print_job(
                photo_name=os.path.basename(self.current_image_path or "Export"),
                paper_size=self.current_paper,
                photo_size=self.current_size,
                copies=self.current_copies,
                status="exported_pdf"
            )
            QMessageBox.information(self, "Exported", f"Successfully saved calibrated PDF to:\n{path}")

    def _print_sheet(self):
        if not self.current_result or self.current_result.sheet_rgb is None:
            QMessageBox.information(self, "No Sheet", "Please load and process a photo first.")
            return
        success = PrinterService.print_sheet(
            self.current_result.sheet_rgb,
            paper_key=self.current_paper,
            parent_widget=self
        )
        if success:
            self.db.log_print_job(
                photo_name=os.path.basename(self.current_image_path or "Print"),
                paper_size=self.current_paper,
                photo_size=self.current_size,
                copies=self.current_copies,
                status="printed"
            )
            QMessageBox.information(self, "Printed", "Job successfully submitted to printer at 300 DPI.")

    # --- Batch Operations ---
    def _open_batch_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Multiple Photos for Batch Processing", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if files:
            self.batch_processor.clear()
            self.batch_processor.add_files(files)
            self._update_batch_table()
            self.tabs.setCurrentIndex(2)  # Switch to batch tab

    def _setup_batch_callbacks(self):
        def on_started(job: BatchJob, current: int, total: int):
            self.batch_progress.setValue(int(((current - 1) / total) * 100))
            self._update_batch_table()

        def on_completed(job: BatchJob, current: int, total: int):
            self.batch_progress.setValue(int((current / total) * 100))
            self._update_batch_table()

        def on_finished(jobs: List[BatchJob]):
            self.batch_progress.setValue(100)
            self.status_bar.showMessage("Batch processing completed.")
            self._update_batch_table()

        self.batch_processor.on_item_started = on_started
        self.batch_processor.on_item_completed = on_completed
        self.batch_processor.on_batch_finished = on_finished

    def _run_batch(self):
        if len(self.batch_processor.jobs) == 0:
            QMessageBox.information(self, "Empty Queue", "No photos in batch queue. Click 'Batch Photos' in sidebar.")
            return
        self.batch_processor.start_batch(
            settings=self.settings,
            photo_size_key=self.current_size,
            bg_mode=self.current_bg_mode,
            paper_key=self.current_paper,
            copies=self.current_copies
        )

    def _update_batch_table(self):
        jobs = self.batch_processor.jobs
        self.batch_table.setRowCount(len(jobs))
        for row, j in enumerate(jobs):
            self.batch_table.setItem(row, 0, QTableWidgetItem(os.path.basename(j.file_path)))
            self.batch_table.setItem(row, 1, QTableWidgetItem(j.status))
            prog_text = "100%" if j.status == "completed" else "Processing…" if j.status == "processing" else "0%"
            self.batch_table.setItem(row, 2, QTableWidgetItem(prog_text))
            res_text = "OK (Ready)" if j.status == "completed" else (j.error_message or "Pending")
            self.batch_table.setItem(row, 3, QTableWidgetItem(res_text))

    # --- Dialogs ---
    def _show_settings(self):
        dlg = SettingsDialog(self.db, self.settings, self)
        if dlg.exec():
            self.settings = self.db.load_settings()
            self._process_and_update()

    def _show_history(self):
        dlg = HistoryDialog(self.db, self)
        dlg.exec()
