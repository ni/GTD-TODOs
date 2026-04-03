"""Project CRUD operations."""

from datetime import UTC, date, datetime

from sqlmodel import Session, func, select

from app.models import Project, Task, TaskStatus

_UNSET = object()


def create_project(
    session: Session,
    *,
    name: str,
    description: str | None = None,
    notes: str | None = None,
    due_date: date | None = None,
) -> Project:
    now = datetime.now(UTC)
    project = Project(
        name=name,
        description=description,
        notes=notes,
        due_date=due_date,
        created_at=now,
        updated_at=now,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: int) -> Project | None:
    return session.get(Project, project_id)


def list_projects(
    session: Session,
    *,
    include_archived: bool = False,
    include_completed: bool = False,
    has_due_date: bool | None = None,
) -> list[Project]:
    stmt = select(Project)
    if not include_archived:
        stmt = stmt.where(Project.archived_at.is_(None))  # type: ignore[union-attr]
    if not include_completed:
        stmt = stmt.where(Project.completed_at.is_(None))  # type: ignore[union-attr]
    if has_due_date is True:
        stmt = stmt.where(Project.due_date.is_not(None))  # type: ignore[union-attr]
    elif has_due_date is False:
        stmt = stmt.where(Project.due_date.is_(None))  # type: ignore[union-attr]
    stmt = stmt.order_by(Project.name)
    return session.exec(stmt).all()  # type: ignore[return-value]


def update_project(
    session: Session,
    project_id: int,
    *,
    name: str | None = None,
    description: object = _UNSET,
    notes: object = _UNSET,
    due_date: object = _UNSET,
) -> Project | None:
    project = session.get(Project, project_id)
    if project is None:
        return None
    if name is not None:
        project.name = name
    if description is not _UNSET:
        project.description = description  # type: ignore[assignment]
    if notes is not _UNSET:
        project.notes = notes  # type: ignore[assignment]
    if due_date is not _UNSET:
        project.due_date = due_date  # type: ignore[assignment]
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def archive_project(session: Session, project_id: int) -> Project | None:
    project = session.get(Project, project_id)
    if project is None:
        return None
    project.archived_at = datetime.now(UTC)
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project_task_counts(
    session: Session, project_id: int
) -> dict[str, int]:
    """Return open and due-today task counts for a project."""
    today = date.today()
    open_count = session.exec(
        select(func.count())
        .select_from(Task)
        .where(Task.project_id == project_id)
        .where(Task.status != TaskStatus.DONE)
    ).one()
    due_today_count = session.exec(
        select(func.count())
        .select_from(Task)
        .where(Task.project_id == project_id)
        .where(Task.due_date == today)
        .where(Task.status != TaskStatus.DONE)
    ).one()
    return {"open": int(open_count), "due_today": int(due_today_count)}


def can_complete_project(session: Session, project_id: int) -> bool:
    """Return True when every task under the project is done (or there are none)."""
    open_count = session.exec(
        select(func.count())
        .select_from(Task)
        .where(Task.project_id == project_id)
        .where(Task.status != TaskStatus.DONE)
    ).one()
    return int(open_count) == 0


def complete_project(session: Session, project_id: int) -> Project | None:
    """Mark a project complete if all its tasks are done."""
    project = session.get(Project, project_id)
    if project is None:
        return None
    if not can_complete_project(session, project_id):
        return None
    now = datetime.now(UTC)
    project.completed_at = now
    project.updated_at = now
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def count_overdue_projects(session: Session) -> int:
    """Count non-archived, non-completed projects whose due_date is past."""
    today = date.today()
    count = session.exec(
        select(func.count())
        .select_from(Project)
        .where(Project.due_date < today)  # type: ignore[operator]
        .where(Project.archived_at.is_(None))  # type: ignore[union-attr]
        .where(Project.completed_at.is_(None))  # type: ignore[union-attr]
    ).one()
    return int(count)
