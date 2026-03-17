"""Health service helpers."""

from app.schemas import HealthResponse


def get_health_status() -> HealthResponse:
    return HealthResponse(status="ok")