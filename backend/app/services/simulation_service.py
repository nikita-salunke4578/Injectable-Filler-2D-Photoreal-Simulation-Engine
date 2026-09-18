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
from datetime import datetime, timezone
from typing import Any

from app.common.schemas import (
    CheekSimulationRequest,
    SimulationRequest,
    SimulationResponse,
    TreatmentZone,
)
from app.common.image_io import decode_image_base64, encode_image_base64
from app.simulations.lips.pipeline import run_lips_pipeline
from app.simulations.cheeks.pipeline import run_cheeks_pipeline

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
                # Extract specific cheek parameters
                lat_vol = float(z_req.meta.get("lateral_volume_ck1", 1.0))
                med_vol = float(z_req.meta.get("medial_volume_ck2", 0.5))
                sub_vol = float(z_req.meta.get("submalar_volume_ck3", 0.0))
                asym = bool(z_req.meta.get("asymmetry_mode", False))
                l_mult = float(z_req.meta.get("left_cheek_multiplier", 1.0))
                r_mult = float(z_req.meta.get("right_cheek_multiplier", 1.0))
                elasticity = float(z_req.meta.get("skin_elasticity", 1.0))
                side = str(z_req.meta.get("side", "bilateral"))

                current_image = run_cheeks_pipeline(
                    image=current_image,
                    lateral_volume_ck1=lat_vol,
                    medial_volume_ck2=med_vol,
                    submalar_volume_ck3=sub_vol,
                    asymmetry_mode=asym,
                    left_cheek_multiplier=l_mult,
                    right_cheek_multiplier=r_mult,
                    skin_elasticity=elasticity,
                    show_outline=request.show_outline,
                    side=side,
                )
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
            generated_at=datetime.now(timezone.utc),
            request_payload=request.zones,
            estimated_cost_usd=(total_vol * 600.0, total_vol * 800.0),
            total_volume_ml=total_vol,
            disclaimer="Simulated outcome only."
        )

    async def run_cheek_simulation(
        self,
        request: CheekSimulationRequest,
    ) -> dict:
        """Direct execution for the dedicated /api/simulations/cheeks endpoint."""
        image = decode_image_base64(request.image_base64)
        p = request.parameters

        simulated_image = run_cheeks_pipeline(
            image=image,
            lateral_volume_ck1=p.lateral_volume_ck1,
            medial_volume_ck2=p.medial_volume_ck2,
            submalar_volume_ck3=p.submalar_volume_ck3,
            asymmetry_mode=p.asymmetry_mode,
            left_cheek_multiplier=p.left_cheek_multiplier,
            right_cheek_multiplier=p.right_cheek_multiplier,
            skin_elasticity=p.skin_elasticity,
            show_outline=request.show_outline,
        )

        after_base64 = encode_image_base64(simulated_image)
        total_vol = (p.lateral_volume_ck1 + p.medial_volume_ck2 + p.submalar_volume_ck3)

        return {
            "id": str(uuid.uuid4()),
            "zone": "cheeks",
            "before_image_url": "local_base64_used",
            "after_image_url": after_base64,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "parameters": p.model_dump(),
            "total_volume_ml": round(total_vol, 2),
            "estimated_cost_usd": [round(total_vol * 600.0, 2), round(total_vol * 800.0, 2)],
            "disclaimer": "Simulated outcome for planning purposes only.",
        }
