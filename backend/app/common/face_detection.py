"""
Shared face detection and landmark extraction infrastructure.

This module owns the MediaPipe Face Mesh initialisation and provides a
single ``FaceDetector`` class that all three treatment regions reuse.

**Region-specific landmark selection** does NOT belong here.
For example, selecting lip landmarks 61/291/0/17 from the full mesh
belongs in ``app.simulations.lips.landmarks``.

This module only provides:
    - Face presence detection
    - Full-mesh landmark extraction
    - Landmark confidence scores

Usage:
    from app.common.face_detection import FaceDetector

    detector = FaceDetector()
    landmarks = detector.get_landmarks(image)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class FaceLandmarks:
    """Container for extracted facial landmarks.

    Attributes:
        points: Nx3 array of (x, y, z) normalised landmark coordinates.
                N = 468 for MediaPipe Face Mesh.
        confidence: Overall detection confidence in [0, 1].
        image_width: Width of the source image in pixels.
        image_height: Height of the source image in pixels.
    """

    points: "np.ndarray"
    confidence: float
    image_width: int
    image_height: int

    def pixel_coords(self, index: int) -> tuple[int, int]:
        """Convert a normalised landmark to pixel coordinates.

        Args:
            index: MediaPipe landmark index (0-467).

        Returns:
            (x, y) tuple in pixel space.

        TODO:
            Implement actual coordinate conversion.
        """
        raise NotImplementedError("pixel_coords is not yet implemented.")


class FaceDetector:
    """Thin wrapper around MediaPipe Face Mesh.

    Initialises the face-mesh solution once and exposes simple methods
    for detection and landmark extraction.

    TODO:
        - Add ``mediapipe`` to requirements.txt.
        - Initialise ``mp.solutions.face_mesh.FaceMesh`` in ``__init__``.
        - Consider making this a context manager for resource cleanup.
    """

    def __init__(self, *, max_faces: int = 1, min_confidence: float = 0.5) -> None:
        self._max_faces = max_faces
        self._min_confidence = min_confidence
        # TODO: Initialise MediaPipe Face Mesh here.
        logger.info(
            "FaceDetector created (placeholder — MediaPipe not yet initialised)"
        )

    def detect_face(self, image: "np.ndarray") -> bool:
        """Return True if at least one face is detected.

        Args:
            image: HxWx3 uint8 BGR NumPy array.

        TODO:
            Run MediaPipe face detection and return result.
        """
        logger.info("detect_face called (placeholder — returning True)")
        return True

    def get_landmarks(self, image: "np.ndarray") -> FaceLandmarks | None:
        """Extract the full 468-point face mesh from *image*.

        Args:
            image: HxWx3 uint8 BGR NumPy array.

        Returns:
            ``FaceLandmarks`` on success, ``None`` if no face found.

        TODO:
            Run MediaPipe Face Mesh, convert results to ``FaceLandmarks``.
        """
        logger.info("get_landmarks called (placeholder — returning None)")
        return None

    def close(self) -> None:
        """Release MediaPipe resources.

        TODO:
            Call ``self._face_mesh.close()`` once initialised.
        """
        pass
