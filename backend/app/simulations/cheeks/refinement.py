"""
Cheek region physical relighting, specular sheen, and high-pass texture injection.

Recreates natural 3D surface shading and skin pore preservation driven
by physical displacement distance without spatial mask dependency risks.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks


def refine_cheek_region(
    deformed_image: np.ndarray,
    mask: np.ndarray,
    landmarks: CheekLandmarks,
    apexes: tuple[np.ndarray, np.ndarray],
    original_image: np.ndarray,
    *,
    medial_volume_ck2: float = 0.5,
    submalar_volume_ck3: float = 0.0,
    asymmetry_mode: bool = False,
    left_multiplier: float = 1.0,
    right_multiplier: float = 1.0,
    side: str = "bilateral",
    shifts_px: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """
    Applies physics-based relighting and texture injection scaled directly by displacement magnitude.

    Args:
        deformed_image: Warped BGR image (HxWx3 uint8).
        mask: Feathered cheek mask (HxW uint8 0-255).
        landmarks: CheekLandmarks dataclass.
        apexes: (left_apex_disp, right_apex_disp) pixel coordinates of deformed peaks.
        original_image: Original unmodified BGR image for high-pass texture extraction.
        medial_volume_ck2: CK2 volume in mL.
        submalar_volume_ck3: CK3 volume in mL.
        asymmetry_mode: Whether asymmetry multipliers apply.
        left_multiplier: Left cheek multiplier.
        right_multiplier: Right cheek multiplier.
        side: 'left', 'right', or 'bilateral'.
        shifts_px: Physical apex displacement distance in pixels (left_shift_px, right_shift_px).

    Returns:
        Refined BGR image (HxWx3 uint8).
    """
    h, w = deformed_image.shape[:2]
    mask_norm = (mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

    include_left = side in ("bilateral", "left")
    include_right = side in ("bilateral", "right")

    left_apex, right_apex = apexes
    left_shift_px, right_shift_px = shifts_px

    # 1. LAB Lightness Relighting
    lab = cv2.cvtColor(deformed_image, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_channel = lab[:, :, 0]

    grid_y, grid_x = np.indices((h, w), dtype=np.float32)

    eye_dist = max(float(np.linalg.norm(landmarks.anchors[2] - landmarks.anchors[0])), 30.0)
    face_scale = eye_dist / 140.0
    apex_radius = 28.0 * face_scale

    nose_x = float(landmarks.nose_bridge[0])
    half_w = float(w) * 0.5
    x_dist_from_center = np.abs(grid_x - nose_x)
    max_lateral_reach = half_w * 0.24
    lateral_decay = np.clip(1.0 - (x_dist_from_center / max_lateral_reach), 0.0, 1.0)
    lateral_decay = (1.0 - np.cos(lateral_decay * np.pi)) * 0.5

    # Derive highlight intensity directly from physical surface displacement magnitude
    boost_left = (min(0.10, 0.02 + 0.006 * left_shift_px) if include_left and left_shift_px > 0.1 else 0.0)
    d2_left = (grid_x - left_apex[0]) ** 2 + (grid_y - left_apex[1]) ** 2
    hl_map_left = np.exp(-d2_left / (2.0 * (apex_radius ** 2))) * lateral_decay

    boost_right = (min(0.10, 0.02 + 0.006 * right_shift_px) if include_right and right_shift_px > 0.1 else 0.0)
    d2_right = (grid_x - right_apex[0]) ** 2 + (grid_y - right_apex[1]) ** 2
    hl_map_right = np.exp(-d2_right / (2.0 * (apex_radius ** 2))) * lateral_decay

    combined_hl = boost_left * hl_map_left + boost_right * hl_map_right
    combined_hl = np.clip(combined_hl, 0.0, 1.0)

    # Multiplicative L channel brightening
    MAX_BOOST = 0.035
    l_channel_boosted = l_channel * (1.0 + MAX_BOOST * combined_hl * mask_norm[:, :, 0])
    lab[:, :, 0] = np.clip(l_channel_boosted, 0.0, 255.0)
    relit = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    # 2. High-Pass Texture Injection (Pore & Skin Detail Restoration)
    blurred_orig = cv2.GaussianBlur(original_image, (5, 5), 1.2)
    high_pass = original_image.astype(np.float32) - blurred_orig.astype(np.float32)

    texture_weight = 0.35
    textured = relit.astype(np.float32) + texture_weight * high_pass * mask_norm
    textured = np.clip(textured, 0.0, 255.0).astype(np.uint8)

    refined = (textured.astype(np.float32) * mask_norm + deformed_image.astype(np.float32) * (1.0 - mask_norm)).astype(np.uint8)

    return refined