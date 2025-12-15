import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta correcta a un recurso tanto en desarrollo
    como cuando la app está empaquetada con PyInstaller.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
