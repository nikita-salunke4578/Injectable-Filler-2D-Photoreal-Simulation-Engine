"""
Jaw simulation pipeline.

Owner: Team Member

Orchestrates the end-to-end jaw simulation:

    MediaPipe Landmarks
            ↓
       Jaw ROI
            ↓
      Jaw Mask
            ↓
 Controlled Contour Deformation
            ↓
 Optional AI Refinement
            ↓
       Blending
            ↓
      Validation
            ↓
     Final Result

The jaw simulation differs from lips/cheeks in that it focuses on
contour sharpening / definition rather than volumetric expansion.

Usage:
    from app.simulations.jaw.pipeline import run_jaw_simulation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from app.common.face_detection import FaceDetector
from .deformation import apply_jaw_deformation
from .landmarks import extract_jaw_landmarks
from .mask import build_jaw_mask
from .refinement import refine_jaw_region

logger = logging.getLogger(__name__)


@dataclass
class JawSimulationConfig:
    """Configuration for a single jaw simulation run.

    Attributes:
        volume_ml: Requested volume parameter (0 – 3.0 mL range).
        intensity: Normalised intensity (0.0 – 1.0).
        definition: Jawline definition parameter (0 – 100).
                    0 = soft/natural, 100 = maximum sharpening.
    """

    volume_ml: float = 0.0
    intensity: float = 0.0
    definition: int = 0


@dataclass
class JawSimulationResult:
    """Output of the jaw simulation pipeline.

    Attributes:
        image: The simulated result image (HxWx3 uint8).
        success: Whether the pipeline completed without error.
        message: Human-readable status message.
    """

    image: "np.ndarray | None" = None
    success: bool = False
    message: str = "Not yet implemented."


async def run_jaw_simulation(
    image: "np.ndarray",
    config: JawSimulationConfig,
) -> JawSimulationResult:
    """Execute the full jaw simulation pipeline.

    This is the main entry point called by ``SimulationService`` when
    the requested zone is ``jaw``.

    Args:
        image: Decoded patient photo (HxWx3 uint8 BGR).
        config: Jaw-specific simulation parameters.

    Returns:
        ``JawSimulationResult`` with the simulated image on success.

    TODO:
        - Wire up ``extract_jaw_landmarks`` from landmarks.py.
        - Wire up ``build_jaw_mask`` from mask.py.
        - Wire up ``apply_jaw_deformation`` from deformation.py.
        - Wire up ``refine_jaw_region`` from refinement.py.
        - Wire up blending from app.common.blending.
        - Add validation.
    """
    try:
        if image is None:
            raise ValueError("Input image must not be None.")
        if not isinstance(image, np.ndarray):
            raise ValueError("Input image must be a NumPy array.")
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Input image must have shape HxWx3.")
        if image.dtype != np.uint8:
            raise ValueError("Input image must have dtype uint8.")

        if not 0.0 <= config.intensity <= 1.0:
            raise ValueError("Config intensity must be in the range [0, 1].")
        if not 0 <= config.definition <= 100:
            raise ValueError("Config definition must be in the range [0, 100].")
        if not 0.0 <= config.volume_ml <= 3.0:
            raise ValueError("Config volume_ml must be in the range [0, 3].")

        if config.intensity == 0.0 or config.definition == 0:
            return JawSimulationResult(
                image=image.copy(),
                success=True,
                message="Jaw simulation completed successfully.",
            )

        logger.info(
            "run_jaw_simulation called with volume=%.1f, intensity=%.2f, definition=%d",
            config.volume_ml,
            config.intensity,
            config.definition,
        )

        detector = FaceDetector()
        face_landmarks = detector.get_landmarks(image)
        jaw_landmarks = extract_jaw_landmarks(face_landmarks)
        if jaw_landmarks is None:
            raise ValueError("Jaw landmarks could not be extracted from the detected face.")

        jaw_mask = build_jaw_mask(
            image.shape[:2],
            jaw_landmarks,
            feather_radius=25,
        )
        deformed_image = apply_jaw_deformation(
            image,
            jaw_landmarks,
            intensity=config.intensity,
            definition=config.definition,
        )
        refined_image = await refine_jaw_region(
            deformed_image,
            jaw_mask,
            original_image=image,
        )

        if refined_image is None:
            raise ValueError("Jaw refinement returned no image.")
        if not isinstance(refined_image, np.ndarray):
            raise ValueError("Jaw refinement returned a non-NumPy image.")
        if refined_image.shape != image.shape:
            raise ValueError("Jaw refinement returned an image with an invalid shape.")
        if refined_image.dtype != np.uint8:
            raise ValueError("Jaw refinement returned an image with an invalid dtype.")

        final_image = refined_image.copy()
        
        if final_image is None:
            raise ValueError("Final image is None.")
        if final_image.shape != image.shape:
            raise ValueError("Final image shape does not match the original image.")
        if final_image.dtype != np.uint8:
            raise ValueError("Final image dtype is not uint8.")
        if not np.isfinite(final_image).all():
            raise ValueError("Final image contains non-finite values.")

        return JawSimulationResult(
            image=final_image,
            success=True,
            message="Jaw simulation completed successfully.",
        )
    except Exception as exc:
        logger.exception("Jaw simulation failed.")
        return JawSimulationResult(
            image=None,
            success=False,
            message=f"Jaw simulation failed: {exc}",
        )
