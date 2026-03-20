"""Phase 4 tests — Login (passkey authentication) flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import COOKIE_NAME, create_session_cookie
from app.config import get_settings
from app.db import get_engine, init_db
from app.main import create_app
from app.models import WebAuthnCredential

# Reusable credential bytes for test fixtures
_CRED_ID = b"\x01\x02\x03"
_PUB_KEY = b"\x04\x05\x06"


def _seed_credential(db_url: str) -> None:
    """Insert a test credential into the database."""
    init_db(db_url)
    engine = get_engine(db_url)
    with Session(engine) as session:
        session.add(WebAuthnCredential(
            credential_id=_CRED_ID,
            public_key=_PUB_KEY,
            sign_count=5,
        ))
        session.commit()


@pytest.fixture
def login_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client with AUTH_DISABLED=false and one credential in DB."""
    get_settings.cache_clear()
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-login")
    _seed_credential(db_url)
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def login_client_no_creds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client with AUTH_DISABLED=false and NO credentials."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-login")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_login_page_renders(login_client: TestClient) -> None:
    resp = login_client.get("/auth/login")
    assert resp.status_code == 200
    assert "Sign In" in resp.text


def test_login_options_returns_challenge_and_credentials(login_client: TestClient) -> None:
    resp = login_client.post("/auth/login/options")
    assert resp.status_code == 200
    data = resp.json()
    assert "challenge" in data
    assert "allowCredentials" in data
    assert len(data["allowCredentials"]) >= 1


def _mock_verified_authentication(new_sign_count: int = 6):
    mock = MagicMock()
    mock.new_sign_count = new_sign_count
    return mock


def test_login_verify_sets_session_and_redirects(login_client: TestClient) -> None:
    # Get options first to set a challenge
    login_client.post("/auth/login/options")

    from webauthn.helpers import bytes_to_base64url
    raw_id_b64 = bytes_to_base64url(_CRED_ID)

    with patch(
        "app.services.auth_service.webauthn.verify_authentication_response",
        return_value=_mock_verified_authentication(6),
    ):
        resp = login_client.post(
            "/auth/login/verify",
            json={
                "id": raw_id_b64,
                "rawId": raw_id_b64,
                "type": "public-key",
                "response": {
                    "authenticatorData": "fake",
                    "clientDataJSON": "fake",
                    "signature": "fake",
                    "userHandle": None,
                },
            },
        )
    assert resp.status_code == 200
    assert COOKIE_NAME in resp.cookies


def test_login_verify_updates_sign_count(
    login_client: TestClient, tmp_path: Path,
) -> None:
    login_client.post("/auth/login/options")

    from webauthn.helpers import bytes_to_base64url
    raw_id_b64 = bytes_to_base64url(_CRED_ID)

    with patch(
        "app.services.auth_service.webauthn.verify_authentication_response",
        return_value=_mock_verified_authentication(10),
    ):
        login_client.post(
            "/auth/login/verify",
            json={
                "id": raw_id_b64,
                "rawId": raw_id_b64,
                "type": "public-key",
                "response": {
                    "authenticatorData": "fake",
                    "clientDataJSON": "fake",
                    "signature": "fake",
                    "userHandle": None,
                },
            },
        )

    # Verify sign count was updated
    import os
    db_url = os.environ["DATABASE_URL"]
    engine = get_engine(db_url)
    with Session(engine) as session:
        cred = session.exec(select(WebAuthnCredential)).first()
        assert cred is not None
        assert cred.sign_count == 10


def test_login_verify_rejects_invalid_response(login_client: TestClient) -> None:
    resp = login_client.post("/auth/login/verify", json={"bad": "data"})
    assert resp.status_code == 400


def test_login_verify_rejects_replayed_sign_count(login_client: TestClient) -> None:
    login_client.post("/auth/login/options")

    from webauthn.helpers import bytes_to_base64url
    raw_id_b64 = bytes_to_base64url(_CRED_ID)

    # Mock verify to raise (py_webauthn raises on replayed sign count)
    with patch(
        "app.services.auth_service.webauthn.verify_authentication_response",
        side_effect=Exception("Sign count replay detected"),
    ):
        resp = login_client.post(
            "/auth/login/verify",
            json={
                "id": raw_id_b64,
                "rawId": raw_id_b64,
                "type": "public-key",
                "response": {
                    "authenticatorData": "fake",
                    "clientDataJSON": "fake",
                    "signature": "fake",
                    "userHandle": None,
                },
            },
        )
    assert resp.status_code == 400


def test_logout_clears_cookie_and_redirects(login_client: TestClient) -> None:
    # Set a session cookie first
    cookie = create_session_cookie()
    login_client.cookies.set(COOKIE_NAME, cookie)
    resp = login_client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]


def test_login_redirects_to_setup_when_no_credentials(
    login_client_no_creds: TestClient,
) -> None:
    resp = login_client_no_creds.get("/auth/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/setup" in resp.headers["location"]
