"""
Cheek region physical relighting, specular sheen, and high-pass texture injection.

Recreates natural 3D surface shading and skin pore preservation
without generative AI or plastic blurring artifacts.
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
) -> np.ndarray:
    """
    Applies non-AI physics-based shading, specular highlight, and high-pass texture injection.

    Stages:
    1. LAB Lightness adjustment: Brightens the apex (+5-10%) and casts subtle shadow beneath zygoma.
    2. Micro specular highlight: localized taut skin reflection at CK2 apex.
    3. High-pass texture injection: preserves original skin pores and micro-texture.

    Args:
        deformed_image: Warped BGR image (HxWx3 uint8).
        mask: Feathered cheek mask (HxW uint8 0-255).
        landmarks: CheekLandmarks dataclass.
        apexes: (left_apex_disp, right_apex_disp) pixel coordinates of deformed peaks.
        original_image: Original unmodified BGR image for pore extraction.
        medial_volume_ck2: CK2 volume in mL.
        submalar_volume_ck3: CK3 volume in mL.
        asymmetry_mode: Whether asymmetry multipliers apply.
        left_multiplier: Left cheek multiplier.
        right_multiplier: Right cheek multiplier.

    Returns:
        Refined BGR image (HxWx3 uint8).
    """
    h, w = deformed_image.shape[:2]
    mask_norm = (mask.astype(np.float32) / 255.0)[:, :, np.newaxis]

    m_left = left_multiplier if asymmetry_mode else 1.0
    m_right = right_multiplier if asymmetry_mode else 1.0

    left_apex, right_apex = apexes

    # 1. LAB Lightness Relighting
    lab = cv2.cvtColor(deformed_image, cv2.COLOR_BGR2LAB).astype(np.float32)
    l_channel = lab[:, :, 0]

    # Pre-generate pixel coordinate grids
    grid_y, grid_x = np.indices((h, w), dtype=np.float32)

    # Malar Apex highlight radius (~25-35px scaled by face size)
    eye_dist = max(float(np.linalg.norm(landmarks.anchors[2] - landmarks.anchors[0])), 30.0)
    face_scale = eye_dist / 140.0
    apex_radius = 28.0 * face_scale

    # Keep the highlight and shadow tightly centred on the malar region.
    nose_x = float(landmarks.nose_bridge[0])
    half_w = float(w) * 0.5
    x_dist_from_center = np.abs(grid_x - nose_x)
    max_lateral_reach = half_w * 0.24  # keep the relight strictly inside the malar area
    lateral_decay = np.clip(1.0 - (x_dist_from_center / max_lateral_reach), 0.0, 1.0)
    lateral_decay = (1.0 - np.cos(lateral_decay * np.pi)) * 0.5

    # Apex 1: Left cheek
    boost_left = min(0.10, 0.04 + 0.024 * (medial_volume_ck2 * m_left))
    d2_left = (grid_x - left_apex[0]) ** 2 + (grid_y - left_apex[1]) ** 2
    hl_map_left = np.exp(-d2_left / (2.0 * (apex_radius ** 2))) * lateral_decay

    # Apex 2: Right cheek
    boost_right = min(0.10, 0.04 + 0.024 * (medial_volume_ck2 * m_right))
    d2_right = (grid_x - right_apex[0]) ** 2 + (grid_y - right_apex[1]) ** 2
    hl_map_right = np.exp(-d2_right / (2.0 * (apex_radius ** 2))) * lateral_decay

    # Combined apex brightening map  — normalized 0..1
    combined_hl = boost_left * hl_map_left + boost_right * hl_map_right
    combined_hl = np.clip(combined_hl, 0.0, 1.0)

    # ── Multiplicative L relighting (safe for bright/light skin) ─────────────
    # ADDITIVE  (old):  L += delta * (255 - L)   → clips to 255 on light skin
    # MULTIPLICATIVE:   L *= (1 + boost * map)   → scales proportionally, never blows out
    MAX_BOOST = 0.035  # keep the apex highlight very subtle and local
    l_channel_boosted = l_channel * (1.0 + MAX_BOOST * combined_hl * mask_norm[:, :, 0])
    l_channel = np.clip(l_channel_boosted, 0.0, 255.0)
    # ─────────────────────────────────────────────────────────────────────────

    # Submalar soft shadow gradient: subtle drop shadow beneath the zygoma
    # Dark patch fix: the treatment region is intended to be a malar projection,
    # not a shadowed contour. The submalar shadow is removed entirely to avoid
    # a black/gray smudge appearing on the cheek side in studio lighting.
    left_sub_center = np.mean(landmarks.left_ck3, axis=0) + np.array([0, 12 * face_scale])
    right_sub_center = np.mean(landmarks.right_ck3, axis=0) + np.array([0, 12 * face_scale])

    # No-op shadow map: keep darkness at zero so the skin stays natural.
    combined_sh = np.zeros_like(l_channel, dtype=np.float32)
    l_channel = l_channel * (1.0 - 0.0 * combined_sh * mask_norm[:, :, 0])

    lab[:, :, 0] = np.clip(l_channel, 0.0, 255.0)
    relit = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)

    # 2. Specular Highlight — DISABLED for studio photos to prevent white glow
    # On a model with light skin against a white background, any additive white
    # sheen bleeds uncontrollably and adds to the white-flood artifact.
    # The LAB multiplicative brightening above already provides a natural apex highlight.
    # Uncomment and tune only for dark-skinned subjects on dark backgrounds.
    #
    # specular_radius = max(6.0 * face_scale, 4.0)
    # spec_map_l = np.exp(-d2_left / (2.0 * (specular_radius ** 2))) * lateral_decay
    # spec_map_r = np.exp(-d2_right / (2.0 * (specular_radius ** 2))) * lateral_decay
    # spec_alpha_l = min(0.10, 0.04 + 0.02 * (medial_volume_ck2 * m_left))
    # spec_alpha_r = min(0.10, 0.04 + 0.02 * (medial_volume_ck2 * m_right))
    # total_spec = (spec_alpha_l * spec_map_l + spec_alpha_r * spec_map_r)[:, :, np.newaxis]
    # total_spec = np.clip(total_spec * mask_norm, 0.0, 0.10)
    # sheen_color = np.array([255.0, 252.0, 248.0], dtype=np.float32)
    # relit_f = relit.astype(np.float32)
    # relit = np.clip(relit_f * (1.0 - total_spec) + sheen_color * total_spec, 0, 255).astype(np.uint8)

    # 3. High-Pass Texture Injection (Pore & Skin Detail Restoration)
    blurred_orig = cv2.GaussianBlur(original_image, (5, 5), 1.2)
    high_pass = original_image.astype(np.float32) - blurred_orig.astype(np.float32)

    # Inject high frequencies back into relit deformed image within treatment area
    texture_weight = 0.35
    textured = relit.astype(np.float32) + texture_weight * high_pass * mask_norm
    textured = np.clip(textured, 0.0, 255.0).astype(np.uint8)

    # Alpha blend textured patch smoothly with deformed image based on mask
    refined = (textured.astype(np.float32) * mask_norm + deformed_image.astype(np.float32) * (1.0 - mask_norm)).astype(np.uint8)

    return refined
