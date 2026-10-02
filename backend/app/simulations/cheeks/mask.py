"""
Cheek treatment-region mask generation.

Responsibilities
----------------
1. Build anatomical CK1 / CK2 / CK3 treatment masks.
2. Keep the orbital / tear-trough region protected.
3. Subtract detected glasses.
4. Apply soft anatomical boundary feathering.
5. Keep unilateral treatment isolated from the opposite cheek.

The mask is used for FINAL COMPOSITING and refinement.
The RBF deformation itself operates on a separate local geometric ROI.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks


def _odd_kernel(size: int) -> int:
    """Return a valid positive odd OpenCV kernel size."""
    size = max(1, int(size))
    return size if size % 2 == 1 else size + 1


def _zone_mask(
    pts: np.ndarray,
    h: int,
    w: int,
    kernel: np.ndarray,
) -> np.ndarray:
    """
    Build a binary mask around an anatomical landmark group.

    A convex hull is used only to establish the local treatment support.
    The subsequent Gaussian feathering converts this binary support into
    a soft compositing mask.
    """
    mask = np.zeros((h, w), dtype=np.uint8)

    if pts is None or len(pts) < 3:
        return mask

    pts_i = np.round(pts).astype(np.int32)

    hull = cv2.convexHull(pts_i)
    cv2.fillConvexPoly(mask, hull, 255)

    if kernel.size > 1:
        mask = cv2.dilate(mask, kernel, iterations=1)

    return mask


def _build_side_zone_mask(
    landmarks: CheekLandmarks,
    side: str,
    h: int,
    w: int,
    kernel: np.ndarray,
    zone_active: dict[str, bool],
) -> np.ndarray:
    """Construct CK1/CK2/CK3 mask for one facial side."""

    mask = np.zeros((h, w), dtype=np.uint8)

    if side == "left":
        zones = {
            "left_ck1": landmarks.left_ck1,
            "left_ck2": landmarks.left_ck2,
            "left_ck3": landmarks.left_ck3,
        }
    else:
        zones = {
            "right_ck1": landmarks.right_ck1,
            "right_ck2": landmarks.right_ck2,
            "right_ck3": landmarks.right_ck3,
        }

    for key, pts in zones.items():
        if zone_active.get(key, True):
            mask = cv2.bitwise_or(
                mask,
                _zone_mask(pts, h, w, kernel),
            )

    return mask


def _subtract_eye_exclusion(
    mask: np.ndarray,
    exclusion_pts: np.ndarray,
) -> np.ndarray:
    """Remove the lower orbital / tear-trough safety region."""

    if exclusion_pts is None or len(exclusion_pts) < 3:
        return mask

    h, w = mask.shape

    exclusion = np.zeros((h, w), dtype=np.uint8)

    hull = cv2.convexHull(
        np.round(exclusion_pts).astype(np.int32)
    )

    cv2.fillConvexPoly(exclusion, hull, 255)

    # Small safety expansion around the orbital cage.
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (9, 9),
    )

    exclusion = cv2.dilate(
        exclusion,
        kernel,
        iterations=1,
    )

    return cv2.bitwise_and(
        mask,
        cv2.bitwise_not(exclusion),
    )


def _subtract_glasses(
    mask: np.ndarray,
    glasses_mask: np.ndarray | None,
) -> np.ndarray:
    """Hard-remove pixels belonging to detected glasses."""

    if glasses_mask is None:
        return mask

    if glasses_mask.shape != mask.shape:
        raise ValueError(
            "glasses_mask must have the same HxW shape as the treatment mask."
        )

    return cv2.bitwise_and(
        mask,
        cv2.bitwise_not(glasses_mask),
    )


def _apply_lateral_fade(
    mask: np.ndarray,
    landmarks: CheekLandmarks,
) -> np.ndarray:
    """
    Apply a smooth falloff toward the lateral face boundary.

    This prevents the treatment mask from terminating abruptly near the
    edge of the facial landmark support.
    """

    h, w = mask.shape

    all_face_points = np.vstack(
        [
            landmarks.anchors,
            landmarks.left_all,
            landmarks.right_all,
        ]
    ).astype(np.float32)

    min_x = max(
        0,
        int(np.floor(np.min(all_face_points[:, 0]))) - 20,
    )

    max_x = min(
        w - 1,
        int(np.ceil(np.max(all_face_points[:, 0]))) + 20,
    )

    if max_x <= min_x:
        return mask

    face_width = max_x - min_x

    fade_px = max(
        12,
        int(face_width * 0.10),
    )

    x = np.arange(w, dtype=np.float32)

    left_t = np.clip(
        (x - min_x) / float(fade_px),
        0.0,
        1.0,
    )

    right_t = np.clip(
        (max_x - x) / float(fade_px),
        0.0,
        1.0,
    )

    # Smoothstep / cosine transition.
    left_weight = (
        1.0 - np.cos(left_t * np.pi)
    ) * 0.5

    right_weight = (
        1.0 - np.cos(right_t * np.pi)
    ) * 0.5

    lateral_weight = np.minimum(
        left_weight,
        right_weight,
    )

    lateral_weight = np.tile(
        lateral_weight[np.newaxis, :],
        (h, 1),
    )

    return (
        mask.astype(np.float32)
        * lateral_weight
    ).astype(np.uint8)


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
    Build the final soft anatomical cheek-treatment mask.

    Parameters
    ----------
    image_shape:
        Image shape: (H, W) or (H, W, C).

    landmarks:
        CheekLandmarks in pixel coordinates.

    glasses_mask:
        Binary mask, 255 where glasses pixels must remain untouched.

    side:
        "left", "right", or "bilateral".

    zone_active:
        CK1/CK2/CK3 activation map.

    feather_radius:
        Main anatomical feather radius.

    dilate_px:
        Local expansion around anatomical zone landmarks.

    Returns
    -------
    np.ndarray
        uint8 mask in [0, 255].
    """

    if side not in {"left", "right", "bilateral"}:
        raise ValueError(
            "side must be 'left', 'right', or 'bilateral'."
        )

    h, w = image_shape[:2]

    zone_active = zone_active or {}

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            2 * max(0, int(dilate_px)) + 1,
            2 * max(0, int(dilate_px)) + 1,
        ),
    )

    mask = np.zeros(
        (h, w),
        dtype=np.uint8,
    )

    # ---------------------------------------------------------
    # 1. Anatomical treatment zones
    # ---------------------------------------------------------

    if side in {"left", "bilateral"}:
        left_mask = _build_side_zone_mask(
            landmarks,
            "left",
            h,
            w,
            kernel,
            zone_active,
        )

        left_mask = _subtract_eye_exclusion(
            left_mask,
            landmarks.left_eye_exclusion,
        )

        mask = cv2.bitwise_or(
            mask,
            left_mask,
        )

    if side in {"right", "bilateral"}:
        right_mask = _build_side_zone_mask(
            landmarks,
            "right",
            h,
            w,
            kernel,
            zone_active,
        )

        right_mask = _subtract_eye_exclusion(
            right_mask,
            landmarks.right_eye_exclusion,
        )

        mask = cv2.bitwise_or(
            mask,
            right_mask,
        )

    # ---------------------------------------------------------
    # 2. Glasses hard protection
    # ---------------------------------------------------------

    mask = _subtract_glasses(
        mask,
        glasses_mask,
    )

    # ---------------------------------------------------------
    # 3. Anatomical lateral boundary fade
    # ---------------------------------------------------------

    mask = _apply_lateral_fade(
        mask,
        landmarks,
    )

    # ---------------------------------------------------------
    # 4. Main feather
    # ---------------------------------------------------------

    if feather_radius > 0:
        ksize = _odd_kernel(feather_radius)

        mask_f = (
            mask.astype(np.float32) / 255.0
        )

        mask_f = cv2.GaussianBlur(
            mask_f,
            (ksize, ksize),
            0,
        )
    else:
        mask_f = (
            mask.astype(np.float32) / 255.0
        )

    # ---------------------------------------------------------
    # 5. Final very-soft transition
    # ---------------------------------------------------------

    if feather_radius > 0:
        soft_size = _odd_kernel(
            max(45, feather_radius * 2 + 1)
        )

        mask_f = cv2.GaussianBlur(
            mask_f,
            (soft_size, soft_size),
            0,
        )

    return (
        np.clip(mask_f, 0.0, 1.0) * 255.0
    ).astype(np.uint8)