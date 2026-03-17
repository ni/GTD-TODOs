"""Project CRUD operations."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Project


def create_project(
    session: Session,
    *,
    name: str,
    description: str | None = None,
) -> Project:
    now = datetime.now(UTC)
    project = Project(name=name, description=description, created_at=now, updated_at=now)
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
) -> list[Project]:
    stmt = select(Project)
    if not include_archived:
        stmt = stmt.where(Project.archived_at.is_(None))  # type: ignore[union-attr]
    stmt = stmt.order_by(Project.name)
    return list(session.exec(stmt).all())


def update_project(
    session: Session,
    project_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Project | None:
    project = session.get(Project, project_id)
    if project is None:
        return None
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
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
