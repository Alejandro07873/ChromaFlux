from dataclasses import dataclass
from typing import List, Set, Any


@dataclass
class ColorUsageRow:
    asset: str
    module: str
    affects_min: bool
    affects_max: bool


@dataclass
class ColorEntry:
    asset: str
    module: str
    mode: str   # "MIN", "MAX", "START"
    r: float
    g: float
    b: float
    raw_ref: Any

    def __post_init__(self):
        self.r = float(self.r)
        self.g = float(self.g)
        self.b = float(self.b)

    def set_rgb(self, r: float, g: float, b: float):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)

        if isinstance(self.raw_ref, dict):
            self.raw_ref["X"] = self.r
            self.raw_ref["Y"] = self.g
            self.raw_ref["Z"] = self.b


@dataclass
class ColorTableRow:
    r: float
    g: float
    b: float

    total_uses: int
    assets: Set[str]
    usages: List[ColorUsageRow]

    affects_min: bool
    affects_max: bool

    selected: bool = False

    def as_qcolor_tuple(self):
        return (
            int(self.r * 255),
            int(self.g * 255),
            int(self.b * 255),
        )

    def set_rgb(self, r: float, g: float, b: float):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)


def build_table_rows(color_groups: dict) -> List[ColorTableRow]:
    rows: List[ColorTableRow] = []

    for group in color_groups.values():
        rows.append(
            ColorTableRow(
                r=float(group.r),
                g=float(group.g),
                b=float(group.b),
                total_uses=group.total_uses,
                assets=set(group.assets),
                usages=[
                    ColorUsageRow(
                        asset=u.asset,
                        module=u.module,
                        affects_min=(u.mode in ("MIN", "START")),
                        affects_max=(u.mode == "MAX"),
                    )
                    for u in group.usages
                ],
                affects_min=group.affects_min,
                affects_max=group.affects_max,
            )
        )

    return rows
