"""Phase 1 tests — Auth model, config, and AUTH_DISABLED bypass."""

from __future__ import annotations

import pytest
from sqlmodel import Session, select, text

from app.config import get_settings
from app.db import get_engine, init_db
from app.models import WebAuthnCredential


@pytest.fixture
def _auth_db(sqlite_database_url: str) -> str:
    init_db(sqlite_database_url)
    return sqlite_database_url


def test_credential_table_created(_auth_db: str) -> None:
    engine = get_engine(_auth_db)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master"
                " WHERE type='table' AND name='webauthn_credentials'"
            )
        )
        assert result.fetchone() is not None


def test_credential_round_trip(_auth_db: str) -> None:
    engine = get_engine(_auth_db)
    cred = WebAuthnCredential(
        credential_id=b"\x01\x02\x03",
        public_key=b"\x04\x05\x06",
        sign_count=0,
    )
    with Session(engine) as session:
        session.add(cred)
        session.commit()

    with Session(engine) as session:
        row = session.exec(select(WebAuthnCredential)).first()
        assert row is not None
        assert row.credential_id == b"\x01\x02\x03"
        assert row.public_key == b"\x04\x05\x06"
        assert row.sign_count == 0
        assert row.created_at is not None


def test_auth_disabled_allows_all_routes(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/inbox")
    assert resp.status_code == 200


def test_settings_includes_auth_fields() -> None:
    settings = get_settings()
    assert hasattr(settings, "auth_disabled")
    assert hasattr(settings, "auth_secret_key")
    assert hasattr(settings, "auth_session_max_age")
    assert hasattr(settings, "webauthn_rp_id")
    assert hasattr(settings, "webauthn_rp_name")
    assert hasattr(settings, "webauthn_origin")
