"""
Lips-specific landmark processing.

Owner: Jayam

This module is responsible ONLY for identifying and processing
landmarks required by the Lips simulation pipeline.

Shared MediaPipe setup belongs in ``app.common.face_detection``.

Key lip landmarks (MediaPipe Face Mesh indices):
    61  – Left corner of the mouth
    291 – Right corner of the mouth
    0   – Upper lip centre (top of cupid's bow)
    17  – Lower lip centre

These four landmarks serve as the primary anchors for controlled lip
deformation.  Additional landmarks along the upper and lower lip
contours will be used for finer control of the treatment region.

Extended lip contour landmarks (planned):
    Upper outer: 61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291
    Upper inner: 78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308
    Lower inner: 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308
    Lower outer: 61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291

Usage:
    from app.simulations.lips.landmarks import extract_lip_landmarks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.face_detection import FaceLandmarks

logger = logging.getLogger(__name__)

# ── Landmark index constants ────────────────────────────────────────

# Primary anchor landmarks for lip deformation.
LIP_LEFT_CORNER = 61
LIP_RIGHT_CORNER = 291
LIP_UPPER_CENTER = 0
LIP_LOWER_CENTER = 17

PRIMARY_LIP_LANDMARKS = (
    LIP_LEFT_CORNER,
    LIP_RIGHT_CORNER,
    LIP_UPPER_CENTER,
    LIP_LOWER_CENTER,
)

# Extended contour indices for region-boundary construction.
UPPER_OUTER_CONTOUR = (61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291)
UPPER_INNER_CONTOUR = (78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308)
LOWER_INNER_CONTOUR = (78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308)
LOWER_OUTER_CONTOUR = (61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291)


@dataclass
class LipLandmarks:
    """Processed lip-specific landmarks in pixel coordinates.

    Attributes:
        left_corner: (x, y) of left mouth corner.
        right_corner: (x, y) of right mouth corner.
        upper_center: (x, y) of upper lip centre.
        lower_center: (x, y) of lower lip centre.
        upper_contour: List of (x, y) points along the upper lip.
        lower_contour: List of (x, y) points along the lower lip.
    """

    left_corner: tuple[int, int]
    right_corner: tuple[int, int]
    upper_center: tuple[int, int]
    lower_center: tuple[int, int]
    upper_contour: list[tuple[int, int]]
    lower_contour: list[tuple[int, int]]


def extract_lip_landmarks(face: "FaceLandmarks") -> LipLandmarks | None:
    """Extract lip-specific landmarks from a full face mesh.

    Takes the shared ``FaceLandmarks`` produced by
    ``app.common.face_detection.FaceDetector`` and returns only the
    lip-relevant subset, converted to pixel coordinates.

    Args:
        face: Full face-mesh landmarks from the shared detector.

    Returns:
        ``LipLandmarks`` on success, ``None`` if required landmarks
        are missing or below confidence threshold.

    TODO:
        - Convert PRIMARY_LIP_LANDMARKS from normalised to pixel coords.
        - Build upper/lower contour point lists.
        - Add confidence filtering (reject if key landmarks are low).
    """
    logger.info("extract_lip_landmarks called (placeholder — not yet implemented)")
    return None
