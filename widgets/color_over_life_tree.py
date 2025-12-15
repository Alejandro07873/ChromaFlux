from collections import defaultdict
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from widgets.colorpicker import ColorPickerDialog
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QHeaderView


class ColorCellDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Solo columna Color
        if index.column() != 1:
            super().paint(painter, option, index)
            return

        # Obtener el brush real
        brush = index.data(Qt.BackgroundRole)
        if not brush:
            # No es una celda de color → no dibujamos nada especial
            super().paint(painter, option, index)
            return

        painter.save()

        # 🔹 Espaciado interno (separación visual)
        rect = option.rect.adjusted(6, 6, -6, -6)


        # 🔹 Pintar color base (QBrush)
        painter.fillRect(rect, brush)

        # 🔹 Borde blanco fijo (solo en celdas de color)
        pen = QPen(QColor("#FFFFFF"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(rect)

        # 🔹 Borde celeste si está seleccionada
        if index.data(Qt.UserRole):
            pen = QPen(QColor("#00E5FF"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(-1, -1, 1, 1))

        painter.restore()


class ColorOverLifeTreeWidget(QTreeWidget):
    colorChanged = Signal(object)


    def __init__(self, parent=None):
        super().__init__(parent)


        # Fuente base de la tabla
        font = self.font()
        font.setPointSize(11)  # antes ~9
        self.setFont(font)

        header = self.header()
        header_font = header.font()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)

        header.setFixedHeight(34)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setUniformRowHeights(True)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2B2B2B;
                alternate-background-color: #2B2B2B;
            }

            QTreeWidget::item {
                background-color: #2B2B2B;
                height: 32px;
            }

            QTreeWidget::item:selected {
                background: transparent;
                color: inherit;
            }

            QTreeWidget::item:selected:active {
                background: transparent;
            }

            QTreeWidget::item:selected:!active {
                background: transparent;
            }
            """)

        
        self.setIndentation(24)

        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)


        
        self.setItemDelegateForColumn(1, ColorCellDelegate(self))

        # Cada vez que cambia selección, marcamos SOLO la columna Color
        self.itemSelectionChanged.connect(self._refresh_color_selection_highlight)

        # Constantes de columnas
        self.COL_COLOR = 1



    # --------------------------------------------------
    # NUEVO: cargar entries
    # --------------------------------------------------
    def load_entries(self, min_entries, max_entries):
        self.clear()

        tree = defaultdict(lambda: defaultdict(list))

        for e in min_entries + max_entries:
            asset_name = os.path.splitext(os.path.basename(e.asset))[0]
            tree[asset_name][e.module].append(e)

        for asset, modules in tree.items():
            asset_item = QTreeWidgetItem([f"Asset: {asset}"])
            asset_item.setFirstColumnSpanned(True)
            asset_item.setFlags(Qt.ItemIsEnabled)
            font = asset_item.font(0)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            asset_item.setFont(0, font)

            asset_item.setForeground(0, QColor("#E6E6E6"))
            self.addTopLevelItem(asset_item)


            for module, entries in modules.items():
                module_item = QTreeWidgetItem(asset_item)
                module_item.setText(0, module)
                module_item.setFlags(Qt.ItemIsEnabled)
                

                # Estilo visual de Módulo
                font = module_item.font(0)
                font.setPointSize(11)
                font.setBold(True)
                module_item.setFont(0, font)

                module_item.setForeground(0, QColor("#B0B0B0"))

                for entry in sorted(entries, key=lambda e: e.mode):
                    self._add_entry_row(module_item, entry)

                module_item.setExpanded(True)

            asset_item.setExpanded(True)

    def set_headers(self, headers: list[str]):
        self.setColumnCount(len(headers))
        self.setHeaderLabels(headers)

        header = self.header()

        # 🔒 CONTROL REAL DEL ANCHO
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setStretchLastSection(False)
        header.setSectionsClickable(False)

        # Tamaños definitivos
        self.setColumnWidth(0, 285) # nombre
        self.setColumnWidth(1, 150)  #color
        self.setColumnWidth(2, 70)  #R
        self.setColumnWidth(3, 70)  #G
        self.setColumnWidth(4, 70)  #B



    # --------------------------------------------------
    # Crear fila MIN / MAX
    # --------------------------------------------------
    def _add_entry_row(self, parent, entry):
        item = QTreeWidgetItem(parent)

        for col in (2, 3, 4):
            item.setTextAlignment(col, Qt.AlignCenter)
        item.setText(0, entry.mode)
        if entry.mode == "MAX":
            item.setForeground(0, QColor("#FF6A6A"))  # rojo suave
        else:
            item.setForeground(0, QColor("#6AE6FF"))  # cyan suave

        item.setText(2, f"{entry.r:.4f}")
        item.setText(3, f"{entry.g:.4f}")
        item.setText(4, f"{entry.b:.4f}")

        color = QColor.fromRgbF(entry.r, entry.g, entry.b)
        item.setBackground(1, color)

        # 🔑 Guardamos referencia REAL
        item.entry = entry

        item.setFlags(
            Qt.ItemIsSelectable |
            Qt.ItemIsEnabled
        )

    def _refresh_color_selection_highlight(self):
        # Recorremos todo y limpiamos highlight anterior en columna Color
        def walk(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                # Si es fila editable (tiene entry), limpiamos/ponemos highlight
                if hasattr(child, "entry"):
                    self._set_color_cell_selected(child, child.isSelected())
                walk(child)

        for i in range(self.topLevelItemCount()):
            walk(self.topLevelItem(i))


    def _set_color_cell_selected(self, item, selected: bool):
        # NO tocar el color base nunca
        entry = item.entry
        base = QColor.fromRgbF(entry.r, entry.g, entry.b)
        item.setBackground(self.COL_COLOR, base)

        # Solo marcar si está seleccionado (para el delegate)
        item.setData(self.COL_COLOR, Qt.UserRole, selected)




    def _on_item_double_clicked(self, item, column):
        if not hasattr(item, "entry"):
            return

        # Solo si se hace doble click en la columna Color (columna 1)
        if column != 1:
            return

        main = self.window()  # MainWindow
        dlg = ColorPickerDialog(main.i18n, self)

        if not dlg.exec():
            return

        new_color = dlg.get_color()
        if not new_color:
            return

        r, g, b = new_color
        entry = item.entry

        entry.set_rgb(r, g, b)

        item.setText(2, f"{r:.4f}")
        item.setText(3, f"{g:.4f}")
        item.setText(4, f"{b:.4f}")
        item.setBackground(1, QColor.fromRgbF(r, g, b))

        # 🔔 avisar al main
        self.colorChanged.emit(entry)

