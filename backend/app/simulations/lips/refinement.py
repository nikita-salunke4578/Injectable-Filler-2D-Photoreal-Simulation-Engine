"""
Lip region AI refinement.

Owner: Jayam

After geometric deformation, the lip region may contain visual
artefacts (blurring, stretching, texture inconsistency).  This module
applies AI-based refinement to improve photorealism.

Critical constraints:
    1. Refinement must be MASKED — only the lip treatment region is
       refined.  The rest of the face must not be altered.
    2. The person's identity must be preserved.
    3. The refinement must not change the geometric intent (i.e., it
       should not move the lips back or further than the deformation
       intended).

Planned approach:
    - Use an inpainting / image-to-image model with the lip mask.
    - Feed the geometrically deformed image as the input.
    - Use the lip mask to restrict the generation region.
    - Validate identity preservation after refinement.

This is the ONLY stage where generative AI is involved.  The AI does
not decide what changes; it only improves the visual quality of the
change that was already determined by the deformation stage.

Usage:
    from app.simulations.lips.refinement import refine_lip_region
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


async def refine_lip_region(
    deformed_image: "np.ndarray",
    mask: "np.ndarray",
    *,
    original_image: "np.ndarray | None" = None,
) -> "np.ndarray":
    """Apply masked AI refinement to the deformed lip region.

    Args:
        deformed_image: Image after geometric deformation (HxWx3 uint8).
        mask: Lip region mask in [0, 1] (HxW float).
        original_image: The unmodified source image, used for
                        identity-preservation comparison if needed.

    Returns:
        Refined image (HxWx3 uint8, same shape).

    TODO:
        - Select an appropriate inpainting / img2img model.
        - Apply the model ONLY within the masked region.
        - Validate that identity is preserved (FaceNet cosine >= 0.90).
        - Validate that non-target regions are unchanged (< 5% leakage).
        - Fall back to the deformed image if refinement fails validation.
    """
    logger.info(
        "refine_lip_region called (placeholder — returning deformed image unmodified)"
    )

    # TODO: Implement masked AI refinement.
    # For now, return the deformed image as-is.
    return deformed_image
