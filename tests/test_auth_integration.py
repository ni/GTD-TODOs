"""Phase 6 tests — Integration tests for the full auth lifecycle."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import COOKIE_NAME
from app.config import get_settings
from app.main import create_app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def integration_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Auth-enabled client with empty DB."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "integration-test-key")
    app = create_app()
    with TestClient(app) as c:
        yield c


def _mock_verified_registration():
    mock = MagicMock()
    mock.credential_id = b"\xaa\xbb\xcc"
    mock.credential_public_key = b"\xdd\xee\xff"
    mock.sign_count = 0
    return mock


def _mock_verified_authentication(new_sign_count: int = 1):
    mock = MagicMock()
    mock.new_sign_count = new_sign_count
    return mock


# ---------------------------------------------------------------------------
# Test 1: Full setup → login lifecycle
# ---------------------------------------------------------------------------

def test_full_setup_then_login_lifecycle(integration_client: TestClient) -> None:
    c = integration_client

    # Unauthenticated → redirect to login
    resp = c.get("/inbox", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]

    # Login page → no credentials → redirect to setup
    resp = c.get("/auth/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/setup" in resp.headers["location"]

    # Setup page renders
    resp = c.get("/auth/setup")
    assert resp.status_code == 200

    # Get registration options
    resp = c.post("/auth/setup/options")
    assert resp.status_code == 200

    # Verify registration (mocked)
    with patch(
        "app.services.auth_service.webauthn.verify_registration_response",
        return_value=_mock_verified_registration(),
    ):
        resp = c.post("/auth/setup/verify", json={
            "id": "test", "rawId": "test", "type": "public-key",
            "response": {"attestationObject": "x", "clientDataJSON": "x"},
        })
    assert resp.status_code == 200
    assert COOKIE_NAME in resp.cookies
    session_cookie = resp.cookies[COOKIE_NAME]

    # Access inbox with the cookie
    c.cookies.set(COOKIE_NAME, session_cookie)
    resp = c.get("/inbox")
    assert resp.status_code == 200

    # Logout
    resp = c.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302

    # Clear cookie client-side
    c.cookies.clear()

    # Now log in with authentication
    resp = c.get("/auth/login")
    assert resp.status_code == 200
    assert "Sign In" in resp.text

    # Get authentication options
    resp = c.post("/auth/login/options")
    assert resp.status_code == 200

    from webauthn.helpers import bytes_to_base64url
    raw_id_b64 = bytes_to_base64url(b"\xaa\xbb\xcc")

    with patch(
        "app.services.auth_service.webauthn.verify_authentication_response",
        return_value=_mock_verified_authentication(1),
    ):
        resp = c.post("/auth/login/verify", json={
            "id": raw_id_b64, "rawId": raw_id_b64, "type": "public-key",
            "response": {
                "authenticatorData": "x", "clientDataJSON": "x",
                "signature": "x", "userHandle": None,
            },
        })
    assert resp.status_code == 200
    assert COOKIE_NAME in resp.cookies

    # Verify access works
    c.cookies.set(COOKIE_NAME, resp.cookies[COOKIE_NAME])
    resp = c.get("/inbox")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: Second registration blocked
# ---------------------------------------------------------------------------

def test_second_passkey_registration_blocked(integration_client: TestClient) -> None:
    c = integration_client

    # Register first
    c.post("/auth/setup/options")
    with patch(
        "app.services.auth_service.webauthn.verify_registration_response",
        return_value=_mock_verified_registration(),
    ):
        resp = c.post("/auth/setup/verify", json={
            "id": "test", "rawId": "test", "type": "public-key",
            "response": {"attestationObject": "x", "clientDataJSON": "x"},
        })
    assert resp.status_code == 200

    # Try to access setup again
    c.cookies.set(COOKIE_NAME, resp.cookies[COOKIE_NAME])
    resp = c.get("/auth/setup", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]


# ---------------------------------------------------------------------------
# Test 3: Auth protects all page routes
# ---------------------------------------------------------------------------

_PROTECTED_PAGE_ROUTES = [
    "/",
    "/inbox",
    "/today",
    "/projects",
    "/tasks",
]


@pytest.mark.parametrize("path", _PROTECTED_PAGE_ROUTES)
def test_auth_protects_all_page_routes(
    integration_client: TestClient, path: str
) -> None:
    resp = integration_client.get(path, follow_redirects=False)
    assert resp.status_code == 302, f"{path} should redirect when unauthenticated"
    location = resp.headers["location"]
    assert "/auth/" in location, f"{path} should redirect to auth"


# ---------------------------------------------------------------------------
# Test 4: Auth protects all API/export routes
# ---------------------------------------------------------------------------

_PROTECTED_API_ROUTES = [
    "/export/tasks.csv",
    "/export/tasks.json",
    "/export/projects.csv",
    "/export/projects.json",
]


@pytest.mark.parametrize("path", _PROTECTED_API_ROUTES)
def test_auth_protects_all_api_routes(
    integration_client: TestClient, path: str
) -> None:
    resp = integration_client.get(path, follow_redirects=False)
    assert resp.status_code == 401, f"{path} should return 401 when unauthenticated"


# ---------------------------------------------------------------------------
# Test 5: AUTH_DISABLED bypasses everything
# ---------------------------------------------------------------------------

def test_auth_disabled_env_bypasses_everything(client) -> None:  # type: ignore[no-untyped-def]
    """With AUTH_DISABLED=true (default conftest), all routes work without auth."""
    for path in ["/inbox", "/today", "/tasks", "/projects"]:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} should be accessible with AUTH_DISABLED"
    resp = client.get("/export/tasks.json")
    assert resp.status_code == 200
