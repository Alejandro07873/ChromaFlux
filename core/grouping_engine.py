from typing import Dict, List

from core.data_models import ColorEntry


def rgb_key(r: float, g: float, b: float) -> str:
    return f"{float(r):.6f}_{float(g):.6f}_{float(b):.6f}"


class ColorGroup:
    def __init__(self, r: float, g: float, b: float):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)

        self.total_uses = 0
        self.assets = set()
        self.usages: List[ColorEntry] = []

        self.affects_min = False
        self.affects_max = False

    def add(self, entry: ColorEntry):
        self.total_uses += 1
        self.assets.add(entry.asset)
        self.usages.append(entry)

        if entry.mode == "MIN":
            self.affects_min = True
        elif entry.mode == "MAX":
            self.affects_max = True


def group_color_entries(entries: List[ColorEntry]) -> Dict[str, ColorGroup]:
    groups: Dict[str, ColorGroup] = {}

    for entry in entries:
        key = rgb_key(entry.r, entry.g, entry.b)

        if key not in groups:
            groups[key] = ColorGroup(entry.r, entry.g, entry.b)

        groups[key].add(entry)

    return groups
