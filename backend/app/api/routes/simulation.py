"""
Simulation API routes.

Provides the ``POST /api/simulations`` endpoint that the frontend
will eventually call to run a simulation.

The route handler is intentionally thin — it validates input using
Pydantic schemas and delegates actual work to ``SimulationService``.

Currently returns a placeholder response because the simulation
pipelines are under development.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.common.schemas import CheekSimulationRequest, SimulationRequest
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api", tags=["simulation"])

# Singleton service instance (stateless, safe to reuse).
_service = SimulationService()


@router.post("/simulations")
async def run_simulation(request: SimulationRequest) -> dict:
    """Submit a simulation request.

    Accepts one or more zone configurations and dispatches each to
    the corresponding region pipeline.

    Args:
        request: Validated ``SimulationRequest`` body.

    Returns:
        SimulationResponse mapped to dict.
    """
    try:
        result = await _service.run_simulation(request)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {exc}",
        ) from exc


@router.post("/simulations/cheeks")
async def run_cheek_simulation(request: CheekSimulationRequest) -> dict:
    """Submit a dedicated cheeks simulation request.

    Args:
        request: Validated ``CheekSimulationRequest`` body with structured parameters.

    Returns:
        Simulation dictionary with before/after base64 images and metadata.
    """
    try:
        result = await _service.run_cheek_simulation(request)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Cheek simulation failed: {exc}",
        ) from exc
