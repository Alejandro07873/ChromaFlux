import json
import os

class I18N:
    def __init__(self, lang="es"):
        self.base_path = os.path.join(os.path.dirname(__file__), "..", "i18n")
        self.base_path = os.path.abspath(self.base_path)
        self.data = {}
        self.load(lang)

    def load(self, lang):
        path = os.path.join(self.base_path, f"{lang}.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Idioma no encontrado: {lang}")

        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.lang = lang

    def t(self, key, **kwargs):
        if key not in self.data:
            return f"⟨{key}⟩"

        text = self.data[key]
        try:
            return text.format(**kwargs)
        except Exception:
            return text

