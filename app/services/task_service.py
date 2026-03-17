"""Task CRUD operations and recurrence logic."""

from calendar import monthrange
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, select

from app.models import RecurrenceType, Task, TaskStatus


def create_task(
    session: Session,
    *,
    title: str,
    notes: str | None = None,
    status: TaskStatus = TaskStatus.INBOX,
    due_date: date | None = None,
    is_recurring: bool = False,
    recurrence_type: RecurrenceType | None = None,
    recurrence_interval_days: int | None = None,
    project_id: int | None = None,
) -> Task:
    now = datetime.now(UTC)
    task = Task(
        title=title,
        notes=notes,
        status=status,
        due_date=due_date,
        is_recurring=is_recurring,
        recurrence_type=recurrence_type,
        recurrence_interval_days=recurrence_interval_days,
        project_id=project_id,
        created_at=now,
        updated_at=now,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: int) -> Task | None:
    return session.get(Task, task_id)


def list_tasks(
    session: Session,
    *,
    status: TaskStatus | None = None,
    project_id: int | None = None,
) -> list[Task]:
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    stmt = stmt.order_by(Task.due_date, Task.created_at)  # type: ignore[arg-type]
    return list(session.exec(stmt).all())


def list_tasks_due_today(session: Session) -> list[Task]:
    """Return non-done tasks whose due_date equals today."""
    today = date.today()
    stmt = (
        select(Task)
        .where(Task.due_date == today)
        .where(Task.status != TaskStatus.DONE)
        .order_by(Task.created_at)  # type: ignore[arg-type]
    )
    return list(session.exec(stmt).all())


def list_tasks_overdue(session: Session) -> list[Task]:
    """Return non-done tasks whose due_date is before today."""
    today = date.today()
    stmt = (
        select(Task)
        .where(Task.due_date < today)  # type: ignore[operator]
        .where(Task.status != TaskStatus.DONE)
        .order_by(Task.due_date, Task.created_at)  # type: ignore[arg-type]
    )
    return list(session.exec(stmt).all())


def update_task(
    session: Session,
    task_id: int,
    *,
    title: str | None = None,
    notes: str | None = None,
    status: TaskStatus | None = None,
    due_date: date | None = None,
    is_recurring: bool | None = None,
    recurrence_type: RecurrenceType | None = None,
    recurrence_interval_days: int | None = None,
    project_id: int | None = None,
) -> Task | None:
    task = session.get(Task, task_id)
    if task is None:
        return None
    if title is not None:
        task.title = title
    if notes is not None:
        task.notes = notes
    if status is not None:
        task.status = status
    if due_date is not None:
        task.due_date = due_date
    if is_recurring is not None:
        task.is_recurring = is_recurring
    if recurrence_type is not None:
        task.recurrence_type = recurrence_type
    if recurrence_interval_days is not None:
        task.recurrence_interval_days = recurrence_interval_days
    if project_id is not None:
        task.project_id = project_id
    task.updated_at = datetime.now(UTC)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def _advance_due_date(
    current: date, recurrence_type: RecurrenceType, interval_days: int | None
) -> date:
    """Compute the next due date for a recurring task."""
    if recurrence_type == RecurrenceType.DAILY:
        return current + timedelta(days=1)
    if recurrence_type == RecurrenceType.WEEKLY:
        return current + timedelta(weeks=1)
    if recurrence_type == RecurrenceType.MONTHLY:
        year = current.year + (current.month // 12)
        month = (current.month % 12) + 1
        max_day = monthrange(year, month)[1]
        day = min(current.day, max_day)
        return date(year, month, day)
    if recurrence_type == RecurrenceType.INTERVAL_DAYS:
        return current + timedelta(days=interval_days or 1)
    return current + timedelta(days=1)


def complete_task(session: Session, task_id: int) -> Task | None:
    task = session.get(Task, task_id)
    if task is None:
        return None

    now = datetime.now(UTC)
    task.updated_at = now

    if task.is_recurring and task.recurrence_type is not None:
        base_date = task.due_date or date.today()
        task.due_date = _advance_due_date(
            base_date, task.recurrence_type, task.recurrence_interval_days
        )
        task.last_completed_at = now
        # Keep the task actionable — don't move to DONE
        if task.status == TaskStatus.DONE:
            task.status = TaskStatus.INBOX
    else:
        task.status = TaskStatus.DONE
        task.completed_at = now

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def reopen_task(session: Session, task_id: int) -> Task | None:
    task = session.get(Task, task_id)
    if task is None:
        return None
    task.status = TaskStatus.INBOX
    task.completed_at = None
    task.updated_at = datetime.now(UTC)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
