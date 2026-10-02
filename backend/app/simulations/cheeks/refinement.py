"""
Cheek photometric refinement.

Converts the geometric deformation into a subtle 2D shading cue
and restores high-frequency skin texture from the original image.

This is a classical image-processing refinement stage.
It is not a physical 3D tissue renderer.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks


def _gaussian_map(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    center: np.ndarray,
    sigma: float,
) -> np.ndarray:
    """Generate normalized Gaussian influence around a cheek apex."""

    sigma = max(
        float(sigma),
        1.0,
    )

    dx = grid_x - float(center[0])
    dy = grid_y - float(center[1])

    distance_sq = (
        dx * dx
        + dy * dy
    )

    return np.exp(
        -distance_sq
        / (2.0 * sigma * sigma)
    )


def _displacement_shading(
    shape: tuple[int, int],
    apex: np.ndarray,
    displacement_px: float,
    face_scale: float,
) -> np.ndarray:
    """
    Create a smooth local shading field from actual displacement.

    The field is intentionally subtle. It is used as a visual cue,
    not as a physical lighting simulation.
    """

    h, w = shape

    y, x = np.indices(
        (h, w),
        dtype=np.float32,
    )

    sigma = max(
        28.0 * face_scale,
        8.0,
    )

    gaussian = _gaussian_map(
        x,
        y,
        apex,
        sigma,
    )

    # Normalize displacement into a conservative shading coefficient.
    displacement_factor = np.clip(
        displacement_px / max(
            14.0 * face_scale,
            1.0,
        ),
        0.0,
        1.0,
    )

    # Very subtle central lift.
    return (
        gaussian
        * displacement_factor
    )


def _texture_high_pass(
    image: np.ndarray,
) -> np.ndarray:
    """Extract high-frequency skin texture."""

    blurred = cv2.GaussianBlur(
        image,
        (5, 5),
        1.2,
    )

    return (
        image.astype(np.float32)
        - blurred.astype(np.float32)
    )


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
    Apply subtle displacement-driven photometric refinement.

    Parameters
    ----------
    deformed_image:
        Output of the RBF geometric deformation.

    mask:
        Final anatomical cheek blending mask.

    landmarks:
        Cheek landmark structure.

    apexes:
        Displaced left/right CK2 apexes.

    original_image:
        Original input image.

    shifts_px:
        Actual geometric displacement magnitude for left/right cheek.

    Returns
    -------
    np.ndarray
        Refined BGR image.
    """

    if deformed_image.shape != original_image.shape:
        raise ValueError(
            "deformed_image and original_image must have identical shapes."
        )

    if mask.shape[:2] != deformed_image.shape[:2]:
        raise ValueError(
            "mask must match image height and width."
        )

    h, w = deformed_image.shape[:2]

    include_left = side in {
        "left",
        "bilateral",
    }

    include_right = side in {
        "right",
        "bilateral",
    }

    left_apex, right_apex = apexes

    left_shift, right_shift = shifts_px

    # ---------------------------------------------------------
    # Face scale
    # ---------------------------------------------------------

    eye_distance = max(
        float(
            np.linalg.norm(
                landmarks.anchors[2]
                - landmarks.anchors[0]
            )
        ),
        30.0,
    )

    face_scale = eye_distance / 140.0

    # ---------------------------------------------------------
    # Mask
    # ---------------------------------------------------------

    mask_norm = (
        mask.astype(np.float32)
        / 255.0
    )

    mask_3 = mask_norm[:, :, None]

    # ---------------------------------------------------------
    # Build displacement-driven shading
    # ---------------------------------------------------------

    shading = np.zeros(
        (h, w),
        dtype=np.float32,
    )

    if include_left and left_shift > 0.01:
        shading += _displacement_shading(
            (h, w),
            left_apex,
            left_shift,
            face_scale,
        )

    if include_right and right_shift > 0.01:
        shading += _displacement_shading(
            (h, w),
            right_apex,
            right_shift,
            face_scale,
        )

    shading = np.clip(
        shading,
        0.0,
        1.0,
    )

    # ---------------------------------------------------------
    # LAB lightness refinement
    # ---------------------------------------------------------

    lab = cv2.cvtColor(
        deformed_image,
        cv2.COLOR_BGR2LAB,
    ).astype(np.float32)

    l_channel = lab[:, :, 0]

    # Deliberately conservative.
    # This is a visual refinement, not physical illumination.
    LIGHTNESS_GAIN = 0.035

    l_delta = (
        l_channel
        * LIGHTNESS_GAIN
        * shading
        * mask_norm
    )

    lab[:, :, 0] = np.clip(
        l_channel + l_delta,
        0.0,
        255.0,
    )

    relit = cv2.cvtColor(
        lab.astype(np.uint8),
        cv2.COLOR_LAB2BGR,
    )

    # ---------------------------------------------------------
    # Skin texture restoration
    # ---------------------------------------------------------

    high_pass = _texture_high_pass(
        original_image
    )

    # Avoid aggressive texture amplification.
    TEXTURE_WEIGHT = 0.30

    textured = (
        relit.astype(np.float32)
        + TEXTURE_WEIGHT
        * high_pass
        * mask_3
    )

    textured = np.clip(
        textured,
        0.0,
        255.0,
    )

    # ---------------------------------------------------------
    # Final refinement constrained by mask
    # ---------------------------------------------------------

    refined = (
        textured * mask_3
        + deformed_image.astype(
            np.float32
        ) * (1.0 - mask_3)
    )

    return np.clip(
        refined,
        0.0,
        255.0,
    ).astype(np.uint8)