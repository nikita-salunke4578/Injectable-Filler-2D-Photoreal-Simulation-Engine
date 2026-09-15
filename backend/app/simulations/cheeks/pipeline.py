"""
Cheeks simulation pipeline.

Owner: Team Member

Orchestrates the end-to-end cheeks simulation:

    MediaPipe Landmarks
            ↓
       Cheek ROI
            ↓
      Cheek Mask
            ↓
 Controlled Deformation
            ↓
 Optional AI Refinement
            ↓
       Blending
            ↓
      Validation
            ↓
     Final Result

The pipeline receives a decoded image and configuration parameters,
and returns the simulated result image.

Usage:
    from app.simulations.cheeks.pipeline import run_cheeks_simulation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class CheeksSimulationConfig:
    """Configuration for a single cheeks simulation run.

    Attributes:
        volume_ml: Requested volume parameter (0 – 4.0 mL range).
        intensity: Normalised intensity (0.0 – 1.0).
        side: 'left', 'right', or 'bilateral'.
    """

    volume_ml: float = 0.0
    intensity: float = 0.0
    side: str = "bilateral"


@dataclass
class CheeksSimulationResult:
    """Output of the cheeks simulation pipeline.

    Attributes:
        image: The simulated result image (HxWx3 uint8).
        success: Whether the pipeline completed without error.
        message: Human-readable status message.
    """

    image: "np.ndarray | None" = None
    success: bool = False
    message: str = "Not yet implemented."


async def run_cheeks_simulation(
    image: "np.ndarray",
    config: CheeksSimulationConfig,
) -> CheeksSimulationResult:
    """Execute the full cheeks simulation pipeline.

    This is the main entry point called by ``SimulationService`` when
    the requested zone is ``cheeks``.

    Args:
        image: Decoded patient photo (HxWx3 uint8 BGR).
        config: Cheeks-specific simulation parameters.

    Returns:
        ``CheeksSimulationResult`` with the simulated image on success.

    TODO:
        - Wire up ``extract_cheek_landmarks`` from landmarks.py.
        - Wire up ``build_cheek_mask`` from mask.py.
        - Wire up ``apply_cheek_deformation`` from deformation.py.
        - Wire up ``refine_cheek_region`` from refinement.py.
        - Wire up blending from app.common.blending.
        - Add validation.
    """
    logger.info(
        "run_cheeks_simulation called with volume=%.1f, intensity=%.2f, side=%s",
        config.volume_ml,
        config.intensity,
        config.side,
    )

    # TODO: Implement the pipeline steps.
    return CheeksSimulationResult(
        image=None,
        success=False,
        message="Cheeks simulation pipeline is under development.",
    )
