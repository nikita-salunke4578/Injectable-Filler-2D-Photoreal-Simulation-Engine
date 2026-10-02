"""
RBF-based cheek deformation engine.

Architecture
------------
Treatment volume
    ↓
Face-scale normalization
    ↓
CK1 / CK2 / CK3 control-point displacement
    ↓
Hard anatomical anchors
    ↓
Frozen local ROI perimeter
    ↓
Inverse RBF mapping
    ↓
OpenCV remap

Important
---------
The volume-to-pixel conversion is a visual calibration parameter.
It does NOT represent physical filler volume, tissue mechanics, or
true 3D volumetric conservation.
"""

from __future__ import annotations

import cv2
import numpy as np
from scipy.interpolate import Rbf

from app.simulations.cheeks.landmarks import CheekLandmarks


# ---------------------------------------------------------------------
# Visual calibration constants
# ---------------------------------------------------------------------

PX_PER_ML_AT_REFERENCE_FACE = 22.0

REFERENCE_INTEROCULAR_DISTANCE = 140.0

BASE_SIGMA_PX = 35.0

ROI_PADDING_PX = 40

MAX_CK1_DISPLACEMENT = 10.0
MAX_CK2_DISPLACEMENT = 14.0
MAX_CK3_DISPLACEMENT = 14.0

RBF_SMOOTH = 1e-3


def _normalize_vec(v: np.ndarray) -> np.ndarray:
    """Return a unit 2D vector."""

    v = np.asarray(v, dtype=np.float64)

    norm = float(np.linalg.norm(v))

    if norm < 1e-8:
        return np.zeros_like(v)

    return v / norm


def _face_scale(
    eye_left: np.ndarray,
    eye_right: np.ndarray,
) -> float:
    """
    Estimate image-relative face scale from inter-ocular distance.
    """

    eye_distance = max(
        float(np.linalg.norm(eye_right - eye_left)),
        30.0,
    )

    return eye_distance / REFERENCE_INTEROCULAR_DISTANCE


def _perimeter_points(
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    n: int = 8,
) -> np.ndarray:
    """
    Generate fixed perimeter control points.

    These points enforce zero displacement at the local ROI boundary
    and prevent the RBF field from freely drifting outside the treatment
    region.
    """

    x_values = np.linspace(
        x_min,
        x_max,
        n,
    )

    y_values = np.linspace(
        y_min,
        y_max,
        n,
    )

    points: list[list[float]] = []

    for x in x_values:
        points.append(
            [float(x), float(y_min)]
        )
        points.append(
            [float(x), float(y_max)]
        )

    for y in y_values:
        points.append(
            [float(x_min), float(y)]
        )
        points.append(
            [float(x_max), float(y)]
        )

    return np.asarray(
        points,
        dtype=np.float64,
    )


def _zone_direction(
    point: np.ndarray,
    zone: str,
    side: str,
    nose_bridge: np.ndarray,
    face_x_axis: np.ndarray,
    face_y_axis: np.ndarray,
) -> np.ndarray:
    """
    Calculate the desired displacement direction.

    Static anatomical vectors provide stability.
    A dynamic radial component adapts the vector to the actual face.
    """

    static_dirs = {
        "left": {
            "ck1": (-0.10, -0.04),
            "ck2": (-0.46, -0.18),
            "ck3": (-0.52, 0.38),
        },
        "right": {
            "ck1": (0.10, -0.04),
            "ck2": (0.46, -0.18),
            "ck3": (0.52, 0.38),
        },
    }

    local_x, local_y = static_dirs[side][zone]

    static_vector = (
        local_x * face_x_axis
        + local_y * face_y_axis
    )

    static_vector = _normalize_vec(
        static_vector
    )

    radial_vector = _normalize_vec(
        point.astype(np.float64)
        - nose_bridge.astype(np.float64)
    )

    if np.linalg.norm(radial_vector) < 1e-8:
        return static_vector

    # Anatomically stable blend.
    direction = (
        0.65 * static_vector
        + 0.35 * radial_vector
    )

    return _normalize_vec(direction)


def _zone_displacement(
    point: np.ndarray,
    zone_center: np.ndarray,
    volume_ml: float,
    multiplier: float,
    sigma: float,
    px_per_ml: float,
    direction: np.ndarray,
    max_displacement: float,
) -> np.ndarray:
    """
    Calculate displacement at one anatomical control point.

    Gaussian falloff means the treatment center receives maximum
    displacement while nearby points receive progressively less.
    """

    effective_volume = max(
        0.0,
        float(volume_ml) * float(multiplier),
    )

    if effective_volume <= 0.0:
        return np.zeros(2, dtype=np.float64)

    distance = float(
        np.linalg.norm(
            point - zone_center
        )
    )

    gaussian_weight = np.exp(
        -(
            distance ** 2
        )
        / (
            2.0 * sigma ** 2
        )
    )

    displacement_magnitude = (
        effective_volume
        * px_per_ml
        * gaussian_weight
    )

    displacement_magnitude = min(
        displacement_magnitude,
        max_displacement,
    )

    return (
        direction
        * displacement_magnitude
    )


def _append_zone_controls(
    src_points: list[np.ndarray],
    dst_points: list[np.ndarray],
    pts: np.ndarray,
    volume_ml: float,
    multiplier: float,
    zone: str,
    side: str,
    nose_bridge: np.ndarray,
    face_x_axis: np.ndarray,
    face_y_axis: np.ndarray,
    sigma: float,
    px_per_ml: float,
    max_displacement: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Add RBF source/target control pairs for one treatment zone.
    """

    if pts is None or len(pts) == 0:
        return (
            np.zeros(2, dtype=np.float64),
            np.zeros(2, dtype=np.float64),
        )

    pts = np.asarray(
        pts,
        dtype=np.float64,
    )

    center = np.mean(
        pts,
        axis=0,
    )

    # Add the anatomical center as the strongest treatment control.
    center_direction = _zone_direction(
        center,
        zone,
        side,
        nose_bridge,
        face_x_axis,
        face_y_axis,
    )

    center_displacement = _zone_displacement(
        point=center,
        zone_center=center,
        volume_ml=volume_ml,
        multiplier=multiplier,
        sigma=sigma,
        px_per_ml=px_per_ml,
        direction=center_direction,
        max_displacement=max_displacement,
    )

    src_points.append(center.copy())
    dst_points.append(
        center + center_displacement
    )

    # Add individual anatomical points.
    for point in pts:
        direction = _zone_direction(
            point,
            zone,
            side,
            nose_bridge,
            face_x_axis,
            face_y_axis,
        )

        displacement = _zone_displacement(
            point=point,
            zone_center=center,
            volume_ml=volume_ml,
            multiplier=multiplier,
            sigma=sigma,
            px_per_ml=px_per_ml,
            direction=direction,
            max_displacement=max_displacement,
        )

        src_points.append(point.copy())
        dst_points.append(
            point + displacement
        )

    return (
        center,
        center + center_displacement,
    )


def _constrain_map_around_protected_region(
    map_x: np.ndarray,
    map_y: np.ndarray,
    protected_mask: np.ndarray | None,
    feather_px: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Keep protected pixels identity-mapped and smoothly transition the warp
    outside the protected boundary. This prevents objects such as glasses
    from participating in the RBF deformation itself.
    """
    if protected_mask is None:
        return map_x, map_y

    if protected_mask.shape != map_x.shape:
        raise ValueError(
            "protected_mask must match the local deformation grid shape."
        )

    protected = (protected_mask > 0).astype(np.uint8)
    if not np.any(protected):
        return map_x, map_y

    feather_px = max(1, int(feather_px))

    # Safety buffer around the object.
    kernel_size = 2 * feather_px + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )
    protected = cv2.dilate(
        protected,
        kernel,
        iterations=1,
    )

    # Distance from the protected region. Inside = 0, outside increases.
    distance = cv2.distanceTransform(
        (protected == 0).astype(np.uint8),
        cv2.DIST_L2,
        3,
    )

    t = np.clip(
        distance / float(feather_px),
        0.0,
        1.0,
    )

    # Smoothstep transition: identity near object, full RBF farther away.
    t = t * t * (3.0 - 2.0 * t)

    h, w = map_x.shape
    identity_x, identity_y = np.meshgrid(
        np.arange(w, dtype=np.float32),
        np.arange(h, dtype=np.float32),
    )

    constrained_x = (
        identity_x * (1.0 - t)
        + map_x * t
    ).astype(np.float32)
    constrained_y = (
        identity_y * (1.0 - t)
        + map_y * t
    ).astype(np.float32)

    return constrained_x, constrained_y


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
) -> tuple[
    np.ndarray,
    np.ndarray,
    float,
    tuple[int, int, int, int],
]:
    """
    Perform isolated RBF deformation for one cheek.
    """

    src_points: list[np.ndarray] = []
    dst_points: list[np.ndarray] = []

    # ---------------------------------------------------------
    # 1. Treatment control points
    # ---------------------------------------------------------

    _, _ = _append_zone_controls(
        src_points,
        dst_points,
        ck1_pts,
        lateral_volume_ck1,
        multiplier,
        "ck1",
        side_key,
        nose_bridge,
        face_x_axis,
        face_y_axis,
        sigma,
        px_per_ml,
        MAX_CK1_DISPLACEMENT * face_scale,
    )

    ck2_center, ck2_displaced = _append_zone_controls(
        src_points,
        dst_points,
        ck2_pts,
        medial_volume_ck2,
        multiplier,
        "ck2",
        side_key,
        nose_bridge,
        face_x_axis,
        face_y_axis,
        sigma,
        px_per_ml,
        MAX_CK2_DISPLACEMENT * face_scale,
    )

    _, _ = _append_zone_controls(
        src_points,
        dst_points,
        ck3_pts,
        submalar_volume_ck3,
        multiplier,
        "ck3",
        side_key,
        nose_bridge,
        face_x_axis,
        face_y_axis,
        sigma,
        px_per_ml,
        MAX_CK3_DISPLACEMENT * face_scale,
    )

    # ---------------------------------------------------------
    # 2. Hard anatomical anchors
    # ---------------------------------------------------------

    if local_anchors is not None:
        for anchor in np.asarray(
            local_anchors,
            dtype=np.float64,
        ):
            src_points.append(anchor.copy())
            dst_points.append(anchor.copy())

    # ---------------------------------------------------------
    # 3. Compute local geometric ROI
    # ---------------------------------------------------------

    all_source = np.asarray(
        src_points,
        dtype=np.float64,
    )

    if len(all_source) < 4:
        return (
            image.copy(),
            ck2_center,
            0.0,
            (0, w, 0, h),
        )

    x_min = max(
        0,
        int(
            np.floor(
                np.min(all_source[:, 0])
                - ROI_PADDING_PX
            )
        ),
    )

    x_max = min(
        w,
        int(
            np.ceil(
                np.max(all_source[:, 0])
                + ROI_PADDING_PX
            )
        ),
    )

    y_min = max(
        0,
        int(
            np.floor(
                np.min(all_source[:, 1])
                - ROI_PADDING_PX
            )
        ),
    )

    y_max = min(
        h,
        int(
            np.ceil(
                np.max(all_source[:, 1])
                + ROI_PADDING_PX
            )
        ),
    )

    roi_w = x_max - x_min
    roi_h = y_max - y_min

    if roi_w < 10 or roi_h < 10:
        return (
            image[y_min:y_max, x_min:x_max].copy(),
            ck2_center,
            0.0,
            (x_min, x_max, y_min, y_max),
        )

    # ---------------------------------------------------------
    # 4. Frozen ROI perimeter
    # ---------------------------------------------------------

    perimeter = _perimeter_points(
        x_min,
        x_max - 1,
        y_min,
        y_max - 1,
        n=8,
    )

    for point in perimeter:
        src_points.append(point.copy())
        dst_points.append(point.copy())

    src = np.asarray(
        src_points,
        dtype=np.float64,
    )

    dst = np.asarray(
        dst_points,
        dtype=np.float64,
    )

    # ---------------------------------------------------------
    # 5. Remove duplicate control pairs
    # ---------------------------------------------------------

    pair_data = np.hstack(
        [src, dst]
    )

    _, unique_indices = np.unique(
        np.round(pair_data, decimals=4),
        axis=0,
        return_index=True,
    )

    unique_indices = np.sort(
        unique_indices
    )

    src = src[unique_indices]
    dst = dst[unique_indices]

    if len(src) < 4:
        return (
            image[y_min:y_max, x_min:x_max].copy(),
            ck2_center,
            0.0,
            (x_min, x_max, y_min, y_max),
        )

    # ---------------------------------------------------------
    # 6. Calculate CK2 displacement for refinement
    # ---------------------------------------------------------

    ck2_shift = float(
        np.linalg.norm(
            ck2_displaced - ck2_center
        )
    )

    # ---------------------------------------------------------
    # 7. Normalize coordinates
    # ---------------------------------------------------------

    max_dim = max(
        float(w),
        float(h),
        1.0,
    )

    src_norm = src / max_dim
    dst_norm = dst / max_dim

    # ---------------------------------------------------------
    # 8. Inverse RBF
    #
    # Forward:
    #       source → destination
    #
    # Image sampling requires:
    #       destination → source
    #
    # Therefore the RBF is fitted in the inverse direction.
    # ---------------------------------------------------------

    rbf_x = Rbf(
        dst_norm[:, 0],
        dst_norm[:, 1],
        src_norm[:, 0],
        function="multiquadric",
        smooth=RBF_SMOOTH,
    )

    rbf_y = Rbf(
        dst_norm[:, 0],
        dst_norm[:, 1],
        src_norm[:, 1],
        function="multiquadric",
        smooth=RBF_SMOOTH,
    )

    # ---------------------------------------------------------
    # 9. Generate target sampling grid
    # ---------------------------------------------------------

    grid_x, grid_y = np.meshgrid(
        np.arange(roi_w, dtype=np.float64),
        np.arange(roi_h, dtype=np.float64),
    )

    target_x_norm = (
        grid_x + x_min
    ) / max_dim

    target_y_norm = (
        grid_y + y_min
    ) / max_dim

    source_x = (
        rbf_x(
            target_x_norm,
            target_y_norm,
        )
        * max_dim
    )

    source_y = (
        rbf_y(
            target_x_norm,
            target_y_norm,
        )
        * max_dim
    )

    # Convert absolute coordinates into local ROI coordinates.
    map_x = (
        source_x - x_min
    ).astype(np.float32)

    map_y = (
        source_y - y_min
    ).astype(np.float32)

    # IMPORTANT: constrain the deformation field itself around protected
    # objects. Restoring pixels after remap is not sufficient because the
    # surrounding skin can still be stretched around the object boundary.
    local_protected = None
    if glasses_mask is not None:
        local_protected = glasses_mask[
            y_min:y_max,
            x_min:x_max,
        ]

    map_x, map_y = _constrain_map_around_protected_region(
        map_x,
        map_y,
        local_protected,
        feather_px=max(4, int(round(6 * face_scale))),
    )

    map_x = np.clip(
        map_x,
        0.0,
        float(roi_w - 1),
    )

    map_y = np.clip(
        map_y,
        0.0,
        float(roi_h - 1),
    )

    # ---------------------------------------------------------
    # 10. Warp
    # ---------------------------------------------------------

    roi = image[
        y_min:y_max,
        x_min:x_max,
    ]

    warped_roi = cv2.remap(
        roi,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    # ---------------------------------------------------------
    # 11. Hard glasses restoration
    # ---------------------------------------------------------

    if glasses_mask is not None:
        local_glasses = glasses_mask[
            y_min:y_max,
            x_min:x_max,
        ]

        warped_roi[
            local_glasses > 0
        ] = roi[
            local_glasses > 0
        ]

    return (
        warped_roi,
        ck2_displaced,
        ck2_shift,
        (
            x_min,
            x_max,
            y_min,
            y_max,
        ),
    )


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
) -> tuple[
    np.ndarray,
    tuple[np.ndarray, np.ndarray],
    tuple[float, float],
    tuple[np.ndarray, np.ndarray],
]:
    """
    Apply isolated RBF-based cheek deformation.

    Returns
    -------
    deformed_image
    apexes
        Displaced left/right CK2 apexes.
    shifts_px
        Actual left/right CK2 displacement magnitude.
    anchors
        Preserved global anchors.
    """

    if side not in {
        "left",
        "right",
        "bilateral",
    }:
        raise ValueError(
            "side must be 'left', 'right', or 'bilateral'."
        )

    h, w = image.shape[:2]

    deformed = image.copy()

    # ---------------------------------------------------------
    # Face scale
    # ---------------------------------------------------------

    eye_left = landmarks.anchors[0]
    eye_right = landmarks.anchors[2]

    face_scale = _face_scale(
        eye_left,
        eye_right,
    )

    # ---------------------------------------------------------
    # Visual deformation calibration
    # ---------------------------------------------------------

    px_per_ml = (
        PX_PER_ML_AT_REFERENCE_FACE
        * face_scale
    )

    elasticity = float(
        np.clip(
            skin_elasticity,
            0.5,
            1.5,
        )
    )

    sigma = (
        BASE_SIGMA_PX
        * face_scale
        * np.clip(
            elasticity,
            0.8,
            1.2,
        )
    )

    # ---------------------------------------------------------
    # Face coordinate system
    # ---------------------------------------------------------

    nose_bridge = (
        landmarks.nose_bridge
        .astype(np.float64)
    )

    face_x_axis = _normalize_vec(
        (
            eye_right
            - eye_left
        ).astype(np.float64)
    )

    if np.linalg.norm(face_x_axis) < 1e-8:
        face_x_axis = np.array(
            [1.0, 0.0],
            dtype=np.float64,
        )

    face_y_axis = np.array(
        [
            -face_x_axis[1],
            face_x_axis[0],
        ],
        dtype=np.float64,
    )

    # ---------------------------------------------------------
    # Asymmetry
    # ---------------------------------------------------------

    left_multiplier = (
        left_cheek_multiplier
        if asymmetry_mode
        else 1.0
    )

    right_multiplier = (
        right_cheek_multiplier
        if asymmetry_mode
        else 1.0
    )

    left_apex = (
        landmarks.left_apex.copy()
    )

    right_apex = (
        landmarks.right_apex.copy()
    )

    left_shift = 0.0
    right_shift = 0.0

    # ---------------------------------------------------------
    # Left cheek
    # ---------------------------------------------------------

    if side in {"left", "bilateral"}:

        (
            warped,
            left_apex,
            left_shift,
            bounds,
        ) = _process_side(
            image=image,
            side_key="left",
            ck1_pts=landmarks.left_ck1,
            ck2_pts=landmarks.left_ck2,
            ck3_pts=landmarks.left_ck3,
            lateral_volume_ck1=lateral_volume_ck1,
            medial_volume_ck2=medial_volume_ck2,
            submalar_volume_ck3=submalar_volume_ck3,
            multiplier=left_multiplier,
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

        x0, x1, y0, y1 = bounds

        if x1 > x0 and y1 > y0:
            deformed[
                y0:y1,
                x0:x1,
            ] = warped

    # ---------------------------------------------------------
    # Right cheek
    # ---------------------------------------------------------

    if side in {"right", "bilateral"}:

        (
            warped,
            right_apex,
            right_shift,
            bounds,
        ) = _process_side(
            image=image,
            side_key="right",
            ck1_pts=landmarks.right_ck1,
            ck2_pts=landmarks.right_ck2,
            ck3_pts=landmarks.right_ck3,
            lateral_volume_ck1=lateral_volume_ck1,
            medial_volume_ck2=medial_volume_ck2,
            submalar_volume_ck3=submalar_volume_ck3,
            multiplier=right_multiplier,
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

        x0, x1, y0, y1 = bounds

        if x1 > x0 and y1 > y0:
            deformed[
                y0:y1,
                x0:x1,
            ] = warped

    return (
        deformed,
        (
            left_apex,
            right_apex,
        ),
        (
            left_shift,
            right_shift,
        ),
        (
            landmarks.anchors,
            landmarks.anchors,
        ),
    )