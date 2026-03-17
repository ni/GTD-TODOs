from fastapi.testclient import TestClient


def test_home_redirects_to_inbox(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/inbox" in response.headers["location"]


def test_home_follows_redirect_to_html(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")