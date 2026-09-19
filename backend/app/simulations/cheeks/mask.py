"""
Cheek treatment region mask generation with orbital safety cage, per-zone isolation,
and explicit glasses occlusion subtraction.

Constructs soft-feathered ROI masks isolating active treatment sub-zones (CK1, CK2, CK3),
subtracting lower eyelid / tear trough exclusion zones and detected glasses masks.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks


def _zone_mask(pts: np.ndarray, h: int, w: int, kernel: np.ndarray) -> np.ndarray:
    """Generates a dilated convex hull mask for a specific landmark point set."""
    m = np.zeros((h, w), dtype=np.uint8)
    if len(pts) >= 3:
        hull = cv2.convexHull(pts.astype(np.int32))
        cv2.fillConvexPoly(m, hull, 255)
        m = cv2.dilate(m, kernel, iterations=1)
    return m


def build_cheek_mask(
    image_shape: tuple[int, ...],
    landmarks: CheekLandmarks,
    *,
    glasses_mask: np.ndarray | None = None,
    side: str = "bilateral",
    zone_active: dict[str, bool] | None = None,
    feather_radius: int = 25,
    dilate_px: int = 8,
) -> np.ndarray:
    """
    Builds a soft-feathered uint8 mask (0-255) for active cheek treatment zones.

    Args:
        image_shape: Shape of the image (H, W) or (H, W, C).
        landmarks: CheekLandmarks dataclass instance.
        glasses_mask: Optional binary mask (255 where glasses exist, 0 elsewhere).
        side: 'left', 'right', or 'bilateral'.
        zone_active: Optional dictionary controlling active sub-zones.
        feather_radius: Gaussian blur kernel size for smooth boundary blending.
        dilate_px: Morphological dilation radius in pixels.

    Returns:
        np.ndarray of shape (H, W), dtype uint8 with values 0 to 255.
    """
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    zone_active = zone_active or {}

    include_left = side in ("bilateral", "left")
    include_right = side in ("bilateral", "right")

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1)
    )

    # Calculate facial bounding box for lateral boundary weighting
    face_bounds = np.vstack([landmarks.anchors, landmarks.left_all, landmarks.right_all]).astype(np.float32)
    min_x = max(0, int(np.min(face_bounds[:, 0])) - 20)
    max_x = min(w - 1, int(np.max(face_bounds[:, 0])) + 20)

    face_box = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(face_box, (min_x, 0), (max_x, h - 1), 255, -1)

    # 1. Build per-sub-zone masks independently
    if include_left:
        left_mask = np.zeros((h, w), dtype=np.uint8)
        if zone_active.get("left_ck1", True):
            left_mask |= _zone_mask(landmarks.left_ck1, h, w, kernel)
        if zone_active.get("left_ck2", True):
            left_mask |= _zone_mask(landmarks.left_ck2, h, w, kernel)
        if zone_active.get("left_ck3", True):
            left_mask |= _zone_mask(landmarks.left_ck3, h, w, kernel)
        left_mask = cv2.bitwise_and(left_mask, face_box)
        mask = cv2.bitwise_or(mask, left_mask)

    if include_right:
        right_mask = np.zeros((h, w), dtype=np.uint8)
        if zone_active.get("right_ck1", True):
            right_mask |= _zone_mask(landmarks.right_ck1, h, w, kernel)
        if zone_active.get("right_ck2", True):
            right_mask |= _zone_mask(landmarks.right_ck2, h, w, kernel)
        if zone_active.get("right_ck3", True):
            right_mask |= _zone_mask(landmarks.right_ck3, h, w, kernel)
        right_mask = cv2.bitwise_and(right_mask, face_box)
        mask = cv2.bitwise_or(mask, right_mask)

    # 2. Eyelid & Tear Trough Safety Cage: Subtract lower orbit exclusion zones
    exclusion_mask = np.zeros((h, w), dtype=np.uint8)
    excl_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    if include_left and len(landmarks.left_eye_exclusion) >= 3:
        excl_left_hull = cv2.convexHull(landmarks.left_eye_exclusion.astype(np.int32))
        cv2.fillConvexPoly(exclusion_mask, excl_left_hull, 255)

    if include_right and len(landmarks.right_eye_exclusion) >= 3:
        excl_right_hull = cv2.convexHull(landmarks.right_eye_exclusion.astype(np.int32))
        cv2.fillConvexPoly(exclusion_mask, excl_right_hull, 255)

    if np.any(exclusion_mask > 0):
        exclusion_mask = cv2.dilate(exclusion_mask, excl_kernel, iterations=1)
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(exclusion_mask))

    # 3. Glasses Occlusion Subtraction
    if glasses_mask is not None:
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(glasses_mask))

    # 4. Soft boundary feathering
    mask_f = mask.astype(np.float32) / 255.0
    if feather_radius > 0:
        ksize = feather_radius if feather_radius % 2 == 1 else feather_radius + 1
        mask_f = cv2.GaussianBlur(mask_f, (ksize, ksize), 0)

    # 5. Lateral boundary fade
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