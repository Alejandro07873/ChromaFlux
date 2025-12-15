import colorsys


def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(float(r), float(g), float(b))


def hsv_to_rgb(h, s, v):
    return colorsys.hsv_to_rgb(float(h), float(s), float(v))


def color_to_hex(r, g, b):
    R = max(0, min(255, int(float(r) * 255)))
    G = max(0, min(255, int(float(g) * 255)))
    B = max(0, min(255, int(float(b) * 255)))
    return f"#{R:02X}{G:02X}{B:02X}"


def hsv_distance(hsv1, hsv2):
    h1, _, _ = hsv1
    h2, _, _ = hsv2
    d = abs(h1 - h2)
    return min(d, 1.0 - d)


def is_similar_color(r1, g1, b1, r2, g2, b2, tolerance):
    hsv1 = rgb_to_hsv(r1, g1, b1)
    hsv2 = rgb_to_hsv(r2, g2, b2)
    return hsv_distance(hsv1, hsv2) <= float(tolerance)


def classify_color(r, g, b):
    h, s, v = rgb_to_hsv(r, g, b)

    if v < 0.1 or s < 0.1:
        return "Gris"
    if h < 0.05 or h > 0.95:
        return "Rojo"
    if h < 0.15:
        return "Naranja"
    if h < 0.30:
        return "Amarillo"
    if h < 0.45:
        return "Verde"
    if h < 0.60:
        return "Cian"
    if h < 0.75:
        return "Azul"
    if h < 0.90:
        return "Violeta"
    return "Desconocido"
