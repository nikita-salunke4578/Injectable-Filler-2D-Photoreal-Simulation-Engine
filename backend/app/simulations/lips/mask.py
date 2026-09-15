"""
Lip treatment region mask generation.

Owner: Jayam

Builds a soft-edged mask that isolates the lip region for deformation
and blending.  The mask ensures that only the lip area is modified
while the rest of the face remains untouched.

Planned approach:
    1. Use lip contour landmarks to define the boundary polygon.
    2. Apply Delaunay triangulation or convex-hull construction to
       create a filled region.
    3. Apply Gaussian feathering to soften the boundary.
    4. Optionally erode/dilate to control the treatment margin.

The output mask is used by:
    - ``deformation.py`` to restrict displacement to the lip region.
    - ``app.common.blending`` to merge the result seamlessly.

Usage:
    from app.simulations.lips.mask import build_lip_mask
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]
    from .landmarks import LipLandmarks

logger = logging.getLogger(__name__)


def build_lip_mask(
    image_shape: tuple[int, int],
    landmarks: "LipLandmarks",
    *,
    feather_radius: int = 15,
    margin_px: int = 5,
) -> "np.ndarray":
    """Build a feathered mask for the lip treatment region.

    Args:
        image_shape: (height, width) of the source image.
        landmarks: Lip-specific landmarks in pixel coordinates.
        feather_radius: Gaussian kernel size for boundary softening.
        margin_px: Extra margin around the lip contour (pixels).

    Returns:
        Float mask in [0, 1] with shape (H, W).  Values near 1.0
        indicate the lip region; values near 0.0 indicate background.

    TODO:
        - Combine upper and lower contour points into a closed polygon.
        - Fill the polygon with ``cv2.fillPoly`` or ``cv2.drawContours``.
        - Apply ``cv2.GaussianBlur`` for feathering.
        - Optionally apply ``cv2.dilate`` for the treatment margin.
        - Return the feathered float mask.
    """
    logger.info("build_lip_mask called (placeholder — not yet implemented)")
    raise NotImplementedError("build_lip_mask is not yet implemented.")
