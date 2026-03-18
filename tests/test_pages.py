import re

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import TaskStatus
from app.services.project_service import create_project
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