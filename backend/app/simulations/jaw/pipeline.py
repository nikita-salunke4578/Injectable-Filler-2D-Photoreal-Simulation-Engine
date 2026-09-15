"""
Jaw simulation pipeline.

Owner: Team Member

Orchestrates the end-to-end jaw simulation:

    MediaPipe Landmarks
            ↓
       Jaw ROI
            ↓
      Jaw Mask
            ↓
 Controlled Contour Deformation
            ↓
 Optional AI Refinement
            ↓
       Blending
            ↓
      Validation
            ↓
     Final Result

The jaw simulation differs from lips/cheeks in that it focuses on
contour sharpening / definition rather than volumetric expansion.

Usage:
    from app.simulations.jaw.pipeline import run_jaw_simulation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class JawSimulationConfig:
    """Configuration for a single jaw simulation run.

    Attributes:
        volume_ml: Requested volume parameter (0 – 3.0 mL range).
        intensity: Normalised intensity (0.0 – 1.0).
        definition: Jawline definition parameter (0 – 100).
                    0 = soft/natural, 100 = maximum sharpening.
    """

    volume_ml: float = 0.0
    intensity: float = 0.0
    definition: int = 0


@dataclass
class JawSimulationResult:
    """Output of the jaw simulation pipeline.

    Attributes:
        image: The simulated result image (HxWx3 uint8).
        success: Whether the pipeline completed without error.
        message: Human-readable status message.
    """

    image: "np.ndarray | None" = None
    success: bool = False
    message: str = "Not yet implemented."


async def run_jaw_simulation(
    image: "np.ndarray",
    config: JawSimulationConfig,
) -> JawSimulationResult:
    """Execute the full jaw simulation pipeline.

    This is the main entry point called by ``SimulationService`` when
    the requested zone is ``jaw``.

    Args:
        image: Decoded patient photo (HxWx3 uint8 BGR).
        config: Jaw-specific simulation parameters.

    Returns:
        ``JawSimulationResult`` with the simulated image on success.

    TODO:
        - Wire up ``extract_jaw_landmarks`` from landmarks.py.
        - Wire up ``build_jaw_mask`` from mask.py.
        - Wire up ``apply_jaw_deformation`` from deformation.py.
        - Wire up ``refine_jaw_region`` from refinement.py.
        - Wire up blending from app.common.blending.
        - Add validation.
    """
    logger.info(
        "run_jaw_simulation called with volume=%.1f, intensity=%.2f, definition=%d",
        config.volume_ml,
        config.intensity,
        config.definition,
    )

    # TODO: Implement the pipeline steps.
    return JawSimulationResult(
        image=None,
        success=False,
        message="Jaw simulation pipeline is under development.",
    )
