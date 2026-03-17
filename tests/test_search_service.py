"""Service-level tests for task search and filtering."""

from datetime import date

from sqlmodel import Session

from app.models import RecurrenceType, TaskStatus
from app.services.project_service import create_project
from app.services.task_service import create_task, search_tasks


def test_search_tasks_returns_all_when_no_filters(db_session: Session) -> None:
    create_task(db_session, title="A")
    create_task(db_session, title="B")
    results = search_tasks(db_session)
    assert len(results) == 2


def test_search_tasks_by_status(db_session: Session) -> None:
    create_task(db_session, title="Inbox", status=TaskStatus.INBOX)
    create_task(db_session, title="Done", status=TaskStatus.DONE)
    results = search_tasks(db_session, status=TaskStatus.INBOX)
    assert len(results) == 1
    assert results[0].title == "Inbox"


def test_search_tasks_by_project(db_session: Session) -> None:
    proj = create_project(db_session, name="Work")
    create_task(db_session, title="In project", project_id=proj.id)
    create_task(db_session, title="No project")
    results = search_tasks(db_session, project_id=proj.id)
    assert len(results) == 1
    assert results[0].title == "In project"


def test_search_tasks_by_no_project(db_session: Session) -> None:
    proj = create_project(db_session, name="Work")
    create_task(db_session, title="In project", project_id=proj.id)
    create_task(db_session, title="Orphan")
    results = search_tasks(db_session, no_project=True)
    assert len(results) == 1
    assert results[0].title == "Orphan"


def test_search_tasks_by_query_in_title(db_session: Session) -> None:
    create_task(db_session, title="Buy groceries")
    create_task(db_session, title="Write report")
    results = search_tasks(db_session, q="groceries")
    assert len(results) == 1
    assert results[0].title == "Buy groceries"


def test_search_tasks_by_query_in_notes(db_session: Session) -> None:
    create_task(db_session, title="Task A", notes="Remember the dentist")
    create_task(db_session, title="Task B", notes="Pick up laundry")
    results = search_tasks(db_session, q="dentist")
    assert len(results) == 1
    assert results[0].title == "Task A"


def test_search_tasks_query_case_insensitive(db_session: Session) -> None:
    create_task(db_session, title="Buy Groceries")
    results = search_tasks(db_session, q="buy")
    assert len(results) == 1


def test_search_tasks_has_due_date(db_session: Session) -> None:
    create_task(db_session, title="Dated", due_date=date(2026, 4, 1))
    create_task(db_session, title="Not dated")
    results = search_tasks(db_session, has_due_date=True)
    assert len(results) == 1
    assert results[0].title == "Dated"


def test_search_tasks_no_due_date(db_session: Session) -> None:
    create_task(db_session, title="Dated", due_date=date(2026, 4, 1))
    create_task(db_session, title="Not dated")
    results = search_tasks(db_session, has_due_date=False)
    assert len(results) == 1
    assert results[0].title == "Not dated"


def test_search_tasks_recurring_only(db_session: Session) -> None:
    create_task(
        db_session,
        title="Recurring",
        is_recurring=True,
        recurrence_type=RecurrenceType.DAILY,
        due_date=date.today(),
    )
    create_task(db_session, title="One-shot")
    results = search_tasks(db_session, is_recurring=True)
    assert len(results) == 1
    assert results[0].title == "Recurring"


def test_search_tasks_non_recurring_only(db_session: Session) -> None:
    create_task(
        db_session,
        title="Recurring",
        is_recurring=True,
        recurrence_type=RecurrenceType.DAILY,
        due_date=date.today(),
    )
    create_task(db_session, title="One-shot")
    results = search_tasks(db_session, is_recurring=False)
    assert len(results) == 1
    assert results[0].title == "One-shot"


def test_search_tasks_combined_filters(db_session: Session) -> None:
    proj = create_project(db_session, name="Work")
    create_task(
        db_session,
        title="Work inbox",
        project_id=proj.id,
        status=TaskStatus.INBOX,
    )
    create_task(
        db_session,
        title="Work done",
        project_id=proj.id,
        status=TaskStatus.DONE,
    )
    create_task(db_session, title="Personal inbox", status=TaskStatus.INBOX)
    results = search_tasks(db_session, status=TaskStatus.INBOX, project_id=proj.id)
    assert len(results) == 1
    assert results[0].title == "Work inbox"
