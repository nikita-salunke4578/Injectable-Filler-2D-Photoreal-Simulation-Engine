"""
Cheeks simulation pipeline.

Orchestrates the complete midface/cheek enhancement pipeline:
1. Input Config & Volume Bounds Validation
2. Face Detection & Cheek Landmark Extraction
3. Single-Pass Glasses Detection (glasses.py)
4. Region Mask Construction with Hard Glasses Occlusion Subtraction
5. Per-Side Isolated RBF Geometric Deformation with Hard Pixel Protection
6. Physical Displacement-Driven LAB Relighting & Texture Injection
7. Feathered Alpha Blending & Hard Original Glasses Restoration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import cv2
import numpy as np

from app.common.exceptions import DeformationError, FaceNotDetectedError, LandmarkExtractionError
from app.common.face_detection import FaceDetector
from app.simulations.cheeks.landmarks import extract_cheek_landmarks
from app.simulations.cheeks.glasses import detect_glasses
from app.simulations.cheeks.mask import build_cheek_mask
from app.simulations.cheeks.deformation import apply_cheek_deformation
from app.simulations.cheeks.refinement import refine_cheek_region

logger = logging.getLogger(__name__)

VALID_SIDES = {"left", "right", "bilateral"}
VOLUME_LIMITS = {
    "lateral_volume_ck1": (0.0, 2.5),
    "medial_volume_ck2": (0.0, 2.5),
    "submalar_volume_ck3": (0.0, 2.0),
}


def _validate_config(side: str, **volumes: float) -> None:
    """Validates side parameter and volume boundaries."""
    if side not in VALID_SIDES:
        raise DeformationError(f"Invalid side '{side}'. Must be one of {VALID_SIDES}.")
    for name, value in volumes.items():
        lo, hi = VOLUME_LIMITS[name]
        if not (lo <= value <= hi):
            raise DeformationError(f"{name}={value} is out of range [{lo}, {hi}].")


@dataclass
class CheeksSimulationConfig:
    """Configuration parameters for the cheeks simulation."""

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
    """Result of the cheeks simulation pipeline."""

    image: np.ndarray | None = None
    success: bool = False
    message: str = ""


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
    Executes the complete Cheeks simulation pipeline.

    Returns:
        Transformed BGR image (numpy array), or tuple with debug dictionary if return_debug is True.
    """
    _validate_config(
        side,
        lateral_volume_ck1=lateral_volume_ck1,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
    )

    if face_detector is None:
        face_detector = FaceDetector()

    # 1. Face Detection & Landmark Extraction
    try:
        face_pts = face_detector.get_landmarks(image)
    except ValueError as e:
        raise FaceNotDetectedError(str(e)) from e

    try:
        landmarks = extract_cheek_landmarks(face_pts)
    except ValueError as e:
        raise LandmarkExtractionError(str(e)) from e

    # 2. Single-Pass Glasses Detection
    glasses_detected, glasses_mask = detect_glasses(image, landmarks)

    total_vol = lateral_volume_ck1 + medial_volume_ck2 + submalar_volume_ck3
    if total_vol <= 1e-4:
        if return_debug:
            empty_mask = np.zeros(image.shape[:2], dtype=np.uint8)
            return image.copy(), {"mask": empty_mask, "blending_mask": empty_mask}
        return image.copy()

    # Active sub-zones tracking
    zone_active = {
        "left_ck1": lateral_volume_ck1 > 0,
        "left_ck2": medial_volume_ck2 > 0,
        "left_ck3": submalar_volume_ck3 > 0,
        "right_ck1": lateral_volume_ck1 > 0,
        "right_ck2": medial_volume_ck2 > 0,
        "right_ck3": submalar_volume_ck3 > 0,
    }

    # 3. Region Mask Construction with hard glasses mask subtraction
    mask = build_cheek_mask(
        image.shape,
        landmarks,
        glasses_mask=glasses_mask,
        side=side,
        zone_active=zone_active,
        feather_radius=25,
        dilate_px=8,
    )

    # 4. Isolated Per-Side Geometric Deformation with hard glasses pixel preservation
    deformed_img, apexes, shifts_px, _ = apply_cheek_deformation(
        image=image,
        landmarks=landmarks,
        glasses_mask=glasses_mask,
        lateral_volume_ck1=lateral_volume_ck1,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
        asymmetry_mode=asymmetry_mode,
        left_cheek_multiplier=left_cheek_multiplier,
        right_cheek_multiplier=right_cheek_multiplier,
        skin_elasticity=skin_elasticity,
        side=side,
    )

    # Blending mask derived for both refinement and final composite
    if side != "bilateral":
        blending_mask = cv2.GaussianBlur(mask, (21, 21), 0)
    else:
        erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        blending_mask = cv2.erode(mask, erode_kernel, iterations=1)
        blending_mask = cv2.GaussianBlur(blending_mask, (15, 15), 0)

    # 5. Displacement-Driven Relighting and High-Pass Refinement
    refined_img = refine_cheek_region(
        deformed_image=deformed_img,
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

    # 6. Alpha Composite
    alpha = blending_mask.astype(np.float32) / 255.0
    alpha_3c = alpha[:, :, np.newaxis]
    final_img = np.clip(
        refined_img.astype(np.float32) * alpha_3c + image.astype(np.float32) * (1.0 - alpha_3c),
        0.0, 255.0
    ).astype(np.uint8)

    # 7. Final Glasses Pixel Restoration
    if glasses_detected and glasses_mask is not None:
        final_img[glasses_mask > 0] = image[glasses_mask > 0]

    # Leakage assertion for single-sided runs
    if side != "bilateral":
        diff = np.abs(final_img.astype(np.int16) - image.astype(np.int16))
        outside = blending_mask < 5
        if np.any(outside):
            max_leak = int(diff[outside].max())
            if max_leak > 3:
                logger.warning("Leakage check failed: max diff outside mask=%d (side=%s)", max_leak, side)

    # 8. Contour Overlay Option
    if show_outline:
        overlay = final_img.copy()

        if side in ("bilateral", "left"):
            cv2.polylines(
                overlay,
                [landmarks.left_all.astype(np.int32).reshape((-1, 1, 2))],
                isClosed=False,
                color=(255, 255, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                (int(landmarks.left_apex[0]), int(landmarks.left_apex[1])),
                3,
                (0, 230, 255),
                -1,
                lineType=cv2.LINE_AA,
            )

        if side in ("bilateral", "right"):
            cv2.polylines(
                overlay,
                [landmarks.right_all.astype(np.int32).reshape((-1, 1, 2))],
                isClosed=False,
                color=(255, 255, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                (int(landmarks.right_apex[0]), int(landmarks.right_apex[1])),
                3,
                (0, 230, 255),
                -1,
                lineType=cv2.LINE_AA,
            )

        final_img = cv2.addWeighted(overlay, 0.65, final_img, 0.35, 0)

    if return_debug:
        return final_img, {"mask": mask, "blending_mask": blending_mask}

    return final_img


async def run_cheeks_simulation(
    image: np.ndarray,
    config: CheeksSimulationConfig,
) -> CheeksSimulationResult:
    """Async wrapper executing the cheeks simulation pipeline."""
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
        return CheeksSimulationResult(
            image=result if isinstance(result, np.ndarray) else result[0],
            success=True,
            message="Cheek simulation completed successfully.",
        )
    except Exception as e:
        logger.exception("Cheek simulation pipeline failed: %s", e)
        return CheeksSimulationResult(
            image=None,
            success=False,
            message=str(e),
        )