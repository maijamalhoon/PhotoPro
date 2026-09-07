"""
PhotoPro Before/After Split Comparison Component
Provides interactive side-by-side or sliding-split comparison of original and enhanced photo.
"""
import numpy as np

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
    from PySide6.QtGui import QPainter, QImage, QColor, QPen
    from PySide6.QtCore import Qt, QRectF
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QWidget: pass

class BeforeAfterView(QWidget):
    """Interactive split-slider or toggle comparison for original vs processed photo."""

    def __init__(self, parent=None):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__(parent)
        self.original_qimg = None
        self.processed_qimg = None
        self.split_position = 0.5  # 0.0 (all processed) to 1.0 (all original)
        self.mode = "slider"  # "slider" or "toggle"
        self.show_original = False
        self._is_dragging = False

        self.setMinimumSize(250, 320)
        self.setMouseTracking(True)

    def set_images(self, original_rgb: np.ndarray, processed_rgb: np.ndarray):
        if not HAVE_QT or original_rgb is None or processed_rgb is None:
            return

        h1, w1 = original_rgb.shape[:2]
        h2, w2 = processed_rgb.shape[:2]

        # Convert numpy RGB to QImage
        self.original_qimg = QImage(
            original_rgb.data, w1, h1, w1 * 3, QImage.Format.Format_RGB888
        ).copy()
        self.processed_qimg = QImage(
            processed_rgb.data, w2, h2, w2 * 3, QImage.Format.Format_RGB888
        ).copy()
        self.update()

    def toggle_original(self):
        self.show_original = not self.show_original
        self.update()

    def paintEvent(self, event):
        if not HAVE_QT or not self.processed_qimg:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Fill neutral canvas
        painter.fillRect(rect, QColor("#E4E4E7"))

        # Aspect ratio fitting
        img_aspect = self.processed_qimg.width() / float(self.processed_qimg.height())
        canvas_aspect = w / float(h)

        if img_aspect > canvas_aspect:
            dw = w
            dh = int(w / img_aspect)
            dx = 0
            dy = (h - dh) // 2
        else:
            dh = h
            dw = int(h * img_aspect)
            dx = (w - dw) // 2
            dy = 0

        target_rect = QRectF(dx, dy, dw, dh)

        if self.mode == "toggle":
            img_to_draw = self.original_qimg if self.show_original and self.original_qimg else self.processed_qimg
            painter.drawImage(target_rect, img_to_draw)
        else:
            # Slider Split View
            split_x = dx + int(dw * self.split_position)

            # Draw Processed (Right side)
            painter.save()
            painter.setClipRect(QRectF(split_x, dy, dx + dw - split_x, dh))
            painter.drawImage(target_rect, self.processed_qimg)
            painter.restore()

            # Draw Original (Left side)
            if self.original_qimg:
                painter.save()
                painter.setClipRect(QRectF(dx, dy, split_x - dx, dh))
                painter.drawImage(target_rect, self.original_qimg)
                painter.restore()

            # Draw divider bar
            pen = QPen(QColor("#2563EB"), 2)
            painter.setPen(pen)
            painter.drawLine(split_x, dy, split_x, dy + dh)

            # Draw handle pill
            painter.setBrush(QColor("#2563EB"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(split_x - 10, dy + dh // 2 - 10, 20, 20)
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(split_x - 4, dy + dh // 2 - 4, 8, 8)

        painter.end()

    def mousePressEvent(self, event):
        if not HAVE_QT: return
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._update_split_from_mouse(event.position().x())

    def mouseMoveEvent(self, event):
        if not HAVE_QT: return
        if self._is_dragging:
            self._update_split_from_mouse(event.position().x())

    def mouseReleaseEvent(self, event):
        if not HAVE_QT: return
        self._is_dragging = False

    def _update_split_from_mouse(self, mouse_x: float):
        w = self.width()
        pos = max(0.0, min(1.0, mouse_x / float(w)))
        self.split_position = pos
        self.update()
