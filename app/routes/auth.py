"""Authentication routes — setup, login, logout."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlmodel import Session

from app.auth import COOKIE_NAME, create_session_cookie
from app.config import get_settings
from app.db import get_session
from app.routes import templates
from app.services.auth_service import (
    generate_authentication_options,
    generate_registration_options,
    has_credentials,
    verify_authentication,
    verify_registration,
)

logger = logging.getLogger("app")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, session: Session = Depends(get_session)) -> Response:
    if has_credentials(session):
        return RedirectResponse("/auth/login", status_code=302)
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "auth_setup.html",
        {"app_name": settings.app_name},
    )


@router.post("/setup/options")
def setup_options(session: Session = Depends(get_session)) -> Response:
    if has_credentials(session):
        return JSONResponse({"error": "Already registered"}, status_code=400)
    options_json = generate_registration_options(session)
    return Response(content=options_json, media_type="application/json")


@router.post("/setup/verify")
async def setup_verify(request: Request, session: Session = Depends(get_session)) -> Response:
    if has_credentials(session):
        return JSONResponse({"error": "Already registered"}, status_code=400)
    try:
        body = await request.json()
        verify_registration(session, body)
    except Exception as exc:
        logger.warning("Registration verification failed: %s", exc)
        return JSONResponse({"error": "Registration failed"}, status_code=400)

    cookie = create_session_cookie()
    settings = get_settings()
    resp = JSONResponse({"status": "ok"})
    resp.set_cookie(
        COOKIE_NAME,
        cookie,
        max_age=settings.auth_session_max_age,
        httponly=True,
        samesite="strict",
        secure=settings.webauthn_origin.startswith("https"),
    )
    return resp


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, session: Session = Depends(get_session)) -> Response:
    if not has_credentials(session):
        return RedirectResponse("/auth/setup", status_code=302)
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "auth_login.html",
        {"app_name": settings.app_name},
    )


@router.post("/login/options")
def login_options(session: Session = Depends(get_session)) -> Response:
    options_json = generate_authentication_options(session)
    return Response(content=options_json, media_type="application/json")


@router.post("/login/verify")
async def login_verify(request: Request, session: Session = Depends(get_session)) -> Response:
    try:
        body = await request.json()
        verify_authentication(session, body)
    except Exception as exc:
        logger.warning("Authentication verification failed: %s", exc)
        return JSONResponse({"error": "Authentication failed"}, status_code=400)

    cookie = create_session_cookie()
    settings = get_settings()
    resp = JSONResponse({"status": "ok"})
    resp.set_cookie(
        COOKIE_NAME,
        cookie,
        max_age=settings.auth_session_max_age,
        httponly=True,
        samesite="strict",
        secure=settings.webauthn_origin.startswith("https"),
    )
    return resp


@router.post("/logout")
def logout(request: Request) -> Response:
    resp = RedirectResponse("/auth/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp
