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

from app.common.schemas import SimulationRequest
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
        Placeholder result dict.  Will return ``SimulationResponse``
        once pipelines are implemented.

    TODO:
        - Map request zones to individual pipeline calls.
        - Combine results across zones.
        - Return a proper ``SimulationResponse``.
    """
    results = []
    for zone_req in request.zones:
        try:
            result = await _service.run_simulation(
                image_url=request.image_url,
                zone=zone_req.zone,
                params=zone_req.meta,
            )
            results.append(result)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed for zone {zone_req.zone.value}: {exc}",
            ) from exc

    return {
        "status": "placeholder",
        "message": "Simulation pipelines are under development.",
        "zone_results": results,
    }
