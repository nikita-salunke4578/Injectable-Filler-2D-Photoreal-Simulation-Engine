"""
Jaw region AI refinement.

Owner: Team Member

After geometric deformation, applies optional masked AI refinement to
improve photorealism in the jaw/lower-face area.

Same constraints as lips and cheeks refinement:
    1. Refinement must be MASKED to the jaw treatment region only.
    2. Identity must be preserved.
    3. Non-target regions must not be modified.

Usage:
    from app.simulations.jaw.refinement import refine_jaw_region
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


async def refine_jaw_region(
    deformed_image: "np.ndarray",
    mask: "np.ndarray",
    *,
    original_image: "np.ndarray | None" = None,
) -> "np.ndarray":
    """Apply masked AI refinement to the deformed jaw region.

    Args:
        deformed_image: Image after geometric deformation (HxWx3 uint8).
        mask: Jaw region mask in [0, 1] (HxW float).
        original_image: Unmodified source for validation comparison.

    Returns:
        Refined image (HxWx3 uint8, same shape).

    TODO:
        - Select an appropriate inpainting / img2img model.
        - Apply ONLY within the masked region.
        - Validate identity preservation and non-target leakage.
    """
    logger.info(
        "refine_jaw_region called (placeholder — returning deformed image)"
    )
    return deformed_image
