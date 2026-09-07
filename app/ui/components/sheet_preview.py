"""
PhotoPro Sheet Preview Component
Displays rendered 300 DPI sheet with zoom-to-fit, drop shadow, and crisp cutting marks.
"""
import numpy as np

try:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtGui import QPainter, QImage, QColor, QPen
    from PySide6.QtCore import Qt, QRectF
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QWidget: pass

class SheetPreview(QWidget):
    """Smooth-scaling preview widget for 4R and A4 print sheets."""

    def __init__(self, parent=None):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__(parent)
        self.sheet_qimg = None
        self.setMinimumSize(320, 240)

    def set_sheet(self, sheet_rgb: np.ndarray):
        if not HAVE_QT or sheet_rgb is None:
            return
        h, w = sheet_rgb.shape[:2]
        self.sheet_qimg = QImage(
            sheet_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888
        ).copy()
        self.update()

    def clear(self):
        self.sheet_qimg = None
        self.update()

    def paintEvent(self, event):
        if not HAVE_QT: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Canvas background
        painter.fillRect(rect, QColor("#E4E4E7"))

        if not self.sheet_qimg:
            # Placeholder text
            painter.setPen(QColor("#71717A"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No Sheet Generated\nSelect photo to render 300 DPI sheet")
            painter.end()
            return

        # Fit sheet within preview widget preserving aspect ratio with padding
        padding = 16
        avail_w = w - padding * 2
        avail_h = h - padding * 2

        img_w = self.sheet_qimg.width()
        img_h = self.sheet_qimg.height()
        aspect = img_w / float(img_h)

        if avail_w / float(avail_h) > aspect:
            draw_h = avail_h
            draw_w = int(avail_h * aspect)
        else:
            draw_w = avail_w
            draw_h = int(avail_w / aspect)

        draw_x = (w - draw_w) // 2
        draw_y = (h - draw_h) // 2
        dest_rect = QRectF(draw_x, draw_y, draw_w, draw_h)

        # Subtle paper drop shadow
        shadow_rect = QRectF(draw_x + 3, draw_y + 3, draw_w, draw_h)
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 30))

        # Draw sheet image
        painter.drawImage(dest_rect, self.sheet_qimg)

        # Draw outer sheet edge
        painter.setPen(QPen(QColor("#D4D4D8"), 1))
        painter.drawRect(dest_rect)

        painter.end()
