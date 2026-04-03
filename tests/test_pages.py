import re
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import TaskStatus
from app.services.project_service import complete_project, create_project
from app.services.task_service import create_task


def test_home_redirects_to_inbox(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/inbox" in response.headers["location"]


def test_home_follows_redirect_to_html(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_project_detail_groups_ordered_done_last(
    client: TestClient, db_session: Session
) -> None:
    """Status groups on the project detail page follow STATUS_LABELS order,
    meaning 'Done' always appears after all other groups."""
    project = create_project(db_session, name="Order Test")
    pid = project.id

    # Create tasks in deliberately scrambled order so that insertion order
    # alone would NOT produce the correct status group sequence.
    create_task(db_session, title="T-done", status=TaskStatus.DONE, project_id=pid)
    create_task(db_session, title="T-next", status=TaskStatus.NEXT_ACTION, project_id=pid)
    create_task(db_session, title="T-someday", status=TaskStatus.SOMEDAY_MAYBE, project_id=pid)
    create_task(db_session, title="T-inbox", status=TaskStatus.INBOX, project_id=pid)

    response = client.get(f"/projects/{pid}")
    assert response.status_code == 200

    # Extract section headings in the order they appear in the HTML
    headings = re.findall(r'class="section-heading[^"]*">\s*(.+?)\s*</', response.text)

    assert headings == ["Inbox", "Next Action", "Someday / Maybe", "Done"]


def test_projects_list_hides_completed_by_default(
    client: TestClient, db_session: Session
) -> None:
    """The projects page should only show open projects by default."""
    create_project(db_session, name="Open Project")
    completed_proj = create_project(db_session, name="Completed Project")
    complete_project(db_session, completed_proj.id)  # type: ignore[arg-type]

    response = client.get("/projects")
    assert response.status_code == 200
    assert "Open Project" in response.text
    assert "Completed Project" not in response.text


def test_projects_list_show_all_includes_completed(
    client: TestClient, db_session: Session
) -> None:
    """When show=all, completed projects should appear after open ones."""
    create_project(db_session, name="Alpha Open")
    completed_proj = create_project(db_session, name="Beta Completed")
    complete_project(db_session, completed_proj.id)  # type: ignore[arg-type]

    response = client.get("/projects?show=all")
    assert response.status_code == 200
    assert "Alpha Open" in response.text
    assert "Beta Completed" in response.text
    # Completed should appear after open
    assert response.text.index("Alpha Open") < response.text.index("Beta Completed")


def test_projects_list_show_all_completed_after_open(
    client: TestClient, db_session: Session
) -> None:
    """Even with alphabetically-earlier name, completed project sorts last."""
    completed_proj = create_project(db_session, name="AAA Done")
    complete_project(db_session, completed_proj.id)  # type: ignore[arg-type]
    create_project(db_session, name="ZZZ Active")

    response = client.get("/projects?show=all")
    assert response.status_code == 200
    # ZZZ Active (open) should appear before AAA Done (completed)
    assert response.text.index("ZZZ Active") < response.text.index("AAA Done")


def test_projects_list_filter_has_due_date(
    client: TestClient, db_session: Session
) -> None:
    create_project(db_session, name="With Date", due_date=date(2026, 6, 1))
    create_project(db_session, name="No Date")

    resp_yes = client.get("/projects?has_due_date=yes")
    assert "With Date" in resp_yes.text
    assert "No Date" not in resp_yes.text

    resp_no = client.get("/projects?has_due_date=no")
    assert "No Date" in resp_no.text
    assert "With Date" not in resp_no.text

    resp_any = client.get("/projects")
    assert "With Date" in resp_any.text
    assert "No Date" in resp_any.text