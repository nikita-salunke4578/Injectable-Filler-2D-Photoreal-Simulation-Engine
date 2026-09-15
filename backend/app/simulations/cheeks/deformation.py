"""
Controlled cheek deformation.

Owner: Team Member

Applies intensity-controlled geometric deformation to simulate midface
volume enhancement.  The deformation should expand the cheek region
outward from the face surface to simulate volume addition.

The deformation method is at the implementer's discretion but should
follow the project's geometry-first principle: displacement direction
and magnitude are determined by explicit parameters, not by AI.

Usage:
    from app.simulations.cheeks.deformation import apply_cheek_deformation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]
    from .landmarks import CheekLandmarks

logger = logging.getLogger(__name__)


def apply_cheek_deformation(
    image: "np.ndarray",
    landmarks: "CheekLandmarks",
    *,
    intensity: float = 0.5,
    side: str = "bilateral",
) -> "np.ndarray":
    """Apply controlled deformation to the cheek region.

    Args:
        image: Source image (HxWx3 uint8 BGR).
        landmarks: Cheek-specific landmarks in pixel coordinates.
        intensity: Normalised deformation intensity in [0, 1].
        side: 'left', 'right', or 'bilateral'.

    Returns:
        Deformed image (HxWx3 uint8 BGR, same shape as input).

    TODO:
        - Determine displacement vectors for cheek landmarks.
        - Scale displacement by intensity.
        - Handle side selection.
        - Apply image warping (TPS or mesh-based warp).
    """
    logger.info(
        "apply_cheek_deformation called with intensity=%.2f, side=%s "
        "(placeholder — not yet implemented)",
        intensity,
        side,
    )
    raise NotImplementedError("apply_cheek_deformation is not yet implemented.")
