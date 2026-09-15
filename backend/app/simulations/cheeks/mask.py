"""
Cheek treatment region mask generation.

Owner: Team Member

Builds a soft-edged mask that isolates the cheek region for deformation
and blending.  Must handle both bilateral and unilateral treatment.

When ``side='bilateral'``, both cheek regions are included in the mask.
When ``side='left'`` or ``side='right'``, only the corresponding side
is masked.

Usage:
    from app.simulations.cheeks.mask import build_cheek_mask
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]
    from .landmarks import CheekLandmarks

logger = logging.getLogger(__name__)


def build_cheek_mask(
    image_shape: tuple[int, int],
    landmarks: "CheekLandmarks",
    *,
    side: str = "bilateral",
    feather_radius: int = 21,
) -> "np.ndarray":
    """Build a feathered mask for the cheek treatment region.

    Args:
        image_shape: (height, width) of the source image.
        landmarks: Cheek-specific landmarks in pixel coordinates.
        side: 'left', 'right', or 'bilateral'.
        feather_radius: Gaussian kernel size for boundary softening.

    Returns:
        Float mask in [0, 1] with shape (H, W).

    TODO:
        - Build polygon from left/right cheek contour points.
        - Handle side selection (bilateral includes both).
        - Fill polygon and apply Gaussian feathering.
    """
    logger.info("build_cheek_mask called (placeholder — not yet implemented)")
    raise NotImplementedError("build_cheek_mask is not yet implemented.")
