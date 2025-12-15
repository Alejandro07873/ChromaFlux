from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set

from core.color_over_life import ColorOverLife


ColorKey = Tuple[float, float, float]


@dataclass
class ColorUsage:
    asset: str
    module_name: str
    affects_min: bool
    affects_max: bool


@dataclass
class ColorGroup:
    r: float
    g: float
    b: float

    total_uses: int = 0
    assets: Set[str] = field(default_factory=set)
    usages: List[ColorUsage] = field(default_factory=list)

    affects_min: bool = False
    affects_max: bool = False


def group_color_over_life(
    asset_name: str,
    modules: List[ColorOverLife],
    groups: Dict[ColorKey, ColorGroup]
):
    for module in modules:

        if module.has_min_vec and module.min_vec is not None:
            key = module.min_vec.as_tuple()
            _add_to_group(
                key=key,
                asset=asset_name,
                module=module,
                affects_min=True,
                affects_max=False,
                groups=groups
            )

        if module.has_max_vec and module.max_vec is not None:
            key = module.max_vec.as_tuple()
            _add_to_group(
                key=key,
                asset=asset_name,
                module=module,
                affects_min=False,
                affects_max=True,
                groups=groups
            )


def _add_to_group(
    key: ColorKey,
    asset: str,
    module: ColorOverLife,
    affects_min: bool,
    affects_max: bool,
    groups: Dict[ColorKey, ColorGroup]
):
    if key not in groups:
        groups[key] = ColorGroup(
            r=float(key[0]),
            g=float(key[1]),
            b=float(key[2])
        )

    group = groups[key]

    group.total_uses += 1
    group.assets.add(asset)

    group.affects_min |= affects_min
    group.affects_max |= affects_max

    group.usages.append(
        ColorUsage(
            asset=asset,
            module_name=module.name,
            affects_min=affects_min,
            affects_max=affects_max
        )
    )
