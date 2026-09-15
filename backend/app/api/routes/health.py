"""
Health-check route.

Provides a simple ``/health`` endpoint used by monitoring, load
balancers, and development tooling to verify the backend is running.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return basic health status.

    Responds with ``{"status": "ok"}`` when the server is up.
    """
    return {
        "status": "ok",
        "service": "Injectable Filler Simulation Engine",
    }
