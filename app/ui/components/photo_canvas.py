"""
PhotoPro Photo Canvas Component
Displays active photo with interactive pan, zoom, rotation, and ISO/IEC biometric guide oval overlay.
"""
import numpy as np

try:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtGui import QPainter, QImage, QColor, QPen, QBrush
    from PySide6.QtCore import Qt, QRectF, QPointF, Signal
    HAVE_QT = True
except ImportError:
    HAVE_QT = False
    class QWidget: pass

class PhotoCanvas(QWidget):
    """Interactive cropping viewport with biometric guide overlay."""
    cropChanged = Signal() if HAVE_QT else None

    def __init__(self, parent=None):
        if not HAVE_QT:
            super().__init__()
            return
        super().__init__(parent)
        self.image_qimg = None
        self.show_guide = True
        self.aspect_ratio = 35.0 / 45.0  # Default passport 35x45mm

        # Viewport transform
        self.zoom = 1.0
        self.angle = 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self._dragging = False
        self._last_mouse = QPointF()

        self.setMinimumSize(240, 310)
        self.setMouseTracking(True)

    def set_image(self, image_rgb: np.ndarray, aspect_ratio: float = 35.0 / 45.0):
        if not HAVE_QT or image_rgb is None:
            return
        h, w = image_rgb.shape[:2]
        self.image_qimg = QImage(
            image_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888
        ).copy()
        self.aspect_ratio = aspect_ratio
        self.reset_transform()
        self.update()

    def set_aspect_ratio(self, ratio: float):
        self.aspect_ratio = ratio
        self.update()

    def reset_transform(self):
        self.zoom = 1.0
        self.angle = 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0

    def set_zoom(self, zoom: float):
        self.zoom = max(1.0, min(3.0, zoom))
        self.update()

    def set_angle(self, angle: float):
        self.angle = angle
        self.update()

    def toggle_guide(self, enable: bool):
        self.show_guide = enable
        self.update()

    def paintEvent(self, event):
        if not HAVE_QT: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Fill neutral dark canvas
        painter.fillRect(rect, QColor("#18181B"))

        # Compute inner passport viewport rectangle
        target_w = w * 0.90
        target_h = target_w / self.aspect_ratio
        if target_h > h * 0.90:
            target_h = h * 0.90
            target_w = target_h * self.aspect_ratio

        vx = (w - target_w) / 2.0
        vy = (h - target_h) / 2.0
        viewport_rect = QRectF(vx, vy, target_w, target_h)

        # 1. Clip and draw image within viewport
        painter.save()
        painter.setClipRect(viewport_rect)
        painter.fillRect(viewport_rect, QColor("#FFFFFF"))

        if self.image_qimg:
            # Base scale to fit viewport
            img_w = self.image_qimg.width()
            img_h = self.image_qimg.height()
            base_scale = max(target_w / img_w, target_h / img_h)
            total_scale = base_scale * self.zoom

            # Center with offset and rotation
            painter.save()
            painter.translate(vx + target_w / 2.0 + self.offset_x, vy + target_h / 2.0 + self.offset_y)
            painter.rotate(self.angle)
            painter.scale(total_scale, total_scale)
            painter.drawImage(-img_w / 2.0, -img_h / 2.0, self.image_qimg)
            painter.restore()

        # 2. Biometric Passport Guide Overlay
        if self.show_guide:
            # Outer viewport boundary
            pen_bound = QPen(QColor(255, 255, 255, 180), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen_bound)
            painter.drawRect(viewport_rect)

            # Face oval (ISO/IEC crown to chin guideline)
            oval_w = target_w * 0.60
            oval_h = target_h * 0.70
            oval_x = vx + (target_w - oval_w) / 2.0
            oval_y = vy + target_h * 0.12

            pen_oval = QPen(QColor("#2563EB"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_oval)
            painter.drawEllipse(QRectF(oval_x, oval_y, oval_w, oval_h))

            # Eye line (around 42% from top of crop)
            eye_y = vy + target_h * 0.42
            pen_line = QPen(QColor("#2563EB"), 1, Qt.PenStyle.DotLine)
            painter.setPen(pen_line)
            painter.drawLine(QPointF(vx + target_w * 0.15, eye_y), QPointF(vx + target_w * 0.85, eye_y))

            # Chin line (around 80% from top)
            chin_y = vy + target_h * 0.80
            painter.drawLine(QPointF(vx + target_w * 0.25, chin_y), QPointF(vx + target_w * 0.75, chin_y))

        painter.restore()

        # Draw crisp border around viewport
        painter.setPen(QPen(QColor("#71717A"), 1))
        painter.drawRect(viewport_rect)
        painter.end()

    def mousePressEvent(self, event):
        if not HAVE_QT: return
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_mouse = event.position()

    def mouseMoveEvent(self, event):
        if not HAVE_QT: return
        if self._dragging:
            delta = event.position() - self._last_mouse
            self._last_mouse = event.position()
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.update()
            if self.cropChanged:
                self.cropChanged.emit()

    def mouseReleaseEvent(self, event):
        if not HAVE_QT: return
        self._dragging = False
