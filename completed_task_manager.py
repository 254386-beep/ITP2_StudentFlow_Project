"""Completed task history persistence and business logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Generator

from task import Task
from utils import auto_save, load_json_list, save_json_list


class CompletedTaskManager:
    """Manages completed tasks stored separately from active tasks."""

    def __init__(self, file_path: str | Path = "completed_tasks.json") -> None:
        self._path = Path(file_path)
        self._completed: list[dict[str, Any]] = []
        self.load()

    @property
    def completed_tasks(self) -> list[dict[str, Any]]:
        return list(self._completed)

    def load(self) -> None:
        raw = load_json_list(self._path)
        self._completed = [item for item in raw if isinstance(item, dict)]

    def _save(self) -> None:
        save_json_list(self._path, self._completed)

    @auto_save()
    def add_completed(self, task: Task, completed_date: str | None = None) -> None:
        task.mark_completed()
        data = task.to_dict()
        data["type"] = data.pop("task_type")
        data["completed_date"] = completed_date or date.today().isoformat()
        self._completed.append(data)
        self._completed.sort(key=lambda item: item.get("completed_date", ""), reverse=True)

    @auto_save()
    def delete_completed(self, task_id: str) -> None:
        task = self.get_completed(task_id)
        if task is None:
            raise ValueError("Completed task not found.")
        self._completed.remove(task)

    @auto_save()
    def pop_for_restore(self, task_id: str) -> Task:
        task_data = self.get_completed(task_id)
        if task_data is None:
            raise ValueError("Completed task not found.")
        self._completed.remove(task_data)
        restored = Task(
            title=str(task_data["title"]),
            course=str(task_data["course"]),
            deadline=str(task_data["deadline"]),
            task_type=str(task_data.get("type", task_data.get("task_type", "Homework"))),
            status="Pending",
            id=str(task_data["id"]),
        )
        restored.refresh_status()
        return restored

    def get_completed(self, task_id: str) -> dict[str, Any] | None:
        for task in self._completed:
            if task.get("id") == task_id:
                return task
        return None

    def count(self) -> int:
        return len(self._completed)

    def completed_this_week(self) -> int:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        total = 0
        for task in self._completed:
            try:
                completed = datetime.strptime(str(task.get("completed_date")), "%Y-%m-%d").date()
            except ValueError:
                continue
            if start <= completed <= today:
                total += 1
        return total

    def iter_completed(self) -> Generator[dict[str, Any], None, None]:
        for task in sorted(self._completed, key=lambda item: item.get("completed_date", ""), reverse=True):
            yield task
