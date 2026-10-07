"""
Final compositing mask.

alpha = soft union of per-zone footprints, each multiplied by THAT zone's protect map
(the same map the warp used, so mask and displacement agree at the face outline and no
ghost edge appears), with glasses pixels forced to exactly 0 so frames/lenses are
bit-identical to the input.
"""
from __future__ import annotations

import cv2
import numpy as np

from .landmarks import CheekLandmarks
from .deformation import zone_weight, side_half_weight, medial_weight, elasticity_response


def build_cheek_mask(shape, lm: CheekLandmarks, zone_protect, *,
                     volumes_left: dict, volumes_right: dict,
                     glasses_mask: np.ndarray | None = None,
                     elasticity: float = 1.0) -> np.ndarray:
    """uint8 [0,255] feathered blend mask. ``zone_protect`` is {zone: map} (a single array is also accepted)."""
    h, w = shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    alpha = np.zeros((h, w), np.float32)
    spread = elasticity_response(elasticity)["spread"]          # the blend footprint follows the warp footprint
    for sg, vols in ((lm.left, volumes_left), (lm.right, volumes_right)):
        half = side_half_weight((h, w), lm, sg.side) * medial_weight(xx, yy, sg, lm.scale)
        for name, z in sg.zones.items():
            if vols.get(name, 0.0) > 1e-4:
                g = zone_weight(xx, yy, z, vols[name], widen=1.9 * spread)[0] * half     # wider than the warp
                pm = zone_protect[name] if isinstance(zone_protect, dict) else zone_protect
                alpha = np.maximum(alpha, np.clip(g * 1.6, 0, 1) * pm)
    alpha = cv2.GaussianBlur(alpha, (0, 0), max(2.0, 0.03 * lm.scale))
    if glasses_mask is not None:
        gm = glasses_mask if glasses_mask.ndim == 2 else glasses_mask[..., 0]
        alpha[gm > 127] = 0.0
    return (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
