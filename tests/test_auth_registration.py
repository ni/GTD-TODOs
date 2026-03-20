"""Phase 3 tests — Registration (first-run setup) flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth import COOKIE_NAME
from app.config import get_settings
from app.db import get_engine, init_db
from app.main import create_app
from app.models import WebAuthnCredential


@pytest.fixture
def auth_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client with AUTH_DISABLED=false and empty DB."""
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-registration")
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client_with_credential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Client with AUTH_DISABLED=false and one credential in DB."""
    get_settings.cache_clear()
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-registration")
    init_db(db_url)
    engine = get_engine(db_url)
    with Session(engine) as session:
        session.add(WebAuthnCredential(
            credential_id=b"\x01\x02\x03",
            public_key=b"\x04\x05\x06",
            sign_count=0,
        ))
        session.commit()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_setup_page_renders_when_no_credentials(auth_client: TestClient) -> None:
    resp = auth_client.get("/auth/setup")
    assert resp.status_code == 200
    assert "Register Passkey" in resp.text


def test_setup_redirects_to_login_when_credentials_exist(
    auth_client_with_credential: TestClient,
) -> None:
    resp = auth_client_with_credential.get("/auth/setup", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]


def test_setup_options_returns_valid_json(auth_client: TestClient) -> None:
    resp = auth_client.post("/auth/setup/options")
    assert resp.status_code == 200
    data = resp.json()
    assert "challenge" in data
    assert "rp" in data
    assert "user" in data


def _mock_verified_registration():
    """Create a mock VerifiedRegistration object."""
    mock = MagicMock()
    mock.credential_id = b"\xaa\xbb\xcc"
    mock.credential_public_key = b"\xdd\xee\xff"
    mock.sign_count = 0
    return mock


def test_setup_verify_stores_credential(
    auth_client: TestClient, tmp_path: Path
) -> None:
    # First get options to set a challenge
    auth_client.post("/auth/setup/options")

    with patch(
        "app.services.auth_service.webauthn.verify_registration_response",
        return_value=_mock_verified_registration(),
    ):
        resp = auth_client.post(
            "/auth/setup/verify",
            json={
                "id": "test-id",
                "rawId": "test-raw-id",
                "type": "public-key",
                "response": {
                    "attestationObject": "fake",
                    "clientDataJSON": "fake",
                },
            },
        )
    assert resp.status_code == 200
    assert COOKIE_NAME in resp.cookies


def test_setup_verify_rejects_invalid_response(auth_client: TestClient) -> None:
    resp = auth_client.post("/auth/setup/verify", json={"bad": "data"})
    assert resp.status_code == 400


def test_middleware_redirects_to_setup_when_no_credentials(
    auth_client: TestClient,
) -> None:
    """With no credentials, /inbox should redirect to /auth/login."""
    resp = auth_client.get("/inbox", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["location"]
