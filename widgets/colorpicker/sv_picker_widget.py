from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QPoint, Signal


class SVPickerWidget(QWidget):
    colorChanged = Signal(int, int)  # s, v

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)

        self.hue = 0
        self.sat = 255
        self.val = 255

        self._dragging = False

    def set_hue(self, h):
        self.hue = h
        self.update()

    def set_sv(self, s, v):
        self.sat = s
        self.val = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Fondo HSV
        for x in range(self.width()):
            for y in range(self.height()):
                s = int((x / self.width()) * 255)
                v = int((1 - y / self.height()) * 255)
                c = QColor()
                c.setHsv(self.hue, s, v)
                painter.setPen(c)
                painter.drawPoint(x, y)

        # Cursor
        cx = int((self.sat / 255) * self.width())
        cy = int((1 - self.val / 255) * self.height())

        painter.setPen(Qt.white)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(cx, cy), 6, 6)

    def mousePressEvent(self, event):
        self._dragging = True
        self._update_from_pos(event.position().toPoint())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_from_pos(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _update_from_pos(self, pos):
        x = max(0, min(pos.x(), self.width()))
        y = max(0, min(pos.y(), self.height()))

        s = int((x / self.width()) * 255)
        v = int((1 - y / self.height()) * 255)

        self.sat = s
        self.val = v

        self.colorChanged.emit(s, v)
        self.update()
