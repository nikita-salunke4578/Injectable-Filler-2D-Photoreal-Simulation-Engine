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
import uuid
from datetime import datetime
from typing import Any

from app.common.schemas import SimulationRequest, SimulationResponse, TreatmentZone
from app.common.image_io import decode_image_base64, encode_image_base64
from app.simulations.lips.pipeline import run_lips_pipeline

logger = logging.getLogger(__name__)


class SimulationService:
    """Dispatches simulation requests to region-specific pipelines.

    This is the single entry point for all simulation work.  The API
    layer calls ``run_simulation`` and receives a standardised result.
    """

    async def run_simulation(
        self,
        request: SimulationRequest,
    ) -> SimulationResponse:
        """Run a simulation for the specified treatment zones.

        Args:
            request: SimulationRequest containing image and zones.

        Returns:
            SimulationResponse with before/after image URLs and metadata.
        """
        # 1. Download/Decode Image
        if request.image_base64:
            # Local testing mode
            image = decode_image_base64(request.image_base64)
            before_url = "local_base64_used"
        else:
            # Cloudinary flow (mocked)
            raise ValueError("Cloudinary URL flow not yet implemented. Please send image_base64.")
            
        current_image = image.copy()
        
        # 2. Iterate Zones and Apply Deformation
        total_vol = 0.0
        for z_req in request.zones:
            if z_req.zone == TreatmentZone.LIPS:
                # Extract specific lip parameters
                philtral_shortening = z_req.meta.get("philtralShortening", 0)
                vermilion_show = z_req.meta.get("vermilionShow", 0)
                cupids_bow = z_req.meta.get("cupidsBow", 0)
                philtral_column = z_req.meta.get("philtralColumn", 0)
                dental_show = z_req.meta.get("dentalShow", 0)
                
                current_image = run_lips_pipeline(
                    image=current_image,
                    philtral_shortening=philtral_shortening,
                    vermilion_show=vermilion_show,
                    cupids_bow=cupids_bow,
                    philtral_column=philtral_column,
                    dental_show=dental_show,
                    show_outline=request.show_outline
                )
                
            elif z_req.zone == TreatmentZone.CHEEKS:
                # TODO: Implement cheeks
                pass
            elif z_req.zone == TreatmentZone.JAW:
                # TODO: Implement jaw
                pass
                
            total_vol += z_req.volume

        # 3. Encode result
        after_url = encode_image_base64(current_image)
        
        # 4. Construct Response
        return SimulationResponse(
            id=str(uuid.uuid4()),
            before_image_url=before_url,
            after_image_url=after_url,
            generated_at=datetime.utcnow(),
            request_payload=request.zones,
            estimated_cost_usd=(total_vol * 600.0, total_vol * 800.0),
            total_volume_ml=total_vol,
            disclaimer="Simulated outcome only."
        )
