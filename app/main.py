"""FastAPI application entry point."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.db import init_db
from app.logging_config import configure_logging
from app.routes import templates
from app.routes.export import router as export_router
from app.routes.health import router as health_router
from app.routes.pages import router as pages_router
from app.routes.tasks import router as tasks_router

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info("Application starting up")
    init_db()
    logger.info("Database initialised")
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # --- Request logging middleware ---
    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def,unused-ignore]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # --- Custom error pages ---
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> HTMLResponse:
        status_code = exc.status_code
        detail = exc.detail or "An error occurred"
        logger.warning(
            "HTTP %d on %s %s: %s",
            status_code, request.method, request.url.path, detail,
        )
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "app_name": settings.app_name,
                "status_code": status_code,
                "detail": detail,
            },
            status_code=status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> HTMLResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "app_name": settings.app_name,
                "status_code": 500,
                "detail": "Internal Server Error",
            },
            status_code=500,
        )

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(health_router)
    app.include_router(pages_router)
    app.include_router(tasks_router)
    app.include_router(export_router)
    return app


app = create_app()