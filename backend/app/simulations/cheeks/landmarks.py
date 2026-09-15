"""
Cheek-specific landmark processing.

Owner: Team Member

This module is responsible only for identifying and processing
landmarks required by the Cheeks simulation pipeline.

Shared MediaPipe setup belongs in ``app.common.face_detection``.

Key cheek landmarks (MediaPipe Face Mesh indices — approximate):
    The cheek / midface region is generally defined by landmarks in
    the zygomatic area.  Exact index selection is the responsibility
    of the team member implementing this module.

    Candidate landmark regions:
        - Left cheek area: ~93, 132, 58, 172, 136, 150, 149, 176, 148
        - Right cheek area: ~323, 361, 288, 397, 365, 379, 378, 400, 377
        - Malar / zygomatic prominence can be approximated from the
          midpoint of the cheek contour.

    These indices are illustrative.  The implementer should validate
    the exact MediaPipe mesh topology for cheek-region accuracy.

Usage:
    from app.simulations.cheeks.landmarks import extract_cheek_landmarks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.face_detection import FaceLandmarks

logger = logging.getLogger(__name__)


@dataclass
class CheekLandmarks:
    """Processed cheek-specific landmarks in pixel coordinates.

    Attributes:
        left_contour: List of (x, y) points along the left cheek.
        right_contour: List of (x, y) points along the right cheek.
        left_center: Estimated centre of the left cheek volume.
        right_center: Estimated centre of the right cheek volume.
    """

    left_contour: list[tuple[int, int]]
    right_contour: list[tuple[int, int]]
    left_center: tuple[int, int]
    right_center: tuple[int, int]


def extract_cheek_landmarks(face: "FaceLandmarks") -> CheekLandmarks | None:
    """Extract cheek-specific landmarks from a full face mesh.

    Args:
        face: Full face-mesh landmarks from the shared detector.

    Returns:
        ``CheekLandmarks`` on success, ``None`` if required landmarks
        are missing or below confidence threshold.

    TODO:
        - Select the appropriate MediaPipe indices for the cheek region.
        - Convert from normalised to pixel coordinates.
        - Calculate cheek centre points.
        - Add confidence filtering.
    """
    logger.info("extract_cheek_landmarks called (placeholder — not yet implemented)")
    return None
