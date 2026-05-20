"""Course persistence and business logic."""

from __future__ import annotations

from pathlib import Path

from utils import auto_save, load_json_list, require_non_empty, save_json_list


class CourseManager:
    """Manages course names stored in JSON."""

    def __init__(self, file_path: str | Path = "courses.json") -> None:
        self._path = Path(file_path)
        self._courses: list[str] = []
        self.load()

    @property
    def courses(self) -> list[str]:
        return list(self._courses)

    def load(self) -> None:
        raw = load_json_list(self._path)
        self._courses = sorted({str(name).strip() for name in raw if str(name).strip()})

    def _save(self) -> None:
        save_json_list(self._path, self._courses)

    @require_non_empty("name")
    @auto_save()
    def add_course(self, name: str) -> None:
        cleaned = name.strip()
        if cleaned in self._courses:
            raise ValueError(f"Course '{cleaned}' already exists.")
        self._courses.append(cleaned)
        self._courses.sort()

    @require_non_empty("new_name")
    @auto_save()
    def edit_course(self, old_name: str, new_name: str) -> None:
        old_clean = old_name.strip()
        new_clean = new_name.strip()
        if old_clean not in self._courses:
            raise ValueError(f"Course '{old_clean}' not found.")
        if new_clean != old_clean and new_clean in self._courses:
            raise ValueError(f"Course '{new_clean}' already exists.")
        index = self._courses.index(old_clean)
        self._courses[index] = new_clean
        self._courses.sort()

    @auto_save()
    def delete_course(self, name: str) -> None:
        cleaned = name.strip()
        if cleaned not in self._courses:
            raise ValueError(f"Course '{cleaned}' not found.")
        self._courses.remove(cleaned)

    def count(self) -> int:
        return len(self._courses)

    def has_course(self, name: str) -> bool:
        return name.strip() in self._courses
