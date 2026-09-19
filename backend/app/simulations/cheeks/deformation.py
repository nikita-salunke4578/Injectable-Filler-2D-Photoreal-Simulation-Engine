"""
Controlled cheek deformation engine with isolated per-side processing.

Translates volume parameters (CK1, CK2, CK3) into physical mesh displacements
using Gaussian Radial Basis Functions (RBF) scoped strictly to active cheek ROIs,
restoring exact unwarped pixels if a glasses mask is supplied.
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


def _perimeter_points(x_min: int, x_max: int, y_min: int, y_max: int, n: int = 6) -> np.ndarray:
    """Generates perimeter freeze points around an ROI boundary."""
    roi_freeze_x = np.linspace(x_min, x_max, n)
    roi_freeze_y = np.linspace(y_min, y_max, n)
    pts = []
    for fx in roi_freeze_x:
        pts.append([fx, float(y_min)])
        pts.append([fx, float(y_max)])
    for fy in roi_freeze_y:
        pts.append([float(x_min), fy])
        pts.append([float(x_max), fy])
    return np.array(pts, dtype=np.float64)


def _process_side(
    image: np.ndarray,
    side_key: str,
    ck1_pts: np.ndarray,
    ck2_pts: np.ndarray,
    ck3_pts: np.ndarray,
    lateral_volume_ck1: float,
    medial_volume_ck2: float,
    submalar_volume_ck3: float,
    multiplier: float,
    nose_bridge: np.ndarray,
    face_x_axis: np.ndarray,
    face_y_axis: np.ndarray,
    sigma: float,
    px_per_ml: float,
    face_scale: float,
    local_anchors: np.ndarray,
    w: int,
    h: int,
    glasses_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, float, tuple[int, int, int, int]]:
    """Applies geometric deformation isolated strictly to a single side's local ROI."""
    src_list: list[np.ndarray] = []
    dst_list: list[np.ndarray] = []

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

    def get_blended_vector(pt: np.ndarray, zone_key: str) -> np.ndarray:
        dynamic_v = _normalize_vec(pt - nose_bridge)
        local = static_dirs[side_key][zone_key]
        static_v = _normalize_vec(local[0] * face_x_axis + local[1] * face_y_axis)
        blended = 0.5 * dynamic_v + 0.5 * static_v
        return _normalize_vec(blended)

    def process_zone(
        pts: np.ndarray,
        vol: float,
        zone_key: str,
        lateral_floor: float = 0.18,
        max_disp_px: float = 14.0,
    ) -> tuple[int, int]:
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
            disp_mag = min(float(disp_mag), max_disp_px * face_scale)
            u = get_blended_vector(pf, zone_key)
            displacement = disp_mag * u

            src_list.append(pf)
            dst_list.append(pf + displacement)

        return start_idx, len(dst_list)

    # Process individual sub-zones
    _, _ = process_zone(ck1_pts, lateral_volume_ck1, "ck1", lateral_floor=0.75, max_disp_px=10.0)
    ck2_start, ck2_end = process_zone(ck2_pts, medial_volume_ck2, "ck2")
    _, _ = process_zone(ck3_pts, submalar_volume_ck3, "ck3")

    apex_disp = np.mean(dst_list[ck2_start:ck2_end], axis=0)
    orig_apex = np.mean(ck2_pts, axis=0)
    shift_px = float(np.linalg.norm(apex_disp - orig_apex))

    # Freeze local anatomical anchors
    for anchor in local_anchors:
        af = anchor.astype(np.float64)
        src_list.append(af)
        dst_list.append(af)

    src_arr = np.array(src_list, dtype=np.float64)
    dst_arr = np.array(dst_list, dtype=np.float64)

    # Local ROI Calculation
    x_min = max(0, int(np.min(src_arr[:, 0]) - 40))
    x_max = min(w, int(np.max(src_arr[:, 0]) + 40))
    y_min = max(0, int(np.min(src_arr[:, 1]) - 40))
    y_max = min(h, int(np.max(src_arr[:, 1]) + 40))

    roi_w = x_max - x_min
    roi_h = y_max - y_min
    if roi_w < 10 or roi_h < 10:
        return image[y_min:y_max, x_min:x_max].copy(), orig_apex, 0.0, (x_min, x_max, y_min, y_max)

    # Freeze perimeter around local ROI
    perim_pts = _perimeter_points(x_min, x_max, y_min, y_max, n=6)
    src_arr = np.vstack([src_arr, perim_pts])
    dst_arr = np.vstack([dst_arr, perim_pts])

    # Deduplicate paired control points
    combined = np.hstack([src_arr, dst_arr])
    _, unique_indices = np.unique(combined, axis=0, return_index=True)
    src_arr = src_arr[unique_indices]
    dst_arr = dst_arr[unique_indices]

    if len(src_arr) < 4:
        return image[y_min:y_max, x_min:x_max].copy(), orig_apex, 0.0, (x_min, x_max, y_min, y_max)

    # Uniform aspect-ratio normalization
    max_dim = max(float(w), float(h))
    src_norm = src_arr / max_dim
    dst_norm = dst_arr / max_dim

    grid_x_local, grid_y_local = np.meshgrid(
        np.arange(roi_w, dtype=np.float64),
        np.arange(roi_h, dtype=np.float64),
    )
    grid_x_abs = (grid_x_local + x_min) / max_dim
    grid_y_abs = (grid_y_local + y_min) / max_dim

    # Inverted RBF Fit scoped to this side's ROI
    rbf_x = Rbf(dst_norm[:, 0], dst_norm[:, 1], src_norm[:, 0], function="multiquadric", smooth=1e-3)
    rbf_y = Rbf(dst_norm[:, 0], dst_norm[:, 1], src_norm[:, 1], function="multiquadric", smooth=1e-3)

    src_x_res = rbf_x(grid_x_abs, grid_y_abs) * max_dim
    src_y_res = rbf_y(grid_x_abs, grid_y_abs) * max_dim

    map_x = (src_x_res - x_min).astype(np.float32)
    map_y = (src_y_res - y_min).astype(np.float32)

    # Clip mapping coordinates strictly within local ROI boundaries
    map_x = np.clip(map_x, 0.0, float(roi_w - 1))
    map_y = np.clip(map_y, 0.0, float(roi_h - 1))

    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(
        roi,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )

    # Apply Hard Glasses Pixel Restoration if glasses_mask exists
    if glasses_mask is not None:
        local_glasses_mask = glasses_mask[y_min:y_max, x_min:x_max]
        protected_warped_roi = warped_roi.copy()
        protected_warped_roi[local_glasses_mask > 0] = roi[local_glasses_mask > 0]
        return protected_warped_roi, apex_disp, shift_px, (x_min, x_max, y_min, y_max)

    return warped_roi, apex_disp, shift_px, (x_min, x_max, y_min, y_max)


def apply_cheek_deformation(
    image: np.ndarray,
    landmarks: CheekLandmarks,
    *,
    glasses_mask: np.ndarray | None = None,
    lateral_volume_ck1: float = 1.0,
    medial_volume_ck2: float = 0.5,
    submalar_volume_ck3: float = 0.0,
    asymmetry_mode: bool = False,
    left_cheek_multiplier: float = 1.0,
    right_cheek_multiplier: float = 1.0,
    skin_elasticity: float = 1.0,
    side: str = "bilateral",
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray], tuple[float, float], tuple[np.ndarray, np.ndarray]]:
    """
    Applies per-side isolated geometric deformation to simulate midface volume enhancement.
    """
    h, w = image.shape[:2]
    deformed_img = image.copy()

    mult_left = left_cheek_multiplier if asymmetry_mode else 1.0
    mult_right = right_cheek_multiplier if asymmetry_mode else 1.0

    eye_l = landmarks.anchors[0]
    eye_r = landmarks.anchors[2]
    inter_ocular_dist = max(float(np.linalg.norm(eye_r - eye_l)), 30.0)
    face_scale = inter_ocular_dist / 140.0

    base_sigma = 35.0 * face_scale
    sigma = base_sigma * max(0.8, min(1.2, skin_elasticity))
    px_per_ml = 22.0 * face_scale

    nose_bridge = landmarks.nose_bridge.astype(np.float64)

    face_x_axis = _normalize_vec((eye_r - eye_l).astype(np.float64))
    if np.allclose(face_x_axis, 0.0):
        face_x_axis = np.array([1.0, 0.0])
    face_y_axis = np.array([-face_x_axis[1], face_x_axis[0]])

    left_apex_disp = landmarks.left_apex.copy()
    right_apex_disp = landmarks.right_apex.copy()
    left_shift_px = 0.0
    right_shift_px = 0.0

    if side in ("bilateral", "left"):
        warped_l, left_apex_disp, left_shift_px, (x0, x1, y0, y1) = _process_side(
            image=image,
            side_key="left",
            ck1_pts=landmarks.left_ck1,
            ck2_pts=landmarks.left_ck2,
            ck3_pts=landmarks.left_ck3,
            lateral_volume_ck1=lateral_volume_ck1,
            medial_volume_ck2=medial_volume_ck2,
            submalar_volume_ck3=submalar_volume_ck3,
            multiplier=mult_left,
            nose_bridge=nose_bridge,
            face_x_axis=face_x_axis,
            face_y_axis=face_y_axis,
            sigma=sigma,
            px_per_ml=px_per_ml,
            face_scale=face_scale,
            local_anchors=landmarks.left_local_anchors,
            w=w,
            h=h,
            glasses_mask=glasses_mask,
        )
        deformed_img[y0:y1, x0:x1] = warped_l

    if side in ("bilateral", "right"):
        warped_r, right_apex_disp, right_shift_px, (x0, x1, y0, y1) = _process_side(
            image=image,
            side_key="right",
            ck1_pts=landmarks.right_ck1,
            ck2_pts=landmarks.right_ck2,
            ck3_pts=landmarks.right_ck3,
            lateral_volume_ck1=lateral_volume_ck1,
            medial_volume_ck2=medial_volume_ck2,
            submalar_volume_ck3=submalar_volume_ck3,
            multiplier=mult_right,
            nose_bridge=nose_bridge,
            face_x_axis=face_x_axis,
            face_y_axis=face_y_axis,
            sigma=sigma,
            px_per_ml=px_per_ml,
            face_scale=face_scale,
            local_anchors=landmarks.right_local_anchors,
            w=w,
            h=h,
            glasses_mask=glasses_mask,
        )
        deformed_img[y0:y1, x0:x1] = warped_r

    return (
        deformed_img,
        (left_apex_disp, right_apex_disp),
        (left_shift_px, right_shift_px),
        (landmarks.anchors, landmarks.anchors),
    )