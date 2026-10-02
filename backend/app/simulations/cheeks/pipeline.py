"""
Cheek simulation pipeline.

End-to-end architecture
-----------------------

Input image
    ↓
Validation
    ↓
Face landmarks
    ↓
Cheek anatomical mapping
    ↓
Glasses detection
    ↓
Treatment mask
    ↓
Per-side RBF deformation
    ↓
Displacement-driven photometric refinement
    ↓
Anatomical alpha compositing
    ↓
Hard glasses restoration
    ↓
Leakage QA
    ↓
Final image
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.common.exceptions import (
    DeformationError,
    FaceNotDetectedError,
    LandmarkExtractionError,
)
from app.common.face_detection import FaceDetector

from app.simulations.cheeks.landmarks import (
    extract_cheek_landmarks,
)
from app.simulations.cheeks.glasses import (
    detect_glasses,
)
from app.simulations.cheeks.mask import (
    build_cheek_mask,
)
from app.simulations.cheeks.deformation import (
    apply_cheek_deformation,
)
from app.simulations.cheeks.refinement import (
    refine_cheek_region,
)

logger = logging.getLogger(__name__)


VALID_SIDES = {
    "left",
    "right",
    "bilateral",
}


VOLUME_LIMITS = {
    "lateral_volume_ck1": (0.0, 2.5),
    "medial_volume_ck2": (0.0, 2.5),
    "submalar_volume_ck3": (0.0, 2.0),
}

# Protected objects need a small safety buffer so the deformation field and
# photometric refinement do not pull or brighten pixels immediately beside them.
GLASSES_SAFETY_DILATION_PX = 18


@dataclass
class CheeksSimulationConfig:
    """Configuration parameters for cheek simulation."""

    lateral_volume_ck1: float = 1.0
    medial_volume_ck2: float = 0.5
    submalar_volume_ck3: float = 0.0

    asymmetry_mode: bool = False

    left_cheek_multiplier: float = 1.0
    right_cheek_multiplier: float = 1.0

    skin_elasticity: float = 1.0

    show_outline: bool = False

    side: str = "bilateral"


@dataclass
class CheeksSimulationResult:
    """Result of the cheek simulation."""

    image: np.ndarray | None = None

    success: bool = False

    message: str = ""


def _validate_config(
    side: str,
    **volumes: float,
) -> None:
    """Validate simulation configuration."""

    if side not in VALID_SIDES:
        raise DeformationError(
            f"Invalid side '{side}'. "
            f"Must be one of {VALID_SIDES}."
        )

    for name, value in volumes.items():

        if name not in VOLUME_LIMITS:
            raise DeformationError(
                f"Unknown volume parameter '{name}'."
            )

        lo, hi = VOLUME_LIMITS[name]

        if not (
            np.isfinite(value)
            and lo <= value <= hi
        ):
            raise DeformationError(
                f"{name}={value} is outside "
                f"the supported range [{lo}, {hi}]."
            )


def _build_zone_activity(
    lateral_volume_ck1: float,
    medial_volume_ck2: float,
    submalar_volume_ck3: float,
) -> dict[str, bool]:
    """Return active CK zones for both sides."""

    return {
        "left_ck1": lateral_volume_ck1 > 0.0,
        "left_ck2": medial_volume_ck2 > 0.0,
        "left_ck3": submalar_volume_ck3 > 0.0,
        "right_ck1": lateral_volume_ck1 > 0.0,
        "right_ck2": medial_volume_ck2 > 0.0,
        "right_ck3": submalar_volume_ck3 > 0.0,
    }


def _build_blending_mask(
    treatment_mask: np.ndarray,
    side: str,
    protected_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Convert the anatomical treatment mask into the final compositing mask.
    """

    if side == "bilateral":

        erosion_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (7, 7),
        )

        mask = cv2.erode(
            treatment_mask,
            erosion_kernel,
            iterations=1,
        )

        mask = cv2.GaussianBlur(
            mask,
            (15, 15),
            0,
        )

    else:

        mask = cv2.GaussianBlur(
            treatment_mask,
            (21, 21),
            0,
        )

    # Gaussian feathering can reintroduce non-zero alpha inside an excluded
    # object. Re-apply the hard protected region after every blur/erosion step.
    if protected_mask is not None:
        mask = mask.copy()
        mask[protected_mask > 0] = 0

    return mask


def _build_protected_mask(
    glasses_mask: np.ndarray | None,
    dilation_px: int = GLASSES_SAFETY_DILATION_PX,
) -> np.ndarray | None:
    """Build the hard protected region used by deformation and refinement."""
    if glasses_mask is None:
        return None

    kernel_size = 2 * int(dilation_px) + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    return cv2.dilate(
        glasses_mask,
        kernel,
        iterations=1,
    )


def _composite(
    original: np.ndarray,
    refined: np.ndarray,
    blending_mask: np.ndarray,
) -> np.ndarray:
    """Alpha-composite refined cheek over the original image."""

    alpha = (
        blending_mask.astype(np.float32)
        / 255.0
    )

    alpha = alpha[:, :, None]

    output = (
        refined.astype(np.float32)
        * alpha
        +
        original.astype(np.float32)
        * (1.0 - alpha)
    )

    return np.clip(
        output,
        0.0,
        255.0,
    ).astype(np.uint8)


def _restore_glasses(
    output: np.ndarray,
    original: np.ndarray,
    glasses_mask: np.ndarray | None,
) -> np.ndarray:
    """Restore original glasses pixels exactly."""

    if glasses_mask is None:
        return output

    restored = output.copy()

    restored[
        glasses_mask > 0
    ] = original[
        glasses_mask > 0
    ]

    return restored


def _run_leakage_check(
    original: np.ndarray,
    output: np.ndarray,
    blending_mask: np.ndarray,
    side: str,
) -> None:
    """
    Check whether unilateral treatment modified pixels outside
    the final compositing mask.
    """

    if side == "bilateral":
        return

    diff = np.abs(
        output.astype(np.int16)
        - original.astype(np.int16)
    )

    outside = blending_mask < 5

    if not np.any(outside):
        return

    max_leak = int(
        diff[outside].max()
    )

    if max_leak > 3:
        logger.warning(
            "Cheek leakage check failed: "
            "max outside-mask difference=%d, side=%s",
            max_leak,
            side,
        )


def _draw_outline(
    image: np.ndarray,
    landmarks,
    side: str,
) -> np.ndarray:
    """Optional debug contour overlay."""

    overlay = image.copy()

    if side in {
        "left",
        "bilateral",
    }:

        cv2.polylines(
            overlay,
            [
                landmarks.left_all.astype(
                    np.int32
                ).reshape((-1, 1, 2))
            ],
            isClosed=False,
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (
                int(landmarks.left_apex[0]),
                int(landmarks.left_apex[1]),
            ),
            3,
            (0, 230, 255),
            -1,
            lineType=cv2.LINE_AA,
        )

    if side in {
        "right",
        "bilateral",
    }:

        cv2.polylines(
            overlay,
            [
                landmarks.right_all.astype(
                    np.int32
                ).reshape((-1, 1, 2))
            ],
            isClosed=False,
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

        cv2.circle(
            overlay,
            (
                int(landmarks.right_apex[0]),
                int(landmarks.right_apex[1]),
            ),
            3,
            (0, 230, 255),
            -1,
            lineType=cv2.LINE_AA,
        )

    return cv2.addWeighted(
        overlay,
        0.65,
        image,
        0.35,
        0,
    )


def run_cheeks_pipeline(
    image: np.ndarray,
    *,
    lateral_volume_ck1: float = 1.0,
    medial_volume_ck2: float = 0.5,
    submalar_volume_ck3: float = 0.0,
    asymmetry_mode: bool = False,
    left_cheek_multiplier: float = 1.0,
    right_cheek_multiplier: float = 1.0,
    skin_elasticity: float = 1.0,
    show_outline: bool = False,
    side: str = "bilateral",
    return_debug: bool = False,
    face_detector: FaceDetector | None = None,
) -> np.ndarray | tuple[np.ndarray, dict]:
    """
    Execute the complete cheek simulation pipeline.
    """

    if image is None:
        raise DeformationError(
            "Input image cannot be None."
        )

    if image.ndim != 3 or image.shape[2] != 3:
        raise DeformationError(
            "Expected a BGR image with shape HxWx3."
        )

    # ---------------------------------------------------------
    # 1. Validate configuration
    # ---------------------------------------------------------

    _validate_config(
        side,
        lateral_volume_ck1=lateral_volume_ck1,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
    )

    # ---------------------------------------------------------
    # 2. Face landmarks
    # ---------------------------------------------------------

    if face_detector is None:
        face_detector = FaceDetector()

    try:
        face_points = face_detector.get_landmarks(
            image
        )
    except ValueError as exc:
        raise FaceNotDetectedError(
            str(exc)
        ) from exc

    try:
        landmarks = extract_cheek_landmarks(
            face_points
        )
    except ValueError as exc:
        raise LandmarkExtractionError(
            str(exc)
        ) from exc

    # ---------------------------------------------------------
    # 3. Glasses detection
    # ---------------------------------------------------------

    glasses_detected, glasses_mask = detect_glasses(
        image,
        landmarks,
    )

    # Treat glasses as an immutable object, not merely as pixels to restore later.
    protected_mask = _build_protected_mask(
        glasses_mask,
    )

    # ---------------------------------------------------------
    # 4. Early exit
    # ---------------------------------------------------------

    total_volume = (
        lateral_volume_ck1
        + medial_volume_ck2
        + submalar_volume_ck3
    )

    if total_volume <= 1e-6:

        if return_debug:

            empty = np.zeros(
                image.shape[:2],
                dtype=np.uint8,
            )

            return image.copy(), {
                "mask": empty,
                "blending_mask": empty,
                "glasses_mask": glasses_mask,
                "glasses_detected": glasses_detected,
            }

        return image.copy()

    # ---------------------------------------------------------
    # 5. Active zones
    # ---------------------------------------------------------

    zone_active = _build_zone_activity(
        lateral_volume_ck1,
        medial_volume_ck2,
        submalar_volume_ck3,
    )

    # ---------------------------------------------------------
    # 6. Anatomical treatment mask
    # ---------------------------------------------------------

    treatment_mask = build_cheek_mask(
        image.shape,
        landmarks,
        glasses_mask=protected_mask,
        side=side,
        zone_active=zone_active,
        feather_radius=25,
        dilate_px=8,
    )

    # ---------------------------------------------------------
    # 7. RBF geometric deformation
    # ---------------------------------------------------------

    (
        deformed_image,
        apexes,
        shifts_px,
        _,
    ) = apply_cheek_deformation(
        image=image,
        landmarks=landmarks,
        glasses_mask=protected_mask,
        lateral_volume_ck1=lateral_volume_ck1,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
        asymmetry_mode=asymmetry_mode,
        left_cheek_multiplier=left_cheek_multiplier,
        right_cheek_multiplier=right_cheek_multiplier,
        skin_elasticity=skin_elasticity,
        side=side,
    )

    # ---------------------------------------------------------
    # 8. Final anatomical blending mask
    # ---------------------------------------------------------

    blending_mask = _build_blending_mask(
        treatment_mask,
        side,
        protected_mask=protected_mask,
    )

    # ---------------------------------------------------------
    # 9. Photometric refinement
    # ---------------------------------------------------------

    refined_image = refine_cheek_region(
        deformed_image=deformed_image,
        mask=blending_mask,
        landmarks=landmarks,
        apexes=apexes,
        original_image=image,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
        asymmetry_mode=asymmetry_mode,
        left_multiplier=left_cheek_multiplier,
        right_multiplier=right_cheek_multiplier,
        side=side,
        shifts_px=shifts_px,
    )

    # ---------------------------------------------------------
    # 10. Anatomical alpha composite
    # ---------------------------------------------------------

    final_image = _composite(
        original=image,
        refined=refined_image,
        blending_mask=blending_mask,
    )

    # ---------------------------------------------------------
    # 11. Hard glasses restoration
    # ---------------------------------------------------------

    if glasses_detected:
        # Restore the entire protected corridor, not only the detected frame pixels.
        # This removes residual warped/ghost frame pixels immediately beside the glasses.
        final_image = _restore_glasses(
            final_image,
            image,
            protected_mask,
        )

    # ---------------------------------------------------------
    # 12. QA
    # ---------------------------------------------------------

    _run_leakage_check(
        original=image,
        output=final_image,
        blending_mask=blending_mask,
        side=side,
    )

    # ---------------------------------------------------------
    # 13. Optional debug overlay
    # ---------------------------------------------------------

    if show_outline:
        final_image = _draw_outline(
            final_image,
            landmarks,
            side,
        )

    # ---------------------------------------------------------
    # 14. Debug output
    # ---------------------------------------------------------

    if return_debug:

        debug = {
            "mask": treatment_mask,
            "blending_mask": blending_mask,
            "glasses_mask": glasses_mask,
            "protected_mask": protected_mask,
            "glasses_detected": glasses_detected,
            "apexes": apexes,
            "shifts_px": shifts_px,
            "landmarks": landmarks,
            "deformed_image": deformed_image,
            "refined_image": refined_image,
        }

        return final_image, debug

    return final_image


async def run_cheeks_simulation(
    image: np.ndarray,
    config: CheeksSimulationConfig,
) -> CheeksSimulationResult:
    """
    Async wrapper around the synchronous cheek engine.
    """

    try:

        result = run_cheeks_pipeline(
            image=image,
            lateral_volume_ck1=config.lateral_volume_ck1,
            medial_volume_ck2=config.medial_volume_ck2,
            submalar_volume_ck3=config.submalar_volume_ck3,
            asymmetry_mode=config.asymmetry_mode,
            left_cheek_multiplier=config.left_cheek_multiplier,
            right_cheek_multiplier=config.right_cheek_multiplier,
            skin_elasticity=config.skin_elasticity,
            show_outline=config.show_outline,
            side=config.side,
        )

        output = (
            result
            if isinstance(result, np.ndarray)
            else result[0]
        )

        return CheeksSimulationResult(
            image=output,
            success=True,
            message="Cheek simulation completed successfully.",
        )

    except Exception as exc:

        logger.exception(
            "Cheek simulation pipeline failed: %s",
            exc,
        )

        return CheeksSimulationResult(
            image=None,
            success=False,
            message=str(exc),
        )