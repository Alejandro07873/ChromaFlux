from PySide6.QtGui import QColor


# ===============================
# HEX
# ===============================

def qcolor_to_hex(color: QColor) -> str:
    return color.name(QColor.HexRgb).upper()


def hex_to_qcolor(hex_color: str) -> QColor:
    return QColor(hex_color)


# ===============================
# RGB
# ===============================

def qcolor_to_rgb_255(color: QColor):
    return color.red(), color.green(), color.blue()


def qcolor_to_rgb_f(color: QColor):
    return color.redF(), color.greenF(), color.blueF()


# ===============================
# HSV
# ===============================

def qcolor_to_hsv(color: QColor):
    h, s, v, a = color.getHsv()
    return h, s, v, a


# ===============================
# HSL
# ===============================

def qcolor_to_hsl(color: QColor):
    h, s, l, a = color.getHsl()
    return h, s, l, a


# ===============================
# CMYK
# ===============================

def qcolor_to_cmyk(color: QColor):
    c, m, y, k, a = color.getCmyk()
    return c, m, y, k, a
