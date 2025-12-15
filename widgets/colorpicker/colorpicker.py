import os
from PySide6.QtWidgets import QDialog, QPushButton, QApplication, QVBoxLayout
from PySide6.QtGui import QColor
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from .wheel_widget import ColorWheelWidget
from .sv_picker_widget import SVPickerWidget
from .formats import (
    qcolor_to_rgb_f,
    qcolor_to_hex,
    hex_to_qcolor,
)
from .utils import is_valid_hex
from .presets import NEON_PRESETS
from .formats import (
    qcolor_to_rgb_f,
    qcolor_to_rgb_255,
    qcolor_to_hex,
    qcolor_to_hsv,
    qcolor_to_hsl,
    qcolor_to_cmyk,
    hex_to_qcolor,
)
from .history import ColorHistoryWidget





def parse_tuple(text, expected_len):
    text = text.strip().replace("(", "").replace(")", "")
    parts = [p.strip() for p in text.split(",")]

    if len(parts) != expected_len:
        return None

    try:
        return [int(float(p)) for p in parts]
    except ValueError:
        return None


class ColorPickerDialog(QDialog):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        
        self.setWindowTitle(self.i18n.t("color_picker_title"))



        # ==============================
        # Cargar UI (FORMA CORRECTA)
        # ==============================
        ui_path = os.path.join(os.path.dirname(__file__), "colorpicker_dialog.ui")
        loader = QUiLoader()
        ui_file = QFile(ui_path)

        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"No se pudo abrir UI: {ui_path}")

        ui = loader.load(ui_file)
        ui_file.close()

        if not ui:
            raise RuntimeError("No se pudo cargar colorpicker_dialog.ui")

        # 🔑 Anclar el layout del UI al QDialog real
        self.setLayout(ui.layout())
        self.ui = ui

        # ==============================
        # SV Picker
        # ==============================
        self.svPicker = SVPickerWidget(self)
        self.ui.svPickerPlaceholder.layout().addWidget(self.svPicker)

        # ==============================
        # Color Wheel
        # ==============================
        self.colorWheel = ColorWheelWidget(self)
        self.ui.wheelPlaceholder.layout().addWidget(self.colorWheel)

        # ==============================
        # Estado central del color
        # ==============================
        self.color = QColor("#00F5FF")
        self.previous_color = QColor("#000000")
    


        # ==============================
        # Conexiones
        # ==============================
        self.ui.editHex.textChanged.connect(self._on_hex_changed)

        self.ui.sliderHue.valueChanged.connect(self._on_hsv_changed)
        self.ui.sliderSat.valueChanged.connect(self._on_hsv_changed)
        self.ui.sliderVal.valueChanged.connect(self._on_hsv_changed)
        self.ui.sliderAlpha.valueChanged.connect(self._on_alpha_changed)

        self.svPicker.colorChanged.connect(self._on_sv_changed)
        
        self.colorWheel.hueChanged.connect(self._on_wheel_changed)

        self.ui.btnCopy.setText(self.i18n.t("colorpicker_copy"))
        self.ui.btnOk.setText(self.i18n.t("colorpicker_ok"))
        self.ui.btnCancel.setText(self.i18n.t("colorpicker_cancel"))
        # ==============================
        # BOTONES (ESTO FALTABA)
        # ==============================
        self.ui.btnCopy.clicked.connect(self._copy_hex)
        self.ui.btnOk.clicked.connect(self.accept)
        self.ui.btnCancel.clicked.connect(self.reject)


        


        # ==============================
        # FORMAT INPUTS (PASO 5)
        # ==============================
        self.ui.editRGB.editingFinished.connect(self._on_edit_rgb)
        self.ui.editHSV.editingFinished.connect(self._on_edit_hsv)
        self.ui.editHSL.editingFinished.connect(self._on_edit_hsl)
        self.ui.editCMYK.editingFinished.connect(self._on_edit_cmyk)

        self._dragging_sv = False
        self._build_presets()

        # ==============================
        # Color History
        # ==============================
        self.history = ColorHistoryWidget(parent=self)
        self.ui.historyPlaceholder.layout().addWidget(self.history)
        self.history.colorSelected.connect(self._on_history_selected)

        # Inicializar UI al final
        self._sync_from_color()



    # =====================================================
    # API pública
    # =====================================================

    def get_color(self):
        return qcolor_to_rgb_f(self.color)

    def get_hex(self):
        return qcolor_to_hex(self.color)
        # =====================================================
        # FORMATOS → COLOR (PASO 5)
        # =====================================================

    def set_from_rgb(self, r, g, b, a=255):
        color = QColor(int(r), int(g), int(b), int(a))
        if color.isValid():
            self.color = color
            self._sync_from_color()

    def set_from_hsv(self, h, s, v, a=255):
        color = QColor()
        color.setHsv(int(h), int(s), int(v), int(a))
        if color.isValid():
            self.color = color
            self._sync_from_color()

    def set_from_hsl(self, h, s, l, a=255):
        color = QColor()
        color.setHsl(int(h), int(s), int(l), int(a))
        if color.isValid():
            self.color = color
            self._sync_from_color()

    def set_from_cmyk(self, c, m, y, k, a=255):
        color = QColor()
        color.setCmyk(int(c), int(m), int(y), int(k), int(a))
        if color.isValid():
            self.color = color
            self._sync_from_color()



    def get_all_formats(self):

        return {
            "HEX": qcolor_to_hex(self.color),
            "RGB_255": qcolor_to_rgb_255(self.color),
            "RGB_F": qcolor_to_rgb_f(self.color),
            "HSV": qcolor_to_hsv(self.color),
            "HSL": qcolor_to_hsl(self.color),
            "CMYK": qcolor_to_cmyk(self.color),
        }

    # =====================================================
    # EVENTOS UI → COLOR
    # =====================================================

    def _on_hex_changed(self, text: str):
        if not is_valid_hex(text):
            return

        self.color = hex_to_qcolor(text)
        self._sync_from_color()


    def _mark_invalid(self, widget, invalid=True):
        if invalid:
            widget.setStyleSheet("border: 1px solid red;")
        else:
            widget.setStyleSheet("")

    def _on_edit_rgb(self):
        values = parse_tuple(self.ui.editRGB.text(), 3)
        if not values:
            self._mark_invalid(self.ui.editRGB, True)
            return

        r, g, b = values
        if not all(0 <= v <= 255 for v in (r, g, b)):
            self._mark_invalid(self.ui.editRGB, True)
            return

        self._mark_invalid(self.ui.editRGB, False)
        self.set_from_rgb(r, g, b, self.ui.sliderAlpha.value())


    def _on_edit_hsv(self):
        values = parse_tuple(self.ui.editHSV.text(), 4)
        if not values:
            self._mark_invalid(self.ui.editHSV, True)
            return

        h, s, v, a = values
        if not (0 <= h <= 359 and 0 <= s <= 255 and 0 <= v <= 255 and 0 <= a <= 255):
            self._mark_invalid(self.ui.editHSV, True)
            return

        self._mark_invalid(self.ui.editHSV, False)
        self.set_from_hsv(h, s, v, a)


    def _on_edit_hsl(self):
        values = parse_tuple(self.ui.editHSL.text(), 4)
        if not values:
            self._mark_invalid(self.ui.editHSL, True)
            return

        h, s, l, a = values
        if not (0 <= h <= 359 and 0 <= s <= 255 and 0 <= l <= 255 and 0 <= a <= 255):
            self._mark_invalid(self.ui.editHSL, True)
            return

        self._mark_invalid(self.ui.editHSL, False)
        self.set_from_hsl(h, s, l, a)


    def _on_edit_cmyk(self):
        values = parse_tuple(self.ui.editCMYK.text(), 5)
        if not values:
            self._mark_invalid(self.ui.editCMYK, True)
            return

        c, m, y, k, a = values
        if not all(0 <= v <= 255 for v in (c, m, y, k, a)):
            self._mark_invalid(self.ui.editCMYK, True)
            return

        self._mark_invalid(self.ui.editCMYK, False)
        self.set_from_cmyk(c, m, y, k, a)

        

    def _on_hsv_changed(self):
        self.color.setHsv(
            self.ui.sliderHue.value(),
            self.ui.sliderSat.value(),
            self.ui.sliderVal.value(),
            self.ui.sliderAlpha.value(),
        )
        self._sync_from_color()


    def _on_alpha_changed(self):
        self.color.setAlpha(self.ui.sliderAlpha.value())
        self._sync_from_color()


    def _on_sv_changed(self, s, v):
        h, _, _, a = self.color.getHsv()
        if h < 0:
            h = 0

        self.color.setHsv(h, s, v, a)

        # SOLO actualiza lo mínimo mientras arrastras
        self.svPicker.set_sv(s, v)
        self._update_preview()



    # =====================================================
    # COLOR → UI
    # =====================================================

    def _sync_from_color(self):
        h, s, v, a = self.color.getHsv()
        if h < 0:
            h = 0

        for w in (
            self.ui.sliderHue,
            self.ui.sliderSat,
            self.ui.sliderVal,
            self.ui.sliderAlpha,
        ):
            w.blockSignals(True)

        self.ui.sliderHue.setValue(h)
        self.ui.sliderSat.setValue(s)
        self.ui.sliderVal.setValue(v)
        self.ui.sliderAlpha.setValue(a)

        for w in (
            self.ui.sliderHue,
            self.ui.sliderSat,
            self.ui.sliderVal,
            self.ui.sliderAlpha,
    ):
            w.blockSignals(False)

        wheel_h = (540 - h) % 360
        self.colorWheel.set_hue(wheel_h)

        self.svPicker.set_hue(h)
        self.svPicker.set_sv(s, v)

        self._update_preview()
        self._update_hex_field()
        formats = self.get_all_formats()
        self.history.add_color(self.color)


        self.ui.editRGB.setText(str(formats["RGB_255"]))
        self.ui.editHSV.setText(str(formats["HSV"]))
        self.ui.editHSL.setText(str(formats["HSL"]))
        self.ui.editCMYK.setText(str(formats["CMYK"]))


    def _on_history_selected(self, color: QColor):
        if color.isValid():
            self.color = color
            self._sync_from_color()

    def _update_preview(self):
        self.ui.previewCurrent.setStyleSheet(
            f"background-color: {qcolor_to_hex(self.color)};"
        )
        self.ui.previewPrevious.setStyleSheet(
            f"background-color: {qcolor_to_hex(self.previous_color)};"
        )

    def _update_hex_field(self):
        hex_color = qcolor_to_hex(self.color)
        if self.ui.editHex.text().upper() != hex_color:
            self.ui.editHex.blockSignals(True)
            self.ui.editHex.setText(hex_color)
            self.ui.editHex.blockSignals(False)

    def _on_wheel_changed(self, h: int):
        qt_h = (540 - h) % 360
        _, s, v, a = self.color.getHsv()
        self.color.setHsv(qt_h, s, v, a)
        self._sync_from_color()



    # =====================================================
    # PRESETS
    # =====================================================

    def _build_presets(self):
        for hex_color in NEON_PRESETS:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {hex_color};
                    border-radius: 4px;
                    border: 1px solid #333;
                }}s
                QPushButton:hover {{
                    border: 1px solid #00f5ff;
                }}
                """
            )
            btn.clicked.connect(lambda _, c=hex_color: self._apply_preset(c))
            self.ui.presetLayout.addWidget(btn)

    def _apply_preset(self, hex_color: str):
        self.color = hex_to_qcolor(hex_color)
        self._sync_from_color()

    # =====================================================
    # UTILIDADES
    # =====================================================

    def _copy_hex(self):
        QApplication.clipboard().setText(self.get_hex())
       



