import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,QLabel,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (
    QFile, Qt, Signal, QTimer)

from PySide6.QtGui import QColor
from core.asset_pipeline import AssetPipeline
from core.json_reader import load_color_over_life_from_root
from widgets.colorpicker import ColorPickerDialog
from core.i18n_manager import I18N
from core.settings_manager import SettingsManager
from widgets.language_dialog import LanguageDialog
from PySide6.QtGui import QColor, QIcon
from PySide6.QtCore import QSize
from widgets.color_over_life_tree import ColorOverLifeTreeWidget
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Signal
from core.resource_path import resource_path
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl



# =========================================================
# DROP ZONE
# =========================================================
class DropZone(QLabel):
    dropped = Signal(list)  
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 🔒 Evitar que cambie de tamaño por el texto
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setWordWrap(False)

        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)

        # 🔒 TAMAÑO DEFINITIVO (AJUSTA AQUÍ)
        self.setFixedSize(225, 180)

        self._default_text = ""
        self._default_style = """
        QLabel {
            border: 2px dashed #555;
            color: #999;
        }
        """
        self.setText(self._default_text)
        self.setStyleSheet(self._default_style)

    def set_default_text(self, text):
        self._default_text = text
        self.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


    def set_release_text(self, text):
        self._release_text = text

    def set_invalid_text(self, text):
        self._invalid_text = text


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            valid = any(
                url.toLocalFile().lower().endswith(".uasset")
                or os.path.isdir(url.toLocalFile())
                for url in event.mimeData().urls()
            )

            if valid:
                self.setStyleSheet("border: 2px dashed #4CAF50; color: #4CAF50;")
                self.setText(self._release_text)
                event.acceptProposedAction()
            else:
                self.setStyleSheet("border: 2px dashed #F44336; color: #F44336;")
                self.setText(self._invalid_text)
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._reset()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self._reset()
        if paths:
            self.dropped.emit(paths)

    def _reset(self):
        self.setStyleSheet(self._default_style)
        self.setText(self._default_text)
       




# =========================================================
# MAIN WINDOW
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # i18n temporal para que nada crashee antes del late init
        self.i18n = I18N("es")

        # 1) Cargar UI lo más rápido posible
        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "main_window.ui")
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.setCentralWidget(self.ui.centralwidget)

        # 2) Estado mínimo
        self.min_entries = []
        self.max_entries = []
        self.selected_color = None
        self.json_roots = {}

        # 3) Conectar botones (sin depender del idioma aún)
        self.ui.btnSelectFolder.clicked.connect(self.load_folder)
        self.ui.btnSelectFiles.clicked.connect(self.load_files)
        self.ui.btnPickColor.clicked.connect(self.pick_color)
        self.ui.btnApply.clicked.connect(self.apply_changes)
        self.ui.chkMin.stateChanged.connect(self.select_min_rows)
        self.ui.chkMax.stateChanged.connect(self.select_max_rows)

        # 4) Dropzone y progress bar
        self._install_dropzone()
        self.ui.txtLog.setFixedWidth(225)
        self.ui.txtLog.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.ui.progressBar.setVisible(False)

        # 5) Cargar lo pesado después de que la ventana ya esté viva
        QTimer.singleShot(0, self._late_init)

    def _late_init(self):
        # Settings + idioma
        self.settings = SettingsManager()
        lang = self.settings.get("language")

        if not lang:
            tmp_i18n = I18N("es")
            dlg = LanguageDialog(tmp_i18n, self)
            if dlg.exec():
                lang = dlg.selected_language
                self.settings.set("language", lang)
            else:
                lang = "es"
                self.settings.set("language", lang)

        self.i18n = I18N(lang)

        # Tree
        self.tree = ColorOverLifeTreeWidget(self)
        self.tree.colorChanged.connect(self.on_tree_color_changed)
        self.ui.chkSelectAll.stateChanged.connect(self.select_all_rows)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectItems)

        # Reemplazar tabs por tree
        parent_layout = self.ui.tabWidget.parentWidget().layout()
        parent_layout.replaceWidget(self.ui.tabWidget, self.tree)
        self.ui.tabWidget.deleteLater()
        self.selection_undo_stack = []
        self.selection_redo_stack = []
        QShortcut(QKeySequence.Undo, self, activated=self.undo_selection)
        QShortcut(QKeySequence.Redo, self, activated=self.redo_selection)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

        # Iconos
        icon_path = resource_path("assets/icons/neon-settings.ico")
        self.ui.btnSettings.setIcon(QIcon(icon_path))
        self.ui.btnSettings.setIconSize(QSize(18, 18))
        self.setWindowIcon(QIcon(resource_path("assets/icons/icon4.ico")))
        self.ui.btnSupport.setIcon(
            QIcon(resource_path("assets/icons/iconHeard.ico"))
        )
        self.ui.btnSupport.setIconSize(QSize(18, 18))

        # Pipeline (esto puede tardar la primera vez)
        self.pipeline = AssetPipeline()

        # UI text
        self.apply_language()
        self._setup_settings_menu()
        self._setup_support_menu()


        self.log(self.i18n.t("log_app_started"))
        # =====================================================
        # Estado inicial del progress stack (mostrar placeholder)
        # =====================================================
        if hasattr(self.ui, "progressStack"):
            self.ui.progressStack.setCurrentIndex(0)




    def apply_language(self):
        t = self.i18n.t

    # Window
        self.setWindowTitle(t("app_title"))

        self.ui.txtLog.setStyleSheet("""
        QPlainTextEdit {
            font-size: 11px;
            background-color: #0f0f0f;
            border: none;
        }
        """)



    # Top bar
        self.ui.btnSelectFolder.setText(t("select_folder"))
        self.ui.btnSelectFiles.setText(t("select_files"))

        # Tree headers (Color Over Life)
        # Tree headers (Color Over Life)
        if hasattr(self, "tree"):
            self.tree.set_headers([
                t("col_type"),
                t("col_color"),
                t("col_r"),
                t("col_g"),
                t("col_b"),
            ])

            # 🔑 Reajustar columnas del Tree tras cambiar idioma
            header = self.tree.header()

            header.blockSignals(True)

            header.setSectionResizeMode(QHeaderView.Fixed)
            header.setStretchLastSection(False)
            header.setSectionsClickable(False)

            self.tree.setColumnWidth(0, 285)  # Tipo
            self.tree.setColumnWidth(1, 150)  # Color
            self.tree.setColumnWidth(2, 70)   # R
            self.tree.setColumnWidth(3, 70)   # G
            self.tree.setColumnWidth(4, 70)   # B

            header.blockSignals(False)



        self.ui.btnPickColor.setText(t("choose_color"))
        self.ui.btnApply.setText(t("apply_changes"))

        self.ui.chkSelectAll.setText(t("select_all"))
        self.ui.chkSyncMinMax.setText(t("sync_min_max"))

        self.ui.chkMin.setText("MIN")
        self.ui.chkMax.setText("MAX")



        self.ui.btnSettings.setToolTip(t("settings"))

    # Status
        self.ui.lblStatus.setText(t("ready"))

    # File counter (reset text, luego se actualizará al cargar assets)
        self.ui.lblFileCount.setText(t("files_loaded", count=0))

    # DropZone (TU widget, no el ui)
        if hasattr(self, "dropZone"):
            self.dropZone.set_default_text(t("dropzone_default"))
            self.dropZone.set_release_text(t("dropzone_release"))
            self.dropZone.set_invalid_text(t("dropzone_invalid"))


        self.ui.btnSettings.setToolTip(t("settings"))
        self.ui.txtLog.setPlaceholderText(t("log_placeholder"))
        self.ui.txtFilter.setPlaceholderText(t("search_placeholder"))
        self.ui.progressBar.setFormat(t("loading_progress"))

    def _open_dropzone_dialog(self):
        menu = QMenu(self)

        act_files = menu.addAction(self.i18n.t("select_files"))
        act_folder = menu.addAction(self.i18n.t("select_folder"))

        action = menu.exec(self.cursor().pos())

        if action == act_files:
            self.load_files()
        elif action == act_folder:
            self.load_folder()

    def _on_selection_changed(self):
        selected = {
            id(it.entry)
            for it in self.tree.selectedItems()
            if hasattr(it, "entry")
        }

        # 🚫 Evitar duplicados consecutivos (INCLUSO vacío)
        if self.selection_undo_stack and self.selection_undo_stack[-1] == selected:
            return

        self.selection_undo_stack.append(selected)

        # 🔄 Cualquier nueva acción invalida redo
        self.selection_redo_stack.clear()



    def _restore_selection(self, state):
        self.tree.blockSignals(True)
        self.tree.clearSelection()

        def walk(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if hasattr(child, "entry") and id(child.entry) in state:
                    child.setSelected(True)
                walk(child)

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))

        self.tree.blockSignals(False)
        self.tree._refresh_color_selection_highlight()
        self.tree.viewport().update()

    def undo_selection(self):
        if len(self.selection_undo_stack) < 2:
            return

        # Estado actual → redo
        current = self.selection_undo_stack.pop()
        self.selection_redo_stack.append(current)

        # Estado anterior → restaurar
        prev = self.selection_undo_stack[-1]
        self._restore_selection(prev)



    def redo_selection(self):
        if not self.selection_redo_stack:
            return

        state = self.selection_redo_stack.pop()

        # El estado actual vuelve a undo
        self.selection_undo_stack.append(state)

        self._restore_selection(state)


    def _setup_settings_menu(self):
        if not hasattr(self.ui, "btnSettings"):
            return

        menu = QMenu(self)

        # Agregar opciones de idioma
        act_es = menu.addAction("Español")
        act_en = menu.addAction("English")

        # Conectar las acciones a sus métodos correspondientes
        act_es.triggered.connect(lambda: self.change_language("es"))
        act_en.triggered.connect(lambda: self.change_language("en"))

        self.ui.btnSettings.setMenu(menu)

    def _setup_support_menu(self):
        if not hasattr(self.ui, "btnSupport"):
            return

        menu = QMenu(self)

        act_kofi = menu.addAction("☕ Ko-fi")
        act_paypal = menu.addAction("♥️ PayPal")

        act_kofi.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://ko-fi.com/alejo__07873")
            )
        )

        act_paypal.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://www.paypal.com/paypalme/Alejo07378")
            )
        )

        self.ui.btnSupport.setMenu(menu)


    def change_language(self, lang):
        self.i18n.load(lang)
        self.settings.set("language", lang)

        self.apply_language()

        # 🔑 FORZAR REAJUSTE DE LAYOUT
        layout = self.ui.centralwidget.layout()
        if layout:
            layout.invalidate()
            layout.activate()

        # 🔑 Ajustar ventana sin romper tamaños fijos
        self.adjustSize()

        self.log(
            self.i18n.t("log_language_changed", lang=lang.upper()),
            level="OK"
        )



    # =====================================================
    # LOG PROFESIONAL (NUEVO)
    # =====================================================
    def log(self, message, level="INFO"):
        if not hasattr(self.ui, "txtLog"):
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        COLORS = {
            "INFO":  "#B0BEC5",  # gris claro
            "OK":    "#4CAF50",  # verde
            "WARN":  "#FFC107",  # amarillo
            "ERROR": "#F44336",  # rojo
            "DEBUG": "#64B5F6",  # azul
        }

        color = COLORS.get(level, "#B0BEC5")

        html = f"""
        <span style="color:#777;">[{timestamp}]</span>
        <span style="color:{color}; font-weight:600;"> {level}</span>
        <span style="color:#E0E0E0;"> {message}</span>
        """

        self.ui.txtLog.appendHtml(html)
        self.ui.txtLog.verticalScrollBar().setValue(
            self.ui.txtLog.verticalScrollBar().maximum()
        )


    def _install_dropzone(self):
        placeholder = self.ui.dropZone
        dz = DropZone(placeholder.parentWidget())
        dz.set_default_text(self.i18n.t("dropzone_default"))
        dz.set_release_text(self.i18n.t("dropzone_release"))
        dz.set_invalid_text(self.i18n.t("dropzone_invalid"))

        dz.dropped.connect(self.handle_drop)
        dz.clicked.connect(self._open_dropzone_dialog)


        layout = placeholder.parentWidget().layout()
        layout.replaceWidget(placeholder, dz)
        placeholder.deleteLater()
        self.dropZone = dz


    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            self.i18n.t("dialog_select_folder")
        )

        if not folder:
            return

        self.log(self.i18n.t("log_loading_folder", path=folder))

        uassets = [
            os.path.join(r, f)
            for r, _, files in os.walk(folder)
            for f in files if f.lower().endswith(".uasset")
        ]

        self.log(self.i18n.t("log_processing_assets", count=len(uassets)))
        self.load_assets(uassets)

    def load_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.i18n.t("dialog_select_uasset"),
            "",
            self.i18n.t("file_filter_uasset")
        )


        if files:
             self.log(
                self.i18n.t(
                    "log_loading_files",
                    count=len(files)
                )
            )

        self.load_assets(files)

    def handle_drop(self, paths):
        self.log(self.i18n.t("log_drag_drop_received", count=len(paths)))
        uassets = []
        for p in paths:
            if os.path.isfile(p) and p.lower().endswith(".uasset"):
                uassets.append(p)
            elif os.path.isdir(p):
                for r, _, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(".uasset"):
                            uassets.append(os.path.join(r, f))
        self.load_assets(uassets)

    def load_assets(self, uassets):
        if not hasattr(self, "pipeline"):
            self.log("Inicializando... espera un segundo.", level="WARN")
            return
        
        # =====================================================
        # ❌ EXCLUIR ASSETS QUE CONTENGAN "moji"
        # =====================================================
        filtered_assets = []
        excluded_assets = []

        for path in uassets:
            name = os.path.basename(path).lower()
            if "moji" in name:
                excluded_assets.append(path)
            else:
                filtered_assets.append(path)

        if excluded_assets:
            self.log(
                f"Se excluyeron {len(excluded_assets)} assets que contienen 'moji'",
                level="INFO"
            )

        # Reemplazamos la lista original
        uassets = filtered_assets



        self.log(self.i18n.t("log_processing_assets", count=len(uassets)))
        self.min_entries.clear()
        self.max_entries.clear()
        self.json_roots.clear()

        # =====================================================
        # Mostrar progress bar y ocultar placeholder inferior
        # =====================================================
        if hasattr(self.ui, "progressStack"):
            self.ui.progressStack.setCurrentIndex(1)


        self.ui.progressBar.setRange(0, len(uassets))
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setVisible(True)

        for index, uasset in enumerate(uassets):
            json_path = self.pipeline.convert_uasset_to_json(uasset)

            with open(json_path, "r", encoding="utf-8") as f:
                root = json.load(f)

            self.json_roots[json_path] = root
            mins, maxs = load_color_over_life_from_root(json_path, root)
            self.min_entries.extend(mins)
            self.max_entries.extend(maxs)

            self.ui.progressBar.setValue(index + 1)

        self.ui.lblFileCount.setText(
            self.i18n.t(
                "files_loaded_count",
                count=len(set(e.asset for e in self.min_entries))
            )
        )


        self.tree.load_entries(self.min_entries, self.max_entries)

        self.ui.progressBar.setVisible(False)
        # =====================================================
        # Volver a mostrar placeholder inferior
        # =====================================================
        if hasattr(self.ui, "progressStack"):
            self.ui.progressStack.setCurrentIndex(0)


        self.log(self.i18n.t("log_assets_loaded"), level="OK")

    def select_all_rows(self, state):
        self.tree.blockSignals(True)
        self.tree.clearSelection()

        if state == Qt.Checked:
            def walk(parent_item):
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if hasattr(child, "entry"):
                        child.setSelected(True)
                    walk(child)

            for i in range(self.tree.topLevelItemCount()):
                walk(self.tree.topLevelItem(i))

        self.tree.blockSignals(False)

        # refrescar visual
        self.tree._refresh_color_selection_highlight()
        self.tree.viewport().update()


    def _select_by_mode(self, mode: str):
        self.tree.blockSignals(True)

        # Mejor limpiar con selectionModel (más fiable)
        sel = self.tree.selectionModel()
        sel.clearSelection()

        def walk(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)

                if hasattr(child, "entry") and child.entry.mode == mode:
                    child.setSelected(True)

                walk(child)

        for i in range(self.tree.topLevelItemCount()):
            walk(self.tree.topLevelItem(i))

        self.tree.blockSignals(False)

        self.tree._refresh_color_selection_highlight()
        self.tree.viewport().update()




    def select_min_rows(self, state):
        if state != Qt.Checked:
            # 🔑 LIMPIAR selección al quitar el check
            self.tree.clearSelection()
            self.tree._refresh_color_selection_highlight()
            self.tree.viewport().update()
            return

        self.ui.chkSelectAll.blockSignals(True)
        self.ui.chkMax.blockSignals(True)

        self.ui.chkSelectAll.setChecked(False)
        self.ui.chkMax.setChecked(False)

        self.ui.chkSelectAll.blockSignals(False)
        self.ui.chkMax.blockSignals(False)

        self._select_by_mode("MIN")


    def select_max_rows(self, state):
        if state != Qt.Checked:
            # 🔑 LIMPIAR selección al quitar el check
            self.tree.clearSelection()
            self.tree._refresh_color_selection_highlight()
            self.tree.viewport().update()
            return

        self.ui.chkSelectAll.blockSignals(True)
        self.ui.chkMin.blockSignals(True)

        self.ui.chkSelectAll.setChecked(False)
        self.ui.chkMin.setChecked(False)

        self.ui.chkSelectAll.blockSignals(False)
        self.ui.chkMin.blockSignals(False)

        self._select_by_mode("MAX")



    def pick_color(self):
        items = [it for it in self.tree.selectedItems() if hasattr(it, "entry")]

        # Si no hay selección, pero hay un checkbox activo, generamos la selección automáticamente
        if not items:
            if self.ui.chkSelectAll.isChecked():
                self.select_all_rows(Qt.Checked)
            elif self.ui.chkMin.isChecked():
                self._select_by_mode("MIN")
            elif self.ui.chkMax.isChecked():
                self._select_by_mode("MAX")

            items = [it for it in self.tree.selectedItems() if hasattr(it, "entry")]

        # ❌ Si sigue sin haber items, ahora sí es error real
        if not items:
            self.log(self.i18n.t("log_select_row_warning"), level="WARN")
            return

        # ✅ SIEMPRE abrir el picker
        dlg = ColorPickerDialog(self.i18n, self)
        if not dlg.exec():
            return

        rgb = dlg.get_color()
        if not rgb:
            return

        r, g, b = rgb

        for item in items:
            entry = item.entry
            entry.set_rgb(r, g, b)

            item.setText(2, f"{r:.4f}")
            item.setText(3, f"{g:.4f}")
            item.setText(4, f"{b:.4f}")
            item.setBackground(1, QColor.fromRgbF(r, g, b))

            # Sync MIN/MAX si aplica
            self.on_tree_color_changed(entry)

        self.selected_color = rgb

        self.ui.lblChosenColor.setStyleSheet(
            f"background-color: rgb({int(r*255)},{int(g*255)},{int(b*255)});"
        )

        # 🔄 Refrescar visual
        self.tree._refresh_color_selection_highlight()
        self.tree.viewport().update()

        self.log(self.i18n.t("log_color_selected"))





    def on_tree_color_changed(self, entry):
        # Si Sync Min / Max no está activo, no hacemos nada
        if not self.ui.chkSyncMinMax.isChecked():
            return

        # Buscar el hermano MIN <-> MAX del mismo asset y módulo
        for e in (self.min_entries + self.max_entries):
            if (
                e is not entry
                and e.asset == entry.asset
                and e.module == entry.module
                and e.mode != entry.mode
            ):
                e.set_rgb(entry.r, entry.g, entry.b)

        # NO reconstruyas el árbol: eso destruye la selección.
        # Solo refresca la vista.

        self.tree._refresh_color_selection_highlight()
        self.tree.viewport().update()

        # Si quieres mantener Select All, no lo recalcules aquí.
        # (Opcional: puedes dejarlo fuera)





    def apply_changes(self):
        if not hasattr(self, "pipeline"):
            self.log("Inicializando... espera un segundo.", level="WARN")
            return
        self.log(self.i18n.t("log_applying_changes"))

        # 1) Detectar qué JSONs hay que guardar
        touched_jsons = set()
        for entry in (self.min_entries + self.max_entries):
            touched_jsons.add(entry.asset)  # entry.asset aquí es el json_path

        # 2) Guardar cada JSON y reconvertir a UASSET
        for json_path in touched_jsons:
            root = self.json_roots.get(json_path)
            if root is None:
                continue

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(root, f, ensure_ascii=False, indent=4)

            self.pipeline.convert_json_to_uasset(json_path)

            try:
                os.remove(json_path)
            except Exception:
                pass

        self.ui.lblStatus.setText(self.i18n.t("log_changes_applied"))
        self.log(self.i18n.t("log_changes_applied"), level="OK")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("ChromaFlux")
    app.setOrganizationName("ChromaFlux")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
