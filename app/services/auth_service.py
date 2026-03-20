"""Authentication service — WebAuthn registration and login helpers."""

from __future__ import annotations

import secrets

import webauthn
from sqlmodel import Session, select
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import get_settings
from app.models import WebAuthnCredential

# In-memory challenge store (single-user app, no concurrency concern).
_current_challenge: bytes | None = None


def _store_challenge(challenge: bytes) -> None:
    global _current_challenge
    _current_challenge = challenge


def _get_challenge() -> bytes | None:
    return _current_challenge


def has_credentials(session: Session) -> bool:
    return session.exec(select(WebAuthnCredential)).first() is not None


def generate_registration_options(session: Session) -> str:
    """Generate WebAuthn registration options, return JSON string."""
    settings = get_settings()
    challenge = secrets.token_bytes(32)
    _store_challenge(challenge)

    options = webauthn.generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_name="owner",
        user_display_name="Owner",
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    return webauthn.options_to_json(options)


def verify_registration(session: Session, credential_json: dict) -> WebAuthnCredential:
    """Verify a registration response and store the credential."""
    settings = get_settings()
    challenge = _get_challenge()
    if challenge is None:
        raise ValueError("No registration challenge pending")

    verification = webauthn.verify_registration_response(
        credential=credential_json,
        expected_challenge=challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin,
    )

    cred = WebAuthnCredential(
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
    )
    session.add(cred)
    session.commit()
    session.refresh(cred)

    _store_challenge(b"")  # Clear challenge after use
    return cred


def generate_authentication_options(session: Session) -> str:
    """Generate WebAuthn authentication options, return JSON string."""
    settings = get_settings()
    challenge = secrets.token_bytes(32)
    _store_challenge(challenge)

    creds = session.exec(select(WebAuthnCredential)).all()
    allow_credentials = [
        PublicKeyCredentialDescriptor(
            id=c.credential_id,
            type=PublicKeyCredentialType.PUBLIC_KEY,
        )
        for c in creds
    ]

    options = webauthn.generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        challenge=challenge,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    return webauthn.options_to_json(options)


def verify_authentication(session: Session, credential_json: dict) -> WebAuthnCredential:
    """Verify an authentication response and update sign count."""
    settings = get_settings()
    challenge = _get_challenge()
    if challenge is None:
        raise ValueError("No authentication challenge pending")

    # Find the credential by ID
    from webauthn.helpers import base64url_to_bytes

    raw_id = credential_json.get("rawId", credential_json.get("id", ""))
    credential_id = base64url_to_bytes(raw_id)

    cred = session.exec(
        select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
    ).first()
    if cred is None:
        raise ValueError("Unknown credential")

    verification = webauthn.verify_authentication_response(
        credential=credential_json,
        expected_challenge=challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin,
        credential_public_key=cred.public_key,
        credential_current_sign_count=cred.sign_count,
    )

    cred.sign_count = verification.new_sign_count
    session.add(cred)
    session.commit()
    session.refresh(cred)

    _store_challenge(b"")  # Clear challenge after use
    return cred
