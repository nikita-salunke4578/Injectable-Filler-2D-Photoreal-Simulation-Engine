"""
Image blending utilities.

Provides shared compositing functions used by all treatment regions
after geometric deformation.  The goal is to merge the modified region
back into the original image with no visible seam.

Planned techniques:
    - Alpha blending (fast, basic)
    - Feathered-mask blending (Gaussian blur on the mask boundary)
    - Poisson / seamless cloning (highest quality, OpenCV seamlessClone)

Region-specific mask generation belongs in each simulation module;
this module only applies the blend given a mask.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def alpha_blend(
    background: "np.ndarray",
    foreground: "np.ndarray",
    mask: "np.ndarray",
) -> "np.ndarray":
    """Simple per-pixel alpha blend.

    ``result = foreground * mask + background * (1 - mask)``

    Args:
        background: Original image (HxWx3 uint8).
        foreground: Modified image (HxWx3 uint8, same shape).
        mask: Single-channel float mask in [0, 1] (HxW).

    Returns:
        Blended image (HxWx3 uint8).

    TODO:
        Implement using NumPy broadcasting.
    """
    raise NotImplementedError("alpha_blend is not yet implemented.")


def feather_mask(
    mask: "np.ndarray",
    *,
    kernel_size: int = 21,
) -> "np.ndarray":
    """Apply Gaussian feathering to a binary mask.

    This softens the boundary between the modified region and the
    original image so that the blend transition is gradual.

    Args:
        mask: Binary mask (HxW, uint8 with 0/255).
        kernel_size: Size of the Gaussian kernel (must be odd).

    Returns:
        Feathered float mask in [0, 1] (HxW).

    TODO:
        Implement using ``cv2.GaussianBlur``.
    """
    raise NotImplementedError("feather_mask is not yet implemented.")


def poisson_blend(
    background: "np.ndarray",
    foreground: "np.ndarray",
    mask: "np.ndarray",
    *,
    center: tuple[int, int] | None = None,
) -> "np.ndarray":
    """Seamless cloning using Poisson blending (OpenCV).

    Produces the highest-quality results by matching gradient fields
    across the boundary.  This is the preferred method for the final
    simulation output.

    Args:
        background: Original image (HxWx3 uint8).
        foreground: Modified image (HxWx3 uint8, same shape).
        mask: Binary mask (HxW, uint8 with 0/255).
        center: (x, y) centre point for the clone.  If ``None``,
                the mask centroid is used.

    Returns:
        Seamlessly blended image (HxWx3 uint8).

    TODO:
        Implement using ``cv2.seamlessClone`` with NORMAL_CLONE.
    """
    raise NotImplementedError("poisson_blend is not yet implemented.")
