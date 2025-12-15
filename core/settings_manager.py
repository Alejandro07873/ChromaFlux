import json
import os


def get_appdata_dir(app_name="ChromaFlux") -> str:
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path


class SettingsManager:
    def __init__(self, app_name="ChromaFlux"):
        self.path = os.path.join(
            get_appdata_dir(app_name),
            "settings.json"
        )

        self.data = {}

        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
