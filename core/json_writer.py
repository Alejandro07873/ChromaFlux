import json
import os
from typing import Iterable, Tuple

from core.data_models import ColorEntry


def apply_color_groups_to_json(
    json_path: str,
    entries: Iterable[ColorEntry],
    new_rgb: Tuple[float, float, float]
) -> bool:

    if not os.path.exists(json_path):
        raise FileNotFoundError(json_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nr, ng, nb = float(new_rgb[0]), float(new_rgb[1]), float(new_rgb[2])

    for entry in entries:
        ref = entry.raw_ref
        if not isinstance(ref, dict):
            continue

        ref["X"] = nr
        ref["Y"] = ng
        ref["Z"] = nb

        entry.r = nr
        entry.g = ng
        entry.b = nb

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return True
