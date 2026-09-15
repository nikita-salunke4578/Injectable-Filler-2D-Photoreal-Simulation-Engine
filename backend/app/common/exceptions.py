"""
Shared exception types for the simulation engine.

All region-specific modules should raise these exceptions rather than
raw Python exceptions so that the API layer can map them to consistent
HTTP error responses.

Usage:
    from app.common.exceptions import FaceNotDetectedError
    raise FaceNotDetectedError("No face detected in the uploaded image.")
"""

from __future__ import annotations


class SimulationEngineError(Exception):
    """Base exception for all simulation-engine errors."""

    def __init__(self, message: str = "An unexpected simulation error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class ImageValidationError(SimulationEngineError):
    """Raised when an uploaded image fails validation checks.

    Examples: unsupported format, too small, too large, unreadable.
    """


class FaceNotDetectedError(SimulationEngineError):
    """Raised when no face (or too many faces) is found in the image.

    The simulation requires exactly one clearly visible, front-facing face.
    """


class LandmarkExtractionError(SimulationEngineError):
    """Raised when facial landmark extraction fails or returns
    insufficient confidence for the target region."""


class DeformationError(SimulationEngineError):
    """Raised when geometric deformation cannot be applied safely.

    For example: degenerate TPS solution, out-of-bounds displacement.
    """


class RefinementError(SimulationEngineError):
    """Raised when the AI refinement stage fails."""


class CloudinaryError(SimulationEngineError):
    """Raised when a Cloudinary upload/download/delete operation fails."""
