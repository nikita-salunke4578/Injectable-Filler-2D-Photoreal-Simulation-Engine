"""
Cheeks simulation pipeline.

Orchestrates the complete midface/cheek enhancement pipeline:
1. Face Detection & Cheek Landmark Extraction
2. Orbital-Safe Mask Generation
3. RBF + TPS Geometric Deformation
4. Non-AI Relighting, Specular Sheen & Texture Injection
5. Feathered Alpha Blending
6. Optional Before/After Contour Overlay
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import cv2
import numpy as np

from app.common.face_detection import FaceDetector
from app.simulations.cheeks.landmarks import extract_cheek_landmarks
from app.simulations.cheeks.mask import build_cheek_mask
from app.simulations.cheeks.deformation import apply_cheek_deformation
from app.simulations.cheeks.refinement import refine_cheek_region

logger = logging.getLogger(__name__)


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
    face_detector: FaceDetector | None = None,
) -> np.ndarray:
    """
    Executes the complete Cheeks simulation pipeline.

    Args:
        image: BGR numpy array (original photo).
        lateral_volume_ck1: CK1 lateral zygomatic volume (0.0 to 2.5 mL).
        medial_volume_ck2: CK2 malar apex volume (0.0 to 2.5 mL).
        submalar_volume_ck3: CK3 lower cheek hollow volume (0.0 to 2.0 mL).
        asymmetry_mode: Whether independent left/right volume multipliers are active.
        left_cheek_multiplier: Multiplier for left cheek volume (0.0 to 2.0).
        right_cheek_multiplier: Multiplier for right cheek volume (0.0 to 2.0).
        skin_elasticity: Skin elasticity scale (0.8 to 1.2).
        show_outline: Whether to overlay original cheek contours on output.
        side: 'left', 'right', or 'bilateral'.
        face_detector: FaceDetector instance (optional to avoid re-instantiation).

    Returns:
        Transformed BGR image (numpy array).
    """
    if face_detector is None:
        face_detector = FaceDetector()

    # 1. Face Detection & Landmark Extraction
    face_pts = face_detector.get_landmarks(image)
    landmarks = extract_cheek_landmarks(face_pts)

    # 2. Region Mask Construction (with lower orbit exclusion cage)
    

    # If all volumes are zero, return original
    total_vol = lateral_volume_ck1 + medial_volume_ck2 + submalar_volume_ck3
    if total_vol <= 1e-4:
        return image.copy()

    mask = build_cheek_mask(
        image.shape,
        landmarks,
        side=side,
        feather_radius=25,
        dilate_px=14,
    )

    # 3. Geometric Deformation (Gaussian RBF + TPS with Normalized Coordinates)
    deformed_img, apexes, _ = apply_cheek_deformation(
        image=image,
        landmarks=landmarks,
        lateral_volume_ck1=lateral_volume_ck1,
        medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3,
        asymmetry_mode=asymmetry_mode,
        left_cheek_multiplier=left_cheek_multiplier,
        right_cheek_multiplier=right_cheek_multiplier,
        skin_elasticity=skin_elasticity,
        side=side,
    )

    # 5. Feathered Alpha Blending (replaces Poisson seamlessClone)
    #
    # WHY NOT seamlessClone:
    #   cv2.seamlessClone fails catastrophically on images with a pure white
    #   (255,255,255) studio background. Poisson's solver tries to equalise
    #   gradient equations across the enormous contrast boundary (skin ~180
    #   vs background 255). To satisfy those equations it floods the entire
    #   cheek interior with white — causing the bright glow artifact you see.
    #
    # FIX — erode + Gaussian-feathered alpha blend:
    #   1. Erode the mask inward by a few px to guarantee zero background overlap.
    #   2. Re-apply a light Gaussian feather on the eroded edge for a smooth join.
    #   3. Composite with standard alpha blending: out = fg*a + bg*(1-a).
    #   This keeps every blend pixel strictly inside the skin region and
    #   is immune to background colour, making it safe for all studio photos.
    #
    # This mask is computed ONCE here and reused for both the refinement pass
    # and the final composite below. Previously refine_cheek_region() was
    # called with the un-eroded `mask` while the final blend used a separately
    # eroded `blending_mask` — two different boundaries for "what got relit"
    # vs. "what gets shown". That mismatch, combined with the eye-exclusion
    # cage carving an interior hole out of `mask`, produced a visible dark
    # island of frozen/un-relit original pixels near the tear trough. Using
    # one consistent mask for both stages removes that second seam.
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    blending_mask = cv2.erode(mask, erode_kernel, iterations=1)
    blending_mask = cv2.GaussianBlur(blending_mask, (15, 15), 0)
    # Keep the alpha mask soft so the final composite blends smoothly into the original skin.

    # 4. Non-AI Refinement (LAB Relighting, Specular Sheen, High-Pass Texture Injection)
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
    )

    # Alpha composite using the same blending_mask used for refinement
    alpha = blending_mask.astype(np.float32) / 255.0
    alpha_3c = alpha[:, :, np.newaxis]
    final_img = np.clip(
        refined_img.astype(np.float32) * alpha_3c + image.astype(np.float32) * (1.0 - alpha_3c),
        0.0, 255.0
    ).astype(np.uint8)

    # 6. Optional Before/After Contour Overlay
    if show_outline:
        overlay = final_img.copy()

        # Draw original cheek sub-zone contours
        if side in ("bilateral", "left"):
            cv2.polylines(
                overlay,
                [landmarks.left_all.astype(np.int32).reshape((-1, 1, 2))],
                isClosed=False,
                color=(255, 255, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )
            # Mark original left apex
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
            # Mark original right apex
            cv2.circle(
                overlay,
                (int(landmarks.right_apex[0]), int(landmarks.right_apex[1])),
                3,
                (0, 230, 255),
                -1,
                lineType=cv2.LINE_AA,
            )

        alpha = 0.65
        final_img = cv2.addWeighted(overlay, alpha, final_img, 1.0 - alpha, 0)

    return final_img


async def run_cheeks_simulation(
    image: np.ndarray,
    config: CheeksSimulationConfig,
) -> CheeksSimulationResult:
    """Async wrapper executing the cheeks simulation pipeline."""
    try:
        result_img = run_cheeks_pipeline(
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
            image=result_img,
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