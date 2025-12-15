from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RGB:
    r: float
    g: float
    b: float

    def __post_init__(self):
        self.r = float(self.r)
        self.g = float(self.g)
        self.b = float(self.b)

    @classmethod
    def from_json_vec(cls, vec: Dict[str, Any]) -> "RGB":
        return cls(
            vec.get("X", 0.0),
            vec.get("Y", 0.0),
            vec.get("Z", 0.0),
        )

    def to_json_vec(self) -> Dict[str, float]:
        return {
            "X": float(self.r),
            "Y": float(self.g),
            "Z": float(self.b),
        }

    def as_tuple(self) -> Tuple[float, float, float]:
        return float(self.r), float(self.g), float(self.b)


@dataclass
class Scalar:
    name: str
    value: float
    offset: Optional[int] = None


@dataclass
class ColorOverLife:
    asset_path: str
    entry_index: int
    name: str

    min_value: Optional[float] = None
    max_value: Optional[float] = None

    min_vec: Optional[RGB] = None
    max_vec: Optional[RGB] = None

    values: List[float] = field(default_factory=list)

    keep_min_value_zero: bool = False
    no_vectors: bool = False
    no_min_or_max_value: bool = False
    enforce_equal_vectors: bool = False

    json_node: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_min_vec(self) -> bool:
        return self.min_vec is not None

    @property
    def has_max_vec(self) -> bool:
        return self.max_vec is not None

    @property
    def min_vec_tuple(self) -> Optional[Tuple[float, float, float]]:
        return self.min_vec.as_tuple() if self.min_vec else None

    @property
    def max_vec_tuple(self) -> Optional[Tuple[float, float, float]]:
        return self.max_vec.as_tuple() if self.max_vec else None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def color_over_life_from_json(
    asset_path: str,
    entry_index: int,
    entry: Dict[str, Any],
) -> Optional[ColorOverLife]:

    if entry.get("Type") != "ParticleModuleColorOverLife":
        return None

    name = entry.get("Name", f"ColorOverLife_{entry_index}")
    props = entry.get("Properties") or {}
    col_node = props.get("ColorOverLife") or {}

    min_value = _coerce_float(col_node.get("MinValue"))
    max_value = _coerce_float(col_node.get("MaxValue"))

    min_vec_node = col_node.get("MinValueVec")
    max_vec_node = col_node.get("MaxValueVec")

    min_vec = RGB.from_json_vec(min_vec_node) if isinstance(min_vec_node, dict) else None
    max_vec = RGB.from_json_vec(max_vec_node) if isinstance(max_vec_node, dict) else None

    values_raw = col_node.get("Values") or []
    values = [_coerce_float(v) for v in values_raw if _coerce_float(v) is not None]

    enforce_equal_vectors = (
        min_vec is not None
        and max_vec is not None
        and min_vec.as_tuple() == max_vec.as_tuple()
    )

    keep_min_zero = min_value is not None and abs(min_value) < 1e-6

    return ColorOverLife(
        asset_path=asset_path,
        entry_index=entry_index,
        name=name,
        min_value=min_value,
        max_value=max_value,
        min_vec=min_vec,
        max_vec=max_vec,
        values=values,
        keep_min_value_zero=keep_min_zero,
        enforce_equal_vectors=enforce_equal_vectors,
        json_node=col_node,
    )


def extract_color_over_life_list(
    asset_path: str,
    json_root: Any,
) -> List[ColorOverLife]:

    if not isinstance(json_root, list):
        return []

    result: List[ColorOverLife] = []

    for idx, entry in enumerate(json_root):
        if not isinstance(entry, dict):
            continue
        col = color_over_life_from_json(asset_path, idx, entry)
        if col:
            result.append(col)

    return result
