"""Settings page routes — API key management."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.routes import templates
from app.services.api_key_service import generate_key, list_keys, revoke_key
from app.services.task_service import get_nav_counts

router = APIRouter(tags=["settings"])


def _base_context(session: Session) -> dict[str, object]:
    return {
        "app_name": get_settings().app_name,
        "nav_counts": get_nav_counts(session),
    }


@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    keys = list_keys(session)
    ctx = _base_context(session)
    ctx.update({
        "api_keys": keys,
        "new_key": request.query_params.get("new_key"),
        "error": request.query_params.get("error"),
        "auth_disabled": get_settings().auth_disabled,
    })
    return templates.TemplateResponse(request, "settings.html", ctx)


@router.post("/settings/api-keys")
def create_api_key(
    request: Request, name: str = Form(""), session: Session = Depends(get_session)
) -> RedirectResponse:
    try:
        _, plaintext = generate_key(session, name)
    except ValueError as e:
        return RedirectResponse(
            f"/settings?error={str(e)}", status_code=303
        )
    return RedirectResponse(f"/settings?new_key={plaintext}", status_code=303)


@router.post("/settings/api-keys/{key_id}/revoke")
def revoke_api_key(
    key_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    if not revoke_key(session, key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return RedirectResponse("/settings", status_code=303)
