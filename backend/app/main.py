"""
Injectable Filler Simulation Engine — FastAPI application entry point.

Assembles the FastAPI application, registers routers, and configures
middleware.  Run with:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.analysis import router as analysis_router
from app.common.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Injectable Filler Simulation Engine",
    version="1.0.0",
    description=(
        "2D image-based facial simulation API. "
        "This is a visualization tool — not medical advice."
    ),
)

# ── CORS ────────────────────────────────────────────────────────────
# Allow the Vite dev server to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(simulation_router)
app.include_router(analysis_router)