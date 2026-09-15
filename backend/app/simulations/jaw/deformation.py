"""
Controlled jaw contour deformation.

Owner: Team Member

Applies intensity-controlled geometric deformation to simulate jawline
definition and angle enhancement.

Unlike the lips (volumetric expansion) and cheeks (midface volume), the
jaw simulation focuses on contour sharpening.  The ``definition``
parameter controls the degree of angularity introduced along the
jawline.

Usage:
    from app.simulations.jaw.deformation import apply_jaw_deformation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]
    from .landmarks import JawLandmarks

logger = logging.getLogger(__name__)


def apply_jaw_deformation(
    image: "np.ndarray",
    landmarks: "JawLandmarks",
    *,
    intensity: float = 0.5,
    definition: int = 50,
) -> "np.ndarray":
    """Apply controlled contour deformation to the jaw region.

    Args:
        image: Source image (HxWx3 uint8 BGR).
        landmarks: Jaw-specific landmarks in pixel coordinates.
        intensity: Normalised deformation intensity in [0, 1].
        definition: Jawline sharpness parameter (0 – 100).
                    Higher values produce more angular contours.

    Returns:
        Deformed image (HxWx3 uint8 BGR, same shape as input).

    TODO:
        - Determine displacement vectors that sharpen the jaw angle.
        - Scale displacement by intensity and definition.
        - Apply image warping along the mandible contour.
    """
    logger.info(
        "apply_jaw_deformation called with intensity=%.2f, definition=%d "
        "(placeholder — not yet implemented)",
        intensity,
        definition,
    )
    raise NotImplementedError("apply_jaw_deformation is not yet implemented.")
