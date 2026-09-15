"""
Jaw treatment region mask generation.

Owner: Team Member

Builds a soft-edged mask that isolates the lower-face / jawline region
for contour deformation and blending.

The jaw mask should cover the mandible contour area while avoiding
the lips and chin regions (unless specifically targeted).

Usage:
    from app.simulations.jaw.mask import build_jaw_mask
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]
    from .landmarks import JawLandmarks

logger = logging.getLogger(__name__)


def build_jaw_mask(
    image_shape: tuple[int, int],
    landmarks: "JawLandmarks",
    *,
    feather_radius: int = 25,
) -> "np.ndarray":
    """Build a feathered mask for the jaw treatment region.

    Args:
        image_shape: (height, width) of the source image.
        landmarks: Jaw-specific landmarks in pixel coordinates.
        feather_radius: Gaussian kernel size for boundary softening.

    Returns:
        Float mask in [0, 1] with shape (H, W).

    TODO:
        - Build polygon from left/right jawline contour and chin points.
        - Fill polygon and apply Gaussian feathering.
        - Ensure the mask does not overlap with the lip region.
    """
    logger.info("build_jaw_mask called (placeholder — not yet implemented)")
    raise NotImplementedError("build_jaw_mask is not yet implemented.")
