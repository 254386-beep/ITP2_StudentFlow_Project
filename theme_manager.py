"""Theme preference persistence."""

from __future__ import annotations

import json
from pathlib import Path


class ThemeManager:
    """Stores and loads the user's Light/Dark appearance preference."""

    def __init__(self, file_path: str | Path = "settings.json") -> None:
        self._path = Path(file_path)

    def load_theme(self) -> str:
        if not self._path.exists():
            return "dark"
        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return "dark"
        theme = str(data.get("theme", "dark")).lower()
        return theme if theme in {"dark", "light"} else "dark"

    def save_theme(self, theme: str) -> None:
        cleaned = theme.lower()
        if cleaned not in {"dark", "light"}:
            raise ValueError("Theme must be 'dark' or 'light'.")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as file:
            json.dump({"theme": cleaned}, file, indent=2)
