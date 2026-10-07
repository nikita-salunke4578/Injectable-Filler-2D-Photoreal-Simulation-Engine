"""Shared MediaPipe face-landmarker for the cheeks module.

Creating a ``FaceLandmarker`` costs several seconds, so one instance is built
lazily and reused for every request (guarded by a lock because FastAPI may
run requests on different worker threads).
"""
from __future__ import annotations

import threading

import numpy as np

from app.common.face_detection import FaceDetector

_detector: FaceDetector | None = None
_lock = threading.Lock()


def get_shared_detector() -> FaceDetector:
    global _detector
    if _detector is None:
        with _lock:
            if _detector is None:
                _detector = FaceDetector()
    return _detector


def detect_landmarks(image_bgr: np.ndarray, detector: FaceDetector | None = None) -> np.ndarray:
    """Return (478, 2) pixel landmarks. Raises ``ValueError`` if no face is found."""
    det = detector or get_shared_detector()
    with _lock:                      # the underlying graph is not re-entrant
        return det.get_landmarks(image_bgr)
