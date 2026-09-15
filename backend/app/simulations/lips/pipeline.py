"""
Lips simulation pipeline.

Owner: Jayam

Orchestrates the end-to-end lips simulation by calling each stage in
sequence:

    MediaPipe Landmarks
            ↓
        Lip ROI
            ↓
        Lip Mask
            ↓
    TPS Deformation
            ↓
  Masked AI Refinement
            ↓
 Poisson / Seamless Blending
            ↓
       Validation
            ↓
      Final Result

The pipeline receives a decoded image and configuration parameters,
and returns the simulated result image.

Usage:
    from app.simulations.lips.pipeline import run_lips_simulation

    result = await run_lips_simulation(image, config)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class LipsSimulationConfig:
    """Configuration for a single lips simulation run.

    Attributes:
        volume_ml: Requested volume parameter (0 – 2.0 mL range).
        intensity: Normalised intensity (0.0 – 1.0).
        enhancement_level: 'subtle' | 'natural' | 'full'.
        upper_lower_balance: -100 (upper-weighted) to 100 (lower-weighted).
    """

    volume_ml: float = 0.0
    intensity: float = 0.0
    enhancement_level: str = "natural"
    upper_lower_balance: int = 0


@dataclass
class LipsSimulationResult:
    """Output of the lips simulation pipeline.

    Attributes:
        image: The simulated result image (HxWx3 uint8).
        success: Whether the pipeline completed without error.
        message: Human-readable status message.
    """

    image: "np.ndarray | None" = None
    success: bool = False
    message: str = "Not yet implemented."


async def run_lips_simulation(
    image: "np.ndarray",
    config: LipsSimulationConfig,
) -> LipsSimulationResult:
    """Execute the full lips simulation pipeline.

    This is the main entry point called by ``SimulationService`` when
    the requested zone is ``lips``.

    Steps:
        1. Extract lip landmarks from the face mesh.
        2. Build the lip treatment region mask.
        3. Apply controlled TPS deformation.
        4. Run masked AI refinement.
        5. Blend the result back into the original image.
        6. Validate identity preservation and leakage.

    Args:
        image: Decoded patient photo (HxWx3 uint8 BGR).
        config: Lips-specific simulation parameters.

    Returns:
        ``LipsSimulationResult`` with the simulated image on success.

    TODO:
        - Wire up ``extract_lip_landmarks`` from landmarks.py.
        - Wire up ``build_lip_mask`` from mask.py.
        - Wire up ``apply_lip_deformation`` from deformation.py.
        - Wire up ``refine_lip_region`` from refinement.py.
        - Wire up ``poisson_blend`` from app.common.blending.
        - Add identity-preservation validation.
        - Add non-target leakage validation.
    """
    logger.info(
        "run_lips_simulation called with volume=%.1f, intensity=%.2f, level=%s",
        config.volume_ml,
        config.intensity,
        config.enhancement_level,
    )

    # TODO: Implement the pipeline steps listed above.
    return LipsSimulationResult(
        image=None,
        success=False,
        message="Lips simulation pipeline is under development.",
    )
