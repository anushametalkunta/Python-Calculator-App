# calculator/storage.py
# Saving and loading the history and the settings (as small JSON files).

from __future__ import annotations

import json
import os
from pathlib import Path

MAX_HISTORY = 100  # we keep only the newest 100 calculations


def get_data_folder() -> Path:
    """The folder where the calculator keeps its saved files."""
    appdata = os.environ.get("APPDATA")  # on Windows: ...\AppData\Roaming
    if appdata:
        return Path(appdata) / "CalculatorApp"
    return Path.home() / ".calculator_app"


DATA_FOLDER = get_data_folder()
HISTORY_FILE = DATA_FOLDER / "history.json"
SETTINGS_FILE = DATA_FOLDER / "settings.json"


def _read_json(path: Path):
    """Read a JSON file. Returns None if it is missing or damaged."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return None


def _write_json(path: Path, data) -> None:
    """Write data to a JSON file. If saving fails, the calculator still works."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError:
        pass


def load_history(path: Path = HISTORY_FILE) -> list[str]:
    """Read the saved history. Returns an empty list if there is none."""
    data = _read_json(path)
    if not isinstance(data, list):
        return []
    good_entries = [
        item for item in data
        if isinstance(item, str) and " = " in item
    ]
    return good_entries[-MAX_HISTORY:]


def save_history(history: list[str], path: Path = HISTORY_FILE) -> None:
    """Save the history (only the newest MAX_HISTORY entries)."""
    _write_json(path, history[-MAX_HISTORY:])


def load_settings(path: Path = SETTINGS_FILE) -> dict:
    """Read the saved settings (like the theme). Returns {} if there are none."""
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def save_settings(settings: dict, path: Path = SETTINGS_FILE) -> None:
    """Save the settings."""
    _write_json(path, settings)