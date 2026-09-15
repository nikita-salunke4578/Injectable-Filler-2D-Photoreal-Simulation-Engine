"""
Simulation service — dispatch layer.

Receives a simulation request (zone + parameters) and routes it to
the corresponding region pipeline:

    zone = 'lips'   → app.simulations.lips.pipeline
    zone = 'cheeks' → app.simulations.cheeks.pipeline
    zone = 'jaw'    → app.simulations.jaw.pipeline

The service layer exists to keep API route handlers thin.  Routes
should validate input and call this service; they should NOT contain
simulation logic directly.

Usage:
    from app.services.simulation_service import SimulationService

    service = SimulationService()
    result = await service.run_simulation(image, zone, params)
"""

from __future__ import annotations

import logging
from typing import Any

from app.common.schemas import TreatmentZone

logger = logging.getLogger(__name__)


class SimulationService:
    """Dispatches simulation requests to region-specific pipelines.

    This is the single entry point for all simulation work.  The API
    layer calls ``run_simulation`` and receives a standardised result.
    """

    async def run_simulation(
        self,
        image_url: str,
        zone: TreatmentZone,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a simulation for the specified treatment zone.

        Args:
            image_url: URL of the patient photo to process.
            zone: Treatment zone to simulate.
            params: Zone-specific parameter dictionary.

        Returns:
            Dictionary with simulation results (will be mapped to
            ``SimulationResponse`` by the API layer).

        TODO:
            - Download image via ``load_image_from_url``.
            - Validate image via ``validate_image_file``.
            - Dispatch to the appropriate pipeline based on ``zone``.
            - Convert pipeline result to response dict.
            - Handle and map pipeline exceptions.
        """
        logger.info("run_simulation called for zone=%s (placeholder)", zone.value)

        if zone == TreatmentZone.LIPS:
            # TODO: from app.simulations.lips.pipeline import run_lips_simulation
            return self._placeholder_result(zone, params)

        if zone == TreatmentZone.CHEEKS:
            # TODO: from app.simulations.cheeks.pipeline import run_cheeks_simulation
            return self._placeholder_result(zone, params)

        if zone == TreatmentZone.JAW:
            # TODO: from app.simulations.jaw.pipeline import run_jaw_simulation
            return self._placeholder_result(zone, params)

        # Defensive — should never reach here due to enum validation.
        raise ValueError(f"Unsupported treatment zone: {zone}")

    @staticmethod
    def _placeholder_result(
        zone: TreatmentZone,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a safe placeholder result while pipelines are unimplemented."""
        return {
            "zone": zone.value,
            "status": "not_implemented",
            "message": (
                f"The {zone.value} simulation pipeline is under development. "
                "This placeholder confirms that the service dispatch is working."
            ),
            "params_received": params,
        }
