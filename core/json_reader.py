import json
from typing import Any, List, Tuple
from core.data_models import ColorEntry


def _as_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def load_color_over_life_from_root(
    json_path: str,
    data: Any
) -> Tuple[List[ColorEntry], List[ColorEntry]]:

    min_entries: List[ColorEntry] = []
    max_entries: List[ColorEntry] = []

    exports = data.get("Exports", []) if isinstance(data, dict) else []

    for export in exports:
        name = export.get("ObjectName", "")
        data_block = export.get("Data", [])

        # =========================================================
        # 1) ParticleModuleColorOverLife
        # =========================================================
        if name.startswith("ParticleModuleColorOverLife"):
            for prop in data_block:
                if prop.get("Name") != "ColorOverLife":
                    continue

                values = prop.get("Value", [])
                min_ref = None
                max_ref = None

                for item in values:
                    if item.get("Name") == "MinValueVec":
                        min_ref = item["Value"][0]["Value"]
                    elif item.get("Name") == "MaxValueVec":
                        max_ref = item["Value"][0]["Value"]

                if isinstance(min_ref, dict):
                    min_entries.append(
                        ColorEntry(
                            asset=json_path,
                            module=name,
                            mode="MIN",
                            r=_as_float(min_ref.get("X")),
                            g=_as_float(min_ref.get("Y")),
                            b=_as_float(min_ref.get("Z")),
                            raw_ref=min_ref,
                        )
                    )

                if isinstance(max_ref, dict):
                    max_entries.append(
                        ColorEntry(
                            asset=json_path,
                            module=name,
                            mode="MAX",
                            r=_as_float(max_ref.get("X")),
                            g=_as_float(max_ref.get("Y")),
                            b=_as_float(max_ref.get("Z")),
                            raw_ref=max_ref,
                        )
                    )

        # =========================================================
        # 2) ParticleModuleColor (INITIAL / START COLOR)
        # =========================================================
        elif name.startswith("ParticleModuleColor"):
            for prop in data_block:
                if prop.get("Name") != "StartColor":
                    continue

                values = prop.get("Value", [])
                min_ref = None
                max_ref = None

                for item in values:
                    if item.get("Name") == "MinValueVec":
                        min_ref = item["Value"][0]["Value"]
                    elif item.get("Name") == "MaxValueVec":
                        max_ref = item["Value"][0]["Value"]

                # Min Value Vector
                if isinstance(min_ref, dict):
                    min_entries.append(
                        ColorEntry(
                            asset=json_path,
                            module=name,
                            mode="MIN",
                            r=_as_float(min_ref.get("X")),
                            g=_as_float(min_ref.get("Y")),
                            b=_as_float(min_ref.get("Z")),
                            raw_ref=min_ref,
                        )
                    )

                # Max Value Vector
                if isinstance(max_ref, dict):
                    max_entries.append(
                        ColorEntry(
                            asset=json_path,
                            module=name,
                            mode="MAX",
                            r=_as_float(max_ref.get("X")),
                            g=_as_float(max_ref.get("Y")),
                            b=_as_float(max_ref.get("Z")),
                            raw_ref=max_ref,
                        )
                    )

    return min_entries, max_entries


def load_color_over_life_from_json(
    json_path: str
) -> Tuple[List[ColorEntry], List[ColorEntry]]:

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return load_color_over_life_from_root(json_path, data)
