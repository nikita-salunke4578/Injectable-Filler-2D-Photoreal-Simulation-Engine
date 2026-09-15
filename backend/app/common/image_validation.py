"""
Image validation utilities.

Responsible for checking that an uploaded image meets the requirements
of the simulation engine *before* any expensive CV processing begins.

Validation order:
    1. File type (JPEG / PNG / WebP)
    2. File size (configurable via MAX_IMAGE_SIZE_MB)
    3. Image readability (can be decoded)
    4. Minimum resolution (e.g. 400×400)
    5. Face presence (delegates to face_detection module)
    6. Single-face requirement

All validators return a ``ValidationResult`` so callers can collect
and surface every issue rather than failing on the first one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Supported MIME types — must match the frontend's ACCEPTED_TYPES list.
ACCEPTED_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

# Minimum dimensions in pixels.
MIN_WIDTH = 400
MIN_HEIGHT = 400


@dataclass
class ValidationResult:
    """Accumulates validation issues for a single image."""

    ok: bool = True
    issues: list[str] = field(default_factory=list)

    def add_issue(self, message: str) -> None:
        self.ok = False
        self.issues.append(message)


# ── Public API ──────────────────────────────────────────────────────


def validate_image_file(
    raw_bytes: bytes,
    *,
    mime_type: str,
    max_size_mb: int = 10,
) -> ValidationResult:
    """Run all non-CV validations on raw uploaded bytes.

    Args:
        raw_bytes: The raw file content.
        mime_type: MIME type reported by the upload.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        A ``ValidationResult`` summarising any issues found.

    TODO:
        - Implement actual file-size and MIME-type checks.
        - Call ``decode_image`` to verify the file is readable.
        - Call ``validate_resolution`` on the decoded image.
    """
    result = ValidationResult()

    # Placeholder — always passes for now.
    logger.info("validate_image_file called (placeholder — skipping real checks)")
    return result


def validate_resolution(image: "np.ndarray") -> ValidationResult:
    """Check that the decoded image meets minimum resolution.

    Args:
        image: Decoded HxWx3 NumPy array.

    Returns:
        A ``ValidationResult``.

    TODO:
        Implement actual height/width check against MIN_WIDTH / MIN_HEIGHT.
    """
    result = ValidationResult()
    logger.info("validate_resolution called (placeholder — skipping real checks)")
    return result


def validate_face_count(image: "np.ndarray") -> ValidationResult:
    """Ensure exactly one face is detected.

    Delegates to ``app.common.face_detection.FaceDetector`` for the
    actual detection.

    Args:
        image: Decoded HxWx3 NumPy array.

    Returns:
        A ``ValidationResult``.

    TODO:
        Instantiate FaceDetector, run detection, verify count == 1.
    """
    result = ValidationResult()
    logger.info("validate_face_count called (placeholder — skipping real checks)")
    return result
