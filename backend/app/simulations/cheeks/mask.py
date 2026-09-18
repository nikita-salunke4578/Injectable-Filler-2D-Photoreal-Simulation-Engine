"""
Cheek treatment region mask generation with orbital safety cage.

Constructs soft-feathered ROI masks isolating the cheek region
and subtracting lower eyelid / tear trough exclusion zones to prevent
ghosting or dark smudges during Poisson cloning.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks


def build_cheek_mask(
    image_shape: tuple[int, ...],
    landmarks: CheekLandmarks,
    *,
    side: str = "bilateral",
    feather_radius: int = 25,
    dilate_px: int = 14,
) -> np.ndarray:
    """
    Builds a soft-feathered uint8 mask (0-255) for the cheek treatment region.

    Args:
        image_shape: Shape of the image (H, W) or (H, W, C).
        landmarks: CheekLandmarks dataclass containing cheek points and exclusion cages.
        side: 'left', 'right', or 'bilateral'.
        feather_radius: Gaussian blur kernel size for smooth boundary blending.
        dilate_px: Morphological dilation radius in pixels.

    Returns:
        np.ndarray of shape (H, W), dtype uint8 with values 0 to 255.
    """
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    include_left = side in ("bilateral", "left")
    include_right = side in ("bilateral", "right")

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1)
    )

    # 1. Fill cheek polygon convex hulls, but keep them within the facial bounds to avoid
    # white background bleed from a dilated temple/hairline region.
    face_bounds = np.vstack([landmarks.anchors, landmarks.left_all, landmarks.right_all]).astype(np.float32)
    min_x = max(0, int(np.min(face_bounds[:, 0])) - 20)
    max_x = min(w - 1, int(np.max(face_bounds[:, 0])) + 20)
    min_y = max(0, int(np.min(face_bounds[:, 1])) - 20)
    max_y = min(h - 1, int(np.max(face_bounds[:, 1])) + 20)
    face_box = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(face_box, (min_x, min_y), (max_x, max_y), 255, -1)

    if include_left and len(landmarks.left_all) >= 3:
        left_hull = cv2.convexHull(landmarks.left_all.astype(np.int32))
        left_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(left_mask, left_hull, 255)
        left_mask = cv2.dilate(left_mask, kernel, iterations=1)
        left_mask = cv2.bitwise_and(left_mask, face_box)
        mask = cv2.bitwise_or(mask, left_mask)

    if include_right and len(landmarks.right_all) >= 3:
        right_hull = cv2.convexHull(landmarks.right_all.astype(np.int32))
        right_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(right_mask, right_hull, 255)
        right_mask = cv2.dilate(right_mask, kernel, iterations=1)
        right_mask = cv2.bitwise_and(right_mask, face_box)
        mask = cv2.bitwise_or(mask, right_mask)

    # 2. Eyelid & Tear Trough Safety Cage: Explicitly subtract lower orbit exclusion zones
    exclusion_mask = np.zeros((h, w), dtype=np.uint8)
    excl_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    if include_left and len(landmarks.left_eye_exclusion) >= 3:
        excl_left_hull = cv2.convexHull(landmarks.left_eye_exclusion.astype(np.int32))
        cv2.fillConvexPoly(exclusion_mask, excl_left_hull, 255)

    if include_right and len(landmarks.right_eye_exclusion) >= 3:
        excl_right_hull = cv2.convexHull(landmarks.right_eye_exclusion.astype(np.int32))
        cv2.fillConvexPoly(exclusion_mask, excl_right_hull, 255)

    # Dilate exclusion mask slightly to ensure complete clearance from lower lash line
    if np.any(exclusion_mask > 0):
        exclusion_mask = cv2.dilate(exclusion_mask, excl_kernel, iterations=1)
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(exclusion_mask))

    # 3. Feather in floating-point space so the mask transitions smoothly instead of
    # creating a hard sticker-like cutout at the lateral edge.
    mask_f = mask.astype(np.float32) / 255.0
    if feather_radius > 0:
        ksize = feather_radius if feather_radius % 2 == 1 else feather_radius + 1
        mask_f = cv2.GaussianBlur(mask_f, (ksize, ksize), 0)

    # 4. Fade relative to the detected face bounds (min_x/max_x, computed above from
    # landmarks.anchors + left_all/right_all) so the transition stays on the face and
    # does not spill into the white studio background.
    fade_band_px = max(12, int((max_x - min_x) * 0.12))
    if fade_band_px > 0:
        x_coords = np.arange(w, dtype=np.float32)
        left_fade = np.clip((x_coords - min_x) / fade_band_px, 0.0, 1.0)
        right_fade = np.clip((max_x - x_coords) / fade_band_px, 0.0, 1.0)
        left_fade = (1.0 - np.cos(left_fade * np.pi)) * 0.5
        right_fade = (1.0 - np.cos(right_fade * np.pi)) * 0.5
        lateral_weight = np.minimum(left_fade, right_fade)
        lateral_weight = np.tile(lateral_weight[np.newaxis, :], (h, 1))
        mask_f = mask_f * lateral_weight

    if feather_radius > 0:
        soft_ksize = max(45, (feather_radius * 2) + 1)
        if soft_ksize % 2 == 0:
            soft_ksize += 1
        mask_f = cv2.GaussianBlur(mask_f, (soft_ksize, soft_ksize), 0)

    return (np.clip(mask_f, 0.0, 1.0) * 255.0).astype(np.uint8)
