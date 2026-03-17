"""Tests for project CRUD service operations."""

from datetime import datetime

from sqlmodel import Session

from app.services.project_service import (
    archive_project,
    create_project,
    get_project,
    list_projects,
    update_project,
)


def test_create_project(db_session: Session) -> None:
    project = create_project(db_session, name="My Project")

    assert project.id is not None
    assert project.name == "My Project"
    assert project.description is None
    assert project.created_at is not None
    assert project.updated_at is not None
    assert project.archived_at is None


def test_create_project_with_description(db_session: Session) -> None:
    project = create_project(
        db_session, name="Described", description="A useful project"
    )

    assert project.description == "A useful project"


def test_get_project(db_session: Session) -> None:
    created = create_project(db_session, name="Findable")

    found = get_project(db_session, created.id)  # type: ignore[arg-type]

    assert found is not None
    assert found.id == created.id
    assert found.name == "Findable"


def test_get_project_not_found(db_session: Session) -> None:
    result = get_project(db_session, 9999)

    assert result is None


def test_list_projects_returns_non_archived(db_session: Session) -> None:
    create_project(db_session, name="Active")
    archived = create_project(db_session, name="Old")
    archive_project(db_session, archived.id)  # type: ignore[arg-type]

    projects = list_projects(db_session)

    names = [p.name for p in projects]
    assert "Active" in names
    assert "Old" not in names


def test_list_projects_includes_archived_when_requested(db_session: Session) -> None:
    create_project(db_session, name="Active2")
    archived = create_project(db_session, name="Old2")
    archive_project(db_session, archived.id)  # type: ignore[arg-type]

    projects = list_projects(db_session, include_archived=True)

    names = [p.name for p in projects]
    assert "Active2" in names
    assert "Old2" in names


def test_update_project(db_session: Session) -> None:
    project = create_project(db_session, name="Original")
    original_updated_at = project.updated_at

    updated = update_project(
        db_session, project.id, name="Renamed", description="Now described"  # type: ignore[arg-type]
    )

    assert updated is not None
    assert updated.name == "Renamed"
    assert updated.description == "Now described"
    assert updated.updated_at >= original_updated_at


def test_update_project_not_found(db_session: Session) -> None:
    result = update_project(db_session, 9999, name="Ghost")

    assert result is None


def test_archive_project(db_session: Session) -> None:
    project = create_project(db_session, name="To Archive")

    archived = archive_project(db_session, project.id)  # type: ignore[arg-type]

    assert archived is not None
    assert archived.archived_at is not None
    assert isinstance(archived.archived_at, datetime)


def test_archive_project_not_found(db_session: Session) -> None:
    result = archive_project(db_session, 9999)

    assert result is None
