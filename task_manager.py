"""Task persistence and business logic."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from task import TASK_TYPES, Task
from utils import (
    auto_save,
    iter_by_status,
    iter_search,
    iter_sorted_by_deadline,
    load_json_list,
    require_non_empty,
    save_json_list,
    validate_deadline,
)


class TaskManager:
    """Manages tasks stored in JSON."""

    def __init__(self, file_path: str | Path = "tasks.json") -> None:
        self._path = Path(file_path)
        self._tasks: list[Task] = []
        self.load()

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks)

    def load(self) -> None:
        raw = load_json_list(self._path)
        self._tasks = [Task.from_dict(item) for item in raw]
        self.refresh_statuses(save=False)

    def _save(self) -> None:
        save_json_list(self._path, [task.to_dict() for task in self._tasks])

    @require_non_empty("title")
    @validate_deadline
    @auto_save()
    def add_task(
        self,
        title: str,
        course: str,
        deadline: str,
        task_type: str,
    ) -> Task:
        if task_type not in TASK_TYPES:
            raise ValueError(f"Task type must be one of: {', '.join(TASK_TYPES)}")
        task = Task(
            title=title.strip(),
            course=course.strip(),
            deadline=deadline.strip(),
            task_type=task_type,
        )
        task.refresh_status()
        self._tasks.append(task)
        return task

    @auto_save()
    def complete_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")
        task.mark_completed()
        self._tasks.remove(task)
        return task

    @auto_save()
    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        if task is None:
            raise ValueError("Task not found.")
        self._tasks.remove(task)

    def get_task(self, task_id: str) -> Task | None:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def search(self, query: str) -> list[Task]:
        self.refresh_statuses(save=False)
        return list(iter_search(self._tasks, query))

    def tasks_by_deadline(self, pending_only: bool = True) -> list[Task]:
        self.refresh_statuses(save=False)
        return list(iter_sorted_by_deadline(self._tasks, pending_only=pending_only))

    def filtered_tasks(self, filter_name: str = "All", query: str = "") -> list[Task]:
        self.refresh_statuses(save=False)
        tasks = list(iter_search(self._tasks, query)) if query.strip() else list(self._tasks)
        if filter_name in TASK_TYPES:
            tasks = [task for task in tasks if task.task_type == filter_name]
        elif filter_name in {"Pending", "Overdue"}:
            tasks = [task for task in tasks if task.status == filter_name]
        return sorted(tasks, key=lambda task: task.deadline_date)

    @auto_save()
    def restore_task(self, task: Task) -> None:
        task.mark_pending()
        self._tasks.append(task)

    @auto_save()
    def extract_completed_tasks(self) -> list[Task]:
        completed = [task for task in self._tasks if task.is_completed]
        for task in completed:
            self._tasks.remove(task)
        return completed

    def count_total(self) -> int:
        return len(self._tasks)

    def count_completed(self) -> int:
        return sum(1 for _ in iter_by_status(self._tasks, "Completed"))

    def count_pending(self) -> int:
        return sum(1 for _ in iter_by_status(self._tasks, "Pending"))

    def count_overdue(self) -> int:
        return sum(1 for _ in iter_by_status(self._tasks, "Overdue"))

    def statistics(self) -> dict[str, int]:
        self.refresh_statuses(save=False)
        total = self.count_total()
        completed = self.count_completed()
        pending = self.count_pending()
        overdue = self.count_overdue()
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "completion_rate": round((completed / total) * 100) if total else 0,
        }

    def iter_tasks(self) -> Generator[Task, None, None]:
        """Generator over active tasks."""
        self.refresh_statuses(save=False)
        for task in self._tasks:
            yield task

    def count_by_course(self, course_name: str) -> int:
        self.refresh_statuses(save=False)
        return sum(1 for task in self._tasks if task.course == course_name)

    def next_deadline(self) -> Task | None:
        for task in self.tasks_by_deadline(pending_only=True):
            return task
        return None

    def tasks_due_within(self, days: int) -> list[Task]:
        self.refresh_statuses(save=False)
        return [
            task
            for task in self._tasks
            if not task.is_completed and 0 <= task.days_until_deadline() <= days
        ]

    def refresh_statuses(self, save: bool = True) -> None:
        changed = False
        for task in self._tasks:
            before = task.status
            task.refresh_status()
            changed = changed or before != task.status
        if changed and save:
            self._save()

    def rename_course_in_tasks(self, old_name: str, new_name: str) -> None:
        changed = False
        for task in self._tasks:
            if task.course == old_name:
                task.course = new_name
                changed = True
        if changed:
            self._save()

    def remove_course_from_tasks(self, course_name: str) -> None:
        changed = False
        for task in self._tasks:
            if task.course == course_name:
                task.course = "Unassigned"
                changed = True
        if changed:
            self._save()
