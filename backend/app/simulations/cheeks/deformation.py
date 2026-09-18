"""
Controlled cheek deformation engine.

Translates volume parameters (CK1, CK2, CK3) into physical mesh displacements
using Gaussian Radial Basis Functions (RBF) and Thin Plate Splines (TPS)
with dynamic anatomical outward vectors and coordinate normalization.
"""

from __future__ import annotations

import cv2
import numpy as np
from scipy.interpolate import Rbf

from app.simulations.cheeks.landmarks import CheekLandmarks


def _normalize_vec(v: np.ndarray) -> np.ndarray:
    """Normalizes a 2D vector to unit length."""
    norm = np.linalg.norm(v)
    if norm < 1e-7:
        return np.zeros_like(v)
    return v / norm


def apply_cheek_deformation(
    image: np.ndarray,
    landmarks: CheekLandmarks,
    *,
    lateral_volume_ck1: float = 1.0,
    medial_volume_ck2: float = 0.5,
    submalar_volume_ck3: float = 0.0,
    asymmetry_mode: bool = False,
    left_cheek_multiplier: float = 1.0,
    right_cheek_multiplier: float = 1.0,
    skin_elasticity: float = 1.0,
    side: str = "bilateral",
) -> tuple[np.ndarray, np.ndarray, tuple[np.ndarray, np.ndarray]]:
    """
    Applies intensity-controlled geometric deformation to simulate midface volume enhancement.

    Args:
        image: Source image (HxWx3 uint8 BGR).
        landmarks: CheekLandmarks object containing anatomical sub-zone coordinates and anchors.
        lateral_volume_ck1: CK1 volume (0.0 to 2.5 mL).
        medial_volume_ck2: CK2 volume (0.0 to 2.5 mL).
        submalar_volume_ck3: CK3 volume (0.0 to 2.0 mL).
        asymmetry_mode: If False, both sides use 1.0 multiplier. If True, uses left/right multipliers.
        left_cheek_multiplier: Scale factor for left cheek volume.
        right_cheek_multiplier: Scale factor for right cheek volume.
        skin_elasticity: Kernel spread radius scale (0.8 to 1.2).
        side: 'left', 'right', or 'bilateral'.

    Returns:
        tuple containing:
            - Deformed image (HxWx3 uint8 BGR).
            - Updated left and right deformed malar apex positions (for relighting).
            - Destination control points for overlay rendering.
    """
    h, w = image.shape[:2]

    # Effective multipliers
    mult_left = left_cheek_multiplier if asymmetry_mode else 1.0
    mult_right = right_cheek_multiplier if asymmetry_mode else 1.0

    if side == "left":
        mult_right = 0.0
    elif side == "right":
        mult_left = 0.0

    # Scale reference from facial size
    eye_l = landmarks.anchors[0]  # Left eye outer (idx 33)
    eye_r = landmarks.anchors[2]  # Right eye outer (idx 263)
    inter_ocular_dist = max(float(np.linalg.norm(eye_r - eye_l)), 30.0)
    face_scale = inter_ocular_dist / 140.0

    # Base kernel spread sigma scaled by skin elasticity
    base_sigma = 35.0 * face_scale
    sigma = base_sigma * max(0.8, min(1.2, skin_elasticity))

    # Pixel displacement per mL (natural anatomical calibration)
    px_per_ml = 22.0 * face_scale

    nose_bridge = landmarks.nose_bridge.astype(np.float64)

    static_dirs = {
        "left": {
            "ck1": np.array([-0.10, -0.04]),
            "ck2": np.array([-0.46, -0.18]),
            "ck3": np.array([-0.52, 0.38]),
        },
        "right": {
            "ck1": np.array([0.10, -0.04]),
            "ck2": np.array([0.46, -0.18]),
            "ck3": np.array([0.52, 0.38]),
        },
    }

    # Face-local basis so the "static" component rotates with head pose instead
    # of assuming an upright, frontal face. face_x_axis points left-eye -> right-eye;
    # face_y_axis is the corresponding "down" direction for this head's tilt.
    face_x_axis = _normalize_vec((eye_r - eye_l).astype(np.float64))
    if np.allclose(face_x_axis, 0.0):
        face_x_axis = np.array([1.0, 0.0])
    face_y_axis = np.array([-face_x_axis[1], face_x_axis[0]])

    def get_blended_vector(pt: np.ndarray, side_key: str, zone_key: str) -> np.ndarray:
        dynamic_v = _normalize_vec(pt - nose_bridge)
        local = static_dirs[side_key][zone_key]
        static_v = _normalize_vec(local[0] * face_x_axis + local[1] * face_y_axis)
        blended = 0.5 * dynamic_v + 0.5 * static_v
        return _normalize_vec(blended)

    src_list: list[np.ndarray] = []
    dst_list: list[np.ndarray] = []

    def process_zone(
        pts: np.ndarray,
        vol: float,
        side_key: str,
        zone_key: str,
        multiplier: float,
        lateral_floor: float = 0.18,
        max_disp_px: float = 14.0,
    ) -> tuple[int, int]:
        """Appends points and returns the start and end index slice in dst_list."""
        start_idx = len(dst_list)
        eff_vol = vol * multiplier
        if eff_vol <= 0:
            for p in pts:
                src_list.append(p.astype(np.float64))
                dst_list.append(p.astype(np.float64))
            return start_idx, len(dst_list)

        center = np.mean(pts, axis=0)
        for p in pts:
            pf = p.astype(np.float64)
            d = np.linalg.norm(pf - center)
            nose_dx = abs(float(pf[0] - nose_bridge[0]))
            lateral_guard = np.clip(1.0 - (nose_dx / max(36.0, w * 0.16)), 0.0, 1.0)
            falloff = np.exp(-(d ** 2) / (2.0 * (sigma ** 2)))
            disp_mag = eff_vol * px_per_ml * falloff * (lateral_floor + (1.0 - lateral_floor) * lateral_guard)
            disp_mag = min(float(disp_mag), max_disp_px * face_scale )
            u = get_blended_vector(pf, side_key, zone_key)
            displacement = disp_mag * u

            src_list.append(pf)
            dst_list.append(pf + displacement)

        return start_idx, len(dst_list)

    # Process Zones and track apex indices directly
    _, _ = process_zone(landmarks.left_ck1, lateral_volume_ck1, "left", "ck1", mult_left, lateral_floor=0.75, max_disp_px=10.0)
    l_ck2_start, l_ck2_end = process_zone(landmarks.left_ck2, medial_volume_ck2, "left", "ck2", mult_left)
    _, _ = process_zone(landmarks.left_ck3, submalar_volume_ck3, "left", "ck3", mult_left)

    _, _ = process_zone(landmarks.right_ck1, lateral_volume_ck1, "right", "ck1", mult_right, lateral_floor=0.75, max_disp_px=10.0)
    r_ck2_start, r_ck2_end = process_zone(landmarks.right_ck2, medial_volume_ck2, "right", "ck2", mult_right)
    _, _ = process_zone(landmarks.right_ck3, submalar_volume_ck3, "right", "ck3", mult_right)

    # Compute malar apex displacements safely
    left_apex_disp = np.mean(dst_list[l_ck2_start:l_ck2_end], axis=0)
    right_apex_disp = np.mean(dst_list[r_ck2_start:r_ck2_end], axis=0)

    # Rigid anchors (Zero displacement)
    for anchor in landmarks.anchors:
        af = anchor.astype(np.float64)
        src_list.append(af)
        dst_list.append(af)

    src_arr = np.array(src_list, dtype=np.float64)
    dst_arr = np.array(dst_list, dtype=np.float64)

    # ROI Calculation
    x_min = max(0, int(np.min(src_arr[:, 0]) - 50))
    x_max = min(w, int(np.max(src_arr[:, 0]) + 50))
    y_min = max(0, int(np.min(src_arr[:, 1]) - 50))
    y_max = min(h, int(np.max(src_arr[:, 1]) + 50))

    roi_w = x_max - x_min
    roi_h = y_max - y_min
    if roi_w < 10 or roi_h < 10:
        return image.copy(), (landmarks.left_apex, landmarks.right_apex), (src_arr, dst_arr)

    # Perimeter anchor freeze
    n_roi_freeze = 8
    roi_freeze_x = np.linspace(x_min, x_max, n_roi_freeze)
    roi_freeze_y = np.linspace(y_min, y_max, n_roi_freeze)

    perimeter_pts = []
    for fx in roi_freeze_x:
        perimeter_pts.append([fx, float(y_min)])
        perimeter_pts.append([fx, float(y_max)])
    for fy in roi_freeze_y:
        perimeter_pts.append([float(x_min), fy])
        perimeter_pts.append([float(x_max), fy])

    perimeter_arr = np.array(perimeter_pts, dtype=np.float64)
    src_arr = np.vstack([src_arr, perimeter_arr])
    dst_arr = np.vstack([dst_arr, perimeter_arr])

    # Deduplicate paired points across both arrays together
    combined = np.hstack([src_arr, dst_arr])
    _, unique_indices = np.unique(combined, axis=0, return_index=True)
    src_arr = src_arr[unique_indices]
    dst_arr = dst_arr[unique_indices]

    if len(src_arr) < 4:
        return image.copy(), (left_apex_disp, right_apex_disp), (src_arr, dst_arr)

    # Uniform aspect-ratio normalization scale factor
    max_dim = max(float(w), float(h))
    src_norm = src_arr / max_dim
    dst_norm = dst_arr / max_dim

    grid_x_local, grid_y_local = np.meshgrid(
        np.arange(roi_w, dtype=np.float64),
        np.arange(roi_h, dtype=np.float64),
    )
    grid_x_abs = (grid_x_local + x_min) / max_dim
    grid_y_abs = (grid_y_local + y_min) / max_dim

    # INVERTED RBF FIT: Inputs are dst_norm (output image space), outputs are src_norm (source image space)
    rbf_x = Rbf(dst_norm[:, 0], dst_norm[:, 1], src_norm[:, 0], function="multiquadric", smooth=1e-3)
    rbf_y = Rbf(dst_norm[:, 0], dst_norm[:, 1], src_norm[:, 1], function="multiquadric", smooth=1e-3)

    src_x_res = rbf_x(grid_x_abs, grid_y_abs) * max_dim
    src_y_res = rbf_y(grid_x_abs, grid_y_abs) * max_dim

    map_x = (src_x_res - x_min).astype(np.float32)
    map_y = (src_y_res - y_min).astype(np.float32)

    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(
        roi,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )

    deformed_img = image.copy()
    deformed_img[y_min:y_max, x_min:x_max] = warped_roi

    return deformed_img, (left_apex_disp, right_apex_disp), (src_arr, dst_arr)