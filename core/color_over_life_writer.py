from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
import json
import os
import subprocess

from color_over_life import RGB, ColorOverLife, extract_color_over_life_list


@dataclass
class ColorOccurrence:
    key: Tuple[float, float, float]
    asset_path: str
    entry_index: int
    name: str
    role: str
    rgb: RGB
    json_vec_node: Dict[str, Any]


@dataclass
class ColorGroup:
    key: Tuple[float, float, float]
    occurrences: List[ColorOccurrence] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.occurrences)

    @property
    def sample_rgb(self) -> RGB:
        return self.occurrences[0].rgb


def _quantize_color(rgb: RGB, decimals: int = 6) -> Tuple[float, float, float]:
    r, g, b = rgb.as_tuple()
    return round(r, decimals), round(g, decimals), round(b, decimals)


def build_color_groups(colors: Iterable[ColorOverLife]) -> List[ColorGroup]:
    buckets: Dict[Tuple[float, float, float], List[ColorOccurrence]] = {}

    for col in colors:
        if col.min_vec:
            key = _quantize_color(col.min_vec)
            occ = ColorOccurrence(
                key=key,
                asset_path=col.asset_path,
                entry_index=col.entry_index,
                name=col.name,
                role="MIN",
                rgb=col.min_vec,
                json_vec_node=col.json_node.setdefault(
                    "MinValueVec", col.min_vec.to_json_vec()
                ),
            )
            buckets.setdefault(key, []).append(occ)

        if col.max_vec:
            key = _quantize_color(col.max_vec)
            occ = ColorOccurrence(
                key=key,
                asset_path=col.asset_path,
                entry_index=col.entry_index,
                name=col.name,
                role="MAX",
                rgb=col.max_vec,
                json_vec_node=col.json_node.setdefault(
                    "MaxValueVec", col.max_vec.to_json_vec()
                ),
            )
            buckets.setdefault(key, []).append(occ)

    groups = [ColorGroup(key=k, occurrences=v) for k, v in buckets.items()]
    groups.sort(key=lambda g: g.count, reverse=True)
    return groups


def apply_group_color(group: ColorGroup, new_rgb: RGB) -> None:
    new_key = _quantize_color(new_rgb)
    for occ in group.occurrences:
        occ.rgb.r = float(new_rgb.r)
        occ.rgb.g = float(new_rgb.g)
        occ.rgb.b = float(new_rgb.b)
        occ.json_vec_node["X"] = float(new_rgb.r)
        occ.json_vec_node["Y"] = float(new_rgb.g)
        occ.json_vec_node["Z"] = float(new_rgb.b)
        occ.key = new_key
    group.key = new_key


def export_uasset_to_json(uasset_path: str, uejson_exe: str = "UEJSON.exe") -> str:
    if not os.path.isfile(uasset_path):
        raise FileNotFoundError(uasset_path)
    subprocess.run([uejson_exe, "-e", uasset_path], check=True)
    json_path = os.path.splitext(uasset_path)[0] + ".json"
    if not os.path.isfile(json_path):
        raise FileNotFoundError(json_path)
    return json_path


def import_json_to_uasset(json_path: str, uejson_exe: str = "UEJSON.exe") -> str:
    if not os.path.isfile(json_path):
        raise FileNotFoundError(json_path)
    subprocess.run([uejson_exe, "-i", json_path], check=True)
    uasset_path = os.path.splitext(json_path)[0] + ".uasset"
    if not os.path.isfile(uasset_path):
        raise FileNotFoundError(uasset_path)
    return uasset_path


def scan_assets_for_color_over_life(
    uasset_paths: Sequence[str],
    uejson_exe: str = "UEJSON.exe",
):
    json_paths: List[str] = []
    all_json_roots: Dict[str, Any] = {}
    all_colors: List[ColorOverLife] = []

    for p in uasset_paths:
        if not p:
            continue

        json_path = export_uasset_to_json(p, uejson_exe)
        json_paths.append(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            root = json.load(f)

        all_json_roots[json_path] = root

        exports = root.get("Exports") if isinstance(root, dict) else root
        cols = extract_color_over_life_list(asset_path=p, json_root=exports)
        all_colors.extend(cols)

    groups = build_color_groups(all_colors)
    return json_paths, all_json_roots, all_colors, groups


def write_back_jsons(json_roots: Mapping[str, Any]) -> None:
    for path, root in json_roots.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(root, f, ensure_ascii=False, indent=2)


def rebuild_uassets_from_jsons(
    json_paths: Sequence[str],
    uejson_exe: str = "UEJSON.exe",
) -> List[str]:
    result: List[str] = []
    for p in json_paths:
        result.append(import_json_to_uasset(p, uejson_exe))
    return result
