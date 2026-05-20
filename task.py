"""Task domain model."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


TASK_TYPES = ("Homework", "Project", "Exam")
STATUSES = ("Pending", "Completed", "Overdue")


@dataclass
class Task:
    """Represents a single student task."""

    title: str
    course: str
    deadline: str
    task_type: str
    status: str = "Pending"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        self.refresh_status()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            title=data["title"],
            course=data["course"],
            deadline=data["deadline"],
            task_type=data["task_type"],
            status=data.get("status", "Pending"),
            id=data.get("id", str(uuid.uuid4())),
        )

    def mark_completed(self) -> None:
        self.status = "Completed"

    def mark_pending(self) -> None:
        self.status = "Pending"
        self.refresh_status()

    def refresh_status(self, today: date | None = None) -> None:
        """Keep pending tasks marked overdue after their deadline passes."""
        if self.status == "Completed":
            return
        today = today or date.today()
        self.status = "Overdue" if self.deadline_date < today else "Pending"

    @property
    def deadline_date(self) -> date:
        return datetime.strptime(self.deadline, "%Y-%m-%d").date()

    def days_until_deadline(self, today: date | None = None) -> int:
        today = today or date.today()
        return (self.deadline_date - today).days

    @property
    def is_completed(self) -> bool:
        return self.status == "Completed"

    @property
    def is_pending(self) -> bool:
        return self.status == "Pending"

    @property
    def is_overdue(self) -> bool:
        return self.status == "Overdue"
