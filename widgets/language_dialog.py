from PySide6.QtWidgets import QDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtGui import QIcon

from core.resource_path import resource_path


class LanguageDialog(QDialog):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)

        self.i18n = i18n
        self.selected_language = None

        # ✅ Icono de la ventana (funciona en EXE)
        self.setWindowIcon(QIcon(resource_path("assets/icons/neon-settings.ico")))
        self.setWindowTitle("ChromaFlux")

        # ✅ Cargar UI usando resource_path (CRÍTICO)
        loader = QUiLoader()
        ui_path = resource_path("ui/language_dialog.ui")

        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # ✅ Layout correcto
        self.setLayout(self.ui.layout())
        self.adjustSize()

        # ✅ Textos i18n
        self.setWindowTitle(self.i18n.t("choose_language"))
        self.ui.btnSpanish.setText(self.i18n.t("language_spanish"))
        self.ui.btnEnglish.setText(self.i18n.t("language_english"))

        # ✅ Señales
        self.ui.btnSpanish.clicked.connect(self._select_es)
        self.ui.btnEnglish.clicked.connect(self._select_en)

    def _select_es(self):
        self.selected_language = "es"
        self.accept()

    def _select_en(self):
        self.selected_language = "en"
        self.accept()
