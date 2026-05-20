"""Shared utilities: decorators, validation, and generators."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, TypeVar

from task import Task


T = TypeVar("T")

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_date(date_str: str) -> bool:
    """Return True if date_str is YYYY-MM-DD and a real calendar date."""
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_deadline(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator: ensure deadline keyword argument is a valid YYYY-MM-DD date."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        bound = signature(func).bind_partial(*args, **kwargs)
        deadline = bound.arguments.get("deadline")
        if deadline is not None and not is_valid_date(str(deadline)):
            raise ValueError("Deadline must be a valid date in YYYY-MM-DD format.")
        return func(*args, **kwargs)

    return wrapper


def require_non_empty(field_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory: reject empty string values for a named field."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            bound = signature(func).bind_partial(*args, **kwargs)
            value = bound.arguments.get(field_name)
            if value is None or not str(value).strip():
                raise ValueError(f"{field_name.replace('_', ' ').title()} cannot be empty.")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def auto_save(save_method_name: str = "_save") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: call instance save method after successful mutation."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
            result = func(self, *args, **kwargs)
            save_fn = getattr(self, save_method_name, None)
            if callable(save_fn):
                save_fn()
            return result

        return wrapper

    return decorator


def load_json_list(path: Path) -> list[Any]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def save_json_list(path: Path, data: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def iter_by_status(tasks: Iterable[Task], status: str | None = None) -> Generator[Task, None, None]:
    """Yield tasks filtered by status (or all if status is None)."""
    for task in tasks:
        if status is None or task.status == status:
            yield task


def iter_sorted_by_deadline(tasks: Iterable[Task], pending_only: bool = False) -> Generator[Task, None, None]:
    """Yield tasks sorted by nearest deadline first."""
    filtered = [t for t in tasks if not pending_only or t.is_pending]
    for task in sorted(filtered, key=lambda t: t.deadline_date):
        yield task


def iter_search(tasks: Iterable[Task], query: str) -> Generator[Task, None, None]:
    """Yield tasks whose title, course, type, or status matches query."""
    needle = query.strip().lower()
    if not needle:
        return
    for task in tasks:
        searchable = (
            task.title.lower(),
            task.course.lower(),
            task.task_type.lower(),
            task.status.lower(),
        )
        if any(needle in value for value in searchable):
            yield task


def deadline_human_label(task: Task) -> str:
    """Return friendly remaining-time text for a task deadline."""
    days = task.days_until_deadline()
    if days == 0:
        return "Due today"
    if days == 1:
        return "Tomorrow"
    if days > 1:
        return f"{days} days left"
    overdue_days = abs(days)
    if overdue_days == 1:
        return "Overdue by 1 day"
    return f"Overdue by {overdue_days} days"
