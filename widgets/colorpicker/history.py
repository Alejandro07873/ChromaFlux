from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal


class ColorHistoryWidget(QWidget):
    colorSelected = Signal(QColor)

    def __init__(self, max_items=8, parent=None):
        super().__init__(parent)
        self.max_items = max_items
        self.colors = []

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)

    def add_color(self, color: QColor):
        if not color.isValid():
            return

        hex_color = color.name().upper()

        # evitar duplicados
        if hex_color in self.colors:
            self.colors.remove(hex_color)

        self.colors.insert(0, hex_color)
        self.colors = self.colors[: self.max_items]

        self._rebuild()

    def _rebuild(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for hex_color in self.colors:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {hex_color};
                    border-radius: 4px;
                    border: 1px solid #333;
                }}
                QPushButton:hover {{
                    border: 1px solid #00f5ff;
                }}
                """
            )
            btn.clicked.connect(
                lambda _, c=hex_color: self.colorSelected.emit(QColor(c))
            )
            self.layout.addWidget(btn)
