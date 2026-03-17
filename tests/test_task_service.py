"""Tests for task CRUD service operations and recurrence logic."""

from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session

from app.models import RecurrenceType, TaskStatus
from app.services.project_service import create_project
from app.services.task_service import (
    complete_task,
    create_task,
    get_task,
    list_tasks,
    reopen_task,
    update_task,
)

# --- Creation ---


def test_create_task_defaults_to_inbox(db_session: Session) -> None:
    task = create_task(db_session, title="Buy milk")

    assert task.id is not None
    assert task.title == "Buy milk"
    assert task.status == TaskStatus.INBOX
    assert task.due_date is None
    assert task.is_recurring is False
    assert task.notes is None


def test_create_task_with_all_fields(db_session: Session) -> None:
    project = create_project(db_session, name="Chores")
    task = create_task(
        db_session,
        title="Water plants",
        notes="# Reminder\nDon't forget the fern.",
        status=TaskStatus.SCHEDULED,
        due_date=date(2026, 3, 20),
        is_recurring=True,
        recurrence_type=RecurrenceType.WEEKLY,
        project_id=project.id,
    )

    assert task.title == "Water plants"
    assert task.notes == "# Reminder\nDon't forget the fern."
    assert task.status == TaskStatus.SCHEDULED
    assert task.due_date == date(2026, 3, 20)
    assert task.is_recurring is True
    assert task.recurrence_type == RecurrenceType.WEEKLY
    assert task.project_id == project.id


def test_create_task_with_interval_days(db_session: Session) -> None:
    task = create_task(
        db_session,
        title="Deep clean",
        is_recurring=True,
        recurrence_type=RecurrenceType.INTERVAL_DAYS,
        recurrence_interval_days=14,
        due_date=date(2026, 4, 1),
    )

    assert task.recurrence_type == RecurrenceType.INTERVAL_DAYS
    assert task.recurrence_interval_days == 14


# --- Retrieval ---


def test_get_task(db_session: Session) -> None:
    created = create_task(db_session, title="Find me")

    found = get_task(db_session, created.id)  # type: ignore[arg-type]

    assert found is not None
    assert found.id == created.id


def test_get_task_not_found(db_session: Session) -> None:
    assert get_task(db_session, 9999) is None


def test_list_tasks_all(db_session: Session) -> None:
    create_task(db_session, title="Task A")
    create_task(db_session, title="Task B")

    tasks = list_tasks(db_session)

    assert len(tasks) == 2


def test_list_tasks_by_status(db_session: Session) -> None:
    create_task(db_session, title="Inbox item")
    create_task(db_session, title="Scheduled item", status=TaskStatus.SCHEDULED)

    inbox_tasks = list_tasks(db_session, status=TaskStatus.INBOX)

    assert len(inbox_tasks) == 1
    assert inbox_tasks[0].title == "Inbox item"


def test_list_tasks_by_project(db_session: Session) -> None:
    project = create_project(db_session, name="Work")
    create_task(db_session, title="In project", project_id=project.id)
    create_task(db_session, title="No project")

    project_tasks = list_tasks(db_session, project_id=project.id)

    assert len(project_tasks) == 1
    assert project_tasks[0].title == "In project"


# --- Update ---


def test_update_task(db_session: Session) -> None:
    task = create_task(db_session, title="Old title")

    updated = update_task(
        db_session,
        task.id,  # type: ignore[arg-type]
        title="New title",
        notes="Some notes",
        status=TaskStatus.NEXT_ACTION,
        due_date=date(2026, 5, 1),
    )

    assert updated is not None
    assert updated.title == "New title"
    assert updated.notes == "Some notes"
    assert updated.status == TaskStatus.NEXT_ACTION
    assert updated.due_date == date(2026, 5, 1)


def test_update_task_assign_project(db_session: Session) -> None:
    project = create_project(db_session, name="Assigned")
    task = create_task(db_session, title="Orphan")

    updated = update_task(db_session, task.id, project_id=project.id)  # type: ignore[arg-type]

    assert updated is not None
    assert updated.project_id == project.id


def test_update_task_not_found(db_session: Session) -> None:
    assert update_task(db_session, 9999, title="Ghost") is None


def test_update_task_preserves_markdown_notes(db_session: Session) -> None:
    md = "## Heading\n\n- item 1\n- item 2\n\n```python\nprint('hi')\n```"
    task = create_task(db_session, title="With MD", notes=md)

    found = get_task(db_session, task.id)  # type: ignore[arg-type]

    assert found is not None
    assert found.notes == md


# --- Completion (non-recurring) ---


def test_complete_non_recurring_task(db_session: Session) -> None:
    task = create_task(db_session, title="One-shot")

    completed = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert completed is not None
    assert completed.status == TaskStatus.DONE
    assert completed.completed_at is not None


def test_complete_non_recurring_task_sets_completed_at(db_session: Session) -> None:
    task = create_task(db_session, title="Timestamped")

    before = datetime.now(UTC).replace(tzinfo=None)
    completed = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert completed is not None
    assert completed.completed_at is not None
    assert completed.completed_at >= before


# --- Completion (recurring) ---


def test_complete_daily_recurring_task_advances_due_date(db_session: Session) -> None:
    task = create_task(
        db_session,
        title="Daily standup",
        is_recurring=True,
        recurrence_type=RecurrenceType.DAILY,
        due_date=date(2026, 3, 17),
        status=TaskStatus.NEXT_ACTION,
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.due_date == date(2026, 3, 18)
    assert result.status != TaskStatus.DONE
    assert result.last_completed_at is not None
    assert result.completed_at is None  # not permanently closed


def test_complete_weekly_recurring_task_advances_due_date(db_session: Session) -> None:
    task = create_task(
        db_session,
        title="Weekly review",
        is_recurring=True,
        recurrence_type=RecurrenceType.WEEKLY,
        due_date=date(2026, 3, 17),
        status=TaskStatus.SCHEDULED,
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.due_date == date(2026, 3, 24)


def test_complete_monthly_recurring_task_advances_due_date(db_session: Session) -> None:
    task = create_task(
        db_session,
        title="Monthly report",
        is_recurring=True,
        recurrence_type=RecurrenceType.MONTHLY,
        due_date=date(2026, 1, 31),
        status=TaskStatus.SCHEDULED,
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.due_date == date(2026, 2, 28)


def test_complete_interval_days_recurring_task_advances_due_date(
    db_session: Session,
) -> None:
    task = create_task(
        db_session,
        title="Biweekly deep clean",
        is_recurring=True,
        recurrence_type=RecurrenceType.INTERVAL_DAYS,
        recurrence_interval_days=14,
        due_date=date(2026, 3, 1),
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.due_date == date(2026, 3, 15)


def test_complete_recurring_task_preserves_recurrence_settings(
    db_session: Session,
) -> None:
    task = create_task(
        db_session,
        title="Keep settings",
        is_recurring=True,
        recurrence_type=RecurrenceType.WEEKLY,
        recurrence_interval_days=None,
        due_date=date(2026, 3, 17),
        notes="Important notes",
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    assert result.is_recurring is True
    assert result.recurrence_type == RecurrenceType.WEEKLY
    assert result.notes == "Important notes"
    assert result.id == task.id  # same record


def test_complete_recurring_task_without_due_date_sets_from_today(
    db_session: Session,
) -> None:
    task = create_task(
        db_session,
        title="No date recurring",
        is_recurring=True,
        recurrence_type=RecurrenceType.DAILY,
        due_date=None,
    )

    result = complete_task(db_session, task.id)  # type: ignore[arg-type]

    assert result is not None
    today = date.today()
    assert result.due_date == today + timedelta(days=1)


# --- Reopen ---


def test_reopen_done_task(db_session: Session) -> None:
    task = create_task(db_session, title="Reopen me")
    complete_task(db_session, task.id)  # type: ignore[arg-type]

    reopened = reopen_task(db_session, task.id)  # type: ignore[arg-type]

    assert reopened is not None
    assert reopened.status == TaskStatus.INBOX
    assert reopened.completed_at is None


def test_reopen_task_not_found(db_session: Session) -> None:
    assert reopen_task(db_session, 9999) is None


# --- Due date persistence ---


def test_due_date_persists_correctly(db_session: Session) -> None:
    target_date = date(2026, 12, 25)
    task = create_task(db_session, title="Christmas", due_date=target_date)

    found = get_task(db_session, task.id)  # type: ignore[arg-type]

    assert found is not None
    assert found.due_date == target_date


# --- Project linking ---


def test_task_linked_to_project(db_session: Session) -> None:
    project = create_project(db_session, name="Link target")
    task = create_task(db_session, title="Linked", project_id=project.id)

    found = get_task(db_session, task.id)  # type: ignore[arg-type]

    assert found is not None
    assert found.project_id == project.id
