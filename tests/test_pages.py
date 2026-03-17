from fastapi.testclient import TestClient


def test_home_page_returns_html(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_home_page_renders_bootstrap_content(client: TestClient) -> None:
    response = client.get("/")

    assert "Phase 0 bootstrap" in response.text
    assert "GTD TODOs" in response.text
    assert "/static/app.css" in response.text