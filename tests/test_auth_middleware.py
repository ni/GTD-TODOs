"""Phase 2 tests — Auth middleware enforcement mode."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import COOKIE_NAME, create_session_cookie
from app.config import get_settings
from app.main import create_app


@pytest.fixture
def auth_enabled_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client with AUTH_DISABLED=false and no credentials in DB."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-middleware")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health_always_accessible(auth_enabled_client: TestClient) -> None:
    resp = auth_enabled_client.get("/health")
    assert resp.status_code == 200


def test_static_always_accessible(auth_enabled_client: TestClient) -> None:
    resp = auth_enabled_client.get("/static/app.css")
    assert resp.status_code == 200


def test_unauthenticated_html_redirects_to_login(auth_enabled_client: TestClient) -> None:
    resp = auth_enabled_client.get("/inbox", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]


def test_unauthenticated_api_returns_401(auth_enabled_client: TestClient) -> None:
    resp = auth_enabled_client.get(
        "/export/tasks.json",
        follow_redirects=False,
    )
    assert resp.status_code == 401


def test_valid_session_cookie_allows_access(auth_enabled_client: TestClient) -> None:
    cookie = create_session_cookie()
    auth_enabled_client.cookies.set(COOKIE_NAME, cookie)
    resp = auth_enabled_client.get("/inbox", follow_redirects=False)
    assert resp.status_code == 200


def test_expired_session_cookie_redirects(
    auth_enabled_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    cookie = create_session_cookie()
    # Patch verify_session_cookie to always return False (simulates expiry)
    monkeypatch.setattr("app.auth.verify_session_cookie", lambda _: False)
    auth_enabled_client.cookies.set(COOKIE_NAME, cookie)
    resp = auth_enabled_client.get("/inbox", follow_redirects=False)
    assert resp.status_code == 302


def test_tampered_cookie_redirects(auth_enabled_client: TestClient) -> None:
    auth_enabled_client.cookies.set(COOKIE_NAME, "tampered.cookie.value")
    resp = auth_enabled_client.get("/inbox", follow_redirects=False)
    assert resp.status_code == 302


def test_auth_disabled_skips_enforcement(client) -> None:  # type: ignore[no-untyped-def]
    """With AUTH_DISABLED=true (default test fixture), unauthenticated access works."""
    resp = client.get("/inbox")
    assert resp.status_code == 200
