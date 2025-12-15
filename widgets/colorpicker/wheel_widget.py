import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QConicalGradient
from PySide6.QtCore import Qt, QPointF, Signal


class ColorWheelWidget(QWidget):
    hueChanged = Signal(int)  # 0–359

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self.hue = 0

    def set_hue(self, h: int):
        self.hue = h % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 6

        # Rueda HSV
        gradient = QConicalGradient(center, -90)
        for i in range(361):
            color = QColor()
            color.setHsv(i, 255, 255)
            gradient.setColorAt(i / 360, color)

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, radius, radius)

        # Cursor
        angle = math.radians(self.hue - 90)
        cx = center.x() + math.cos(angle) * radius
        cy = center.y() + math.sin(angle) * radius

        painter.setBrush(Qt.white)
        painter.setPen(Qt.black)
        painter.drawEllipse(QPointF(cx, cy), 6, 6)

    def mousePressEvent(self, event):
        self._update_from_pos(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._update_from_pos(event.position())

    def _update_from_pos(self, pos: QPointF):
        center = self.rect().center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()

        angle = math.degrees(math.atan2(dy, dx)) + 90
        if angle < 0:
            angle += 360

        hue = int(angle) % 360

        if hue != self.hue:
            self.hue = hue
            self.hueChanged.emit(hue)
            self.update()

