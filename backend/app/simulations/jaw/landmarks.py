"""
Jaw-specific landmark processing.

Owner: Team Member

This module is responsible only for identifying and processing
landmarks required by the Jaw simulation pipeline.

Shared MediaPipe setup belongs in ``app.common.face_detection``.

Key jaw/lower-face landmarks (MediaPipe Face Mesh indices):
    The jawline contour runs along the mandible boundary.  Candidate
    indices for the jaw contour include:

    Left jawline:  ~10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288
    Right jawline: ~10, 109, 67, 103, 54, 21, 162, 127, 234, 93, 132, 58
    Chin:          ~152, 175, 199, 200

    The ``definition`` parameter controls how sharply the jawline
    contour is enhanced.

    These indices are illustrative.  The implementer should validate
    the exact MediaPipe mesh topology for jaw-region accuracy.

Usage:
    from app.simulations.jaw.landmarks import extract_jaw_landmarks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from app.common.face_detection import FaceLandmarks

logger = logging.getLogger(__name__)

# MediaPipe Face Mesh lower-jaw contour points. These indices are the actual
# documented face-oval/jawline points used for the mandibular contour, with
# explicit left/right angle and chin anchors.
LEFT_JAW_CONTOUR_INDICES = (132, 58, 172, 136, 150, 149, 176, 148, 152)
RIGHT_JAW_CONTOUR_INDICES = (361, 288, 397, 365, 379, 378, 400, 377, 152)
CHIN_INDEX = 152
LEFT_JAW_ANGLE_INDEX = 132
RIGHT_JAW_ANGLE_INDEX = 361


@dataclass
class JawLandmarks:
    """Processed jaw-specific landmarks in pixel coordinates.

    Attributes:
        left_contour: List of (x, y) points along the left jawline.
        right_contour: List of (x, y) points along the right jawline.
        chin: (x, y) position of the chin point.
        jaw_angle_left: (x, y) of the left jaw angle.
        jaw_angle_right: (x, y) of the right jaw angle.
    """

    left_contour: list[tuple[int, int]]
    right_contour: list[tuple[int, int]]
    chin: tuple[int, int]
    jaw_angle_left: tuple[int, int]
    jaw_angle_right: tuple[int, int]


def extract_jaw_landmarks(face: "FaceLandmarks") -> JawLandmarks | None:
    """Extract jaw-specific landmarks from the shared MediaPipe face mesh.

    In this repository, the shared detector already returns a NumPy array of
    landmark coordinates in pixel space, not a custom FaceLandmarks dataclass.
    The jaw extractor therefore reads the raw face mesh array directly and
    validates the required lower-jaw landmarks before returning.
    """
    if face is None:
        logger.warning("Jaw landmark extraction received a null face object.")
        return None

    try:
        landmark_count = len(face)
    except TypeError:
        logger.warning("Jaw landmark extraction requires a sequence of face mesh points.")
        return None

    required_indices = (
        LEFT_JAW_CONTOUR_INDICES + RIGHT_JAW_CONTOUR_INDICES + (CHIN_INDEX, LEFT_JAW_ANGLE_INDEX, RIGHT_JAW_ANGLE_INDEX)
    )
    missing_indices = [index for index in sorted(set(required_indices)) if index >= landmark_count]
    if missing_indices:
        logger.warning(
            "Jaw landmark extraction missing required MediaPipe indices: %s (landmark_count=%d)",
            missing_indices,
            landmark_count,
        )
        return None

    def read_point(index: int) -> tuple[int, int] | None:
        try:
            point = face[index]
        except (IndexError, TypeError):
            logger.warning("Jaw landmark extraction could not read index %d.", index)
            return None

        if point is None or len(point) < 2:
            logger.warning("Jaw landmark extraction found an incomplete point at index %d.", index)
            return None

        x_value, y_value = point[0], point[1]
        try:
            x_coord = int(round(float(x_value)))
            y_coord = int(round(float(y_value)))
        except (TypeError, ValueError):
            logger.warning("Jaw landmark extraction found a non-numeric point at index %d.", index)
            return None

        if not (np.isfinite(x_value) and np.isfinite(y_value)):
            logger.warning("Jaw landmark extraction found a non-finite point at index %d.", index)
            return None

        return x_coord, y_coord

    left_contour = [read_point(index) for index in LEFT_JAW_CONTOUR_INDICES]
    right_contour = [read_point(index) for index in RIGHT_JAW_CONTOUR_INDICES]
    chin = read_point(CHIN_INDEX)
    jaw_angle_left = read_point(LEFT_JAW_ANGLE_INDEX)
    jaw_angle_right = read_point(RIGHT_JAW_ANGLE_INDEX)

    if any(point is None for point in left_contour + right_contour + [chin, jaw_angle_left, jaw_angle_right]):
        logger.warning("Jaw landmark extraction failed because one or more required landmarks were invalid or missing.")
        return None

    return JawLandmarks(
        left_contour=[tuple(point) for point in left_contour],
        right_contour=[tuple(point) for point in right_contour],
        chin=tuple(chin),
        jaw_angle_left=tuple(jaw_angle_left),
        jaw_angle_right=tuple(jaw_angle_right),
    )
