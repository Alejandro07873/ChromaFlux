import os
import subprocess

from core.json_reader import load_color_over_life_from_json
from core.json_writer import apply_color_groups_to_json
from core.resource_path import resource_path

# =====================================================
# 🔒 Evitar ventanas CMD en Windows
# =====================================================
CREATE_NO_WINDOW = 0x08000000


class AssetPipeline:
    def __init__(self):
        self.uejson_path = resource_path(
            os.path.join("tools", "UEJSON.exe")
        )

        if not os.path.exists(self.uejson_path):
            raise FileNotFoundError(self.uejson_path)

    # =====================================================
    # 🔹 UASSET → JSON (sin ventana CMD)
    # =====================================================
    def convert_uasset_to_json(self, uasset_path: str) -> str:
        if not os.path.exists(uasset_path):
            raise FileNotFoundError(uasset_path)

        subprocess.run(
            [self.uejson_path, "-e", uasset_path],
            check=True,
            creationflags=CREATE_NO_WINDOW
        )

        json_path = os.path.splitext(uasset_path)[0] + ".json"
        if not os.path.exists(json_path):
            raise FileNotFoundError(json_path)

        return json_path

    # =====================================================
    # 🔹 JSON → UASSET (sin ventana CMD)
    # =====================================================
    def convert_json_to_uasset(self, json_path: str) -> str:
        if not os.path.exists(json_path):
            raise FileNotFoundError(json_path)

        subprocess.run(
            [self.uejson_path, "-i", json_path],
            check=True,
            creationflags=CREATE_NO_WINDOW
        )

        return os.path.splitext(json_path)[0] + ".uasset"

    # =====================================================
    # 🔹 Cargar datos de color
    # =====================================================
    def load_color_data(self, json_path):
        return load_color_over_life_from_json(json_path)

    # =====================================================
    # 🔹 Procesar grupo de assets
    # =====================================================
    def process_asset_group_edit(
        self,
        original_uasset: str,
        entries,
        new_rgb
    ) -> str:
        json_path = self.convert_uasset_to_json(original_uasset)

        apply_color_groups_to_json(
            json_path=json_path,
            entries=entries,
            new_rgb=new_rgb
        )

        return self.convert_json_to_uasset(json_path)

    # =====================================================
    # 🔹 UNDO SUPPORT
    # =====================================================
    def backup_uasset(self, uasset_path: str) -> bytes:
        """
        Devuelve una copia binaria completa del .uasset
        """
        if not os.path.exists(uasset_path):
            raise FileNotFoundError(uasset_path)

        with open(uasset_path, "rb") as f:
            return f.read()

    def restore_uasset(self, uasset_path: str, data: bytes):
        """
        Restaura un .uasset desde una copia binaria
        """
        with open(uasset_path, "wb") as f:
            f.write(data)
