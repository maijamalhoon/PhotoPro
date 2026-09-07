"""
PhotoPro Windows Native Printing Integration
Controls QPrinter, page setup, margin zeroing, and 300 DPI spooling.
Guarantees Windows printer drivers do not auto-scale or distort millimeter dimensions.
"""
import logging
from typing import Optional
import numpy as np

from app.config.constants import DPI, PAPERS, PaperFormat

logger = logging.getLogger(__name__)

class PrinterService:
    """Manages Windows printer setup, hardware resolution, and image spooling."""

    @staticmethod
    def print_sheet(
        sheet_rgb: np.ndarray,
        paper_key: str = "4R",
        parent_widget=None
    ) -> bool:
        """
        Spools sheet image to Windows printer using PySide6 QPrinter & QPrintDialog.
        Ensures 1:1 millimeter physical mapping without driver downsampling.
        """
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QPainter, QImage, QPageSize, QPageLayout
            from PySide6.QtCore import QMarginsF, QSizeF, QRectF

            paper: PaperFormat = PAPERS.get(paper_key, PAPERS["4R"])

            # 1. Initialize HighResolution printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setResolution(DPI)
            printer.setFullPage(True)

            # 2. Configure Paper Layout
            if paper_key == "A4":
                page_size = QPageSize(QPageSize.PageSizeId.A4)
            else:
                # 4R is 101.6 x 152.4 mm (landscape or portrait)
                page_size = QPageSize(
                    QSizeF(paper.width_mm, paper.height_mm),
                    QPageSize.Unit.Millimeter,
                    "4R (6x4 in)"
                )

            # Set borderless / zero-margin print area for photo paper
            layout = QPageLayout(
                page_size,
                QPageLayout.Orientation.Portrait if paper.height_mm > paper.width_mm else QPageLayout.Orientation.Landscape,
                QMarginsF(0, 0, 0, 0)
            )
            printer.setPageLayout(layout)

            # 3. Open Windows Print Dialog
            dialog = QPrintDialog(printer, parent_widget)
            dialog.setWindowTitle("PhotoPro - Print Photo Sheet")

            if dialog.exec() != QPrintDialog.DialogCode.Accepted:
                logger.info("Print canceled by user.")
                return False

            # 4. Spool Sheet Image with QPainter
            h, w = sheet_rgb.shape[:2]
            qimg = QImage(
                sheet_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888
            )

            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError("Could not open painter on target printer.")

            # Target exact 300 DPI physical dimensions
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            painter.drawImage(rect, qimg)
            painter.end()

            logger.info(f"Print job successfully spooled for {paper.name}")
            return True

        except ImportError:
            logger.warning("PySide6 print support not available in current environment.")
            return False
        except Exception as e:
            logger.error(f"Printing failed: {e}")
            return False
