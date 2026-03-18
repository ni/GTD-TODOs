"""Core domain models for projects and tasks."""

from datetime import UTC, date, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TaskStatus(str, Enum):
    INBOX = "inbox"
    NEXT_ACTION = "next_action"
    WAITING_FOR = "waiting_for"
    SCHEDULED = "scheduled"
    SOMEDAY_MAYBE = "someday_maybe"
    DONE = "done"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]


_STATUS_LABELS: dict[TaskStatus, str] = {
    TaskStatus.INBOX: "Inbox",
    TaskStatus.NEXT_ACTION: "Next Action",
    TaskStatus.WAITING_FOR: "Waiting For",
    TaskStatus.SCHEDULED: "Scheduled",
    TaskStatus.SOMEDAY_MAYBE: "Someday / Maybe",
    TaskStatus.DONE: "Done",
}


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    INTERVAL_DAYS = "interval_days"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
    notes: str | None = None
    due_date: date | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    archived_at: datetime | None = None
    completed_at: datetime | None = None


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    notes: str | None = None
    status: TaskStatus = Field(default=TaskStatus.INBOX, index=True)
    due_date: date | None = Field(default=None, index=True)
    is_recurring: bool = Field(default=False, index=True)
    recurrence_type: RecurrenceType | None = None
    recurrence_interval_days: int | None = None
    last_completed_at: datetime | None = None
    project_id: int | None = Field(default=None, foreign_key="projects.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    completed_at: datetime | None = None