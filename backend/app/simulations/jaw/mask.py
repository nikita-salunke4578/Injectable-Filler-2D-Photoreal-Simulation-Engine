"""
Jaw treatment region mask generation.

Owner: Team Member

Builds a soft-edged mask that isolates the lower-face / jawline region
for contour deformation and blending.

The jaw mask should cover the mandible contour area while avoiding
the lips and chin regions (unless specifically targeted).

Usage:
    from app.simulations.jaw.mask import build_jaw_mask
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from .landmarks import JawLandmarks

logger = logging.getLogger(__name__)


def _validate_point(point: tuple[int, int] | list[int] | np.ndarray, label: str, width: int, height: int) -> tuple[int, int]:
    if point is None:
        raise ValueError(f"Jaw mask requires a valid {label} coordinate.")

    try:
        x_value, y_value = point[0], point[1]
    except (TypeError, IndexError, ValueError) as exc:
        raise ValueError(f"Jaw mask point for {label} must contain x and y values.") from exc

    try:
        x_coord = int(round(float(x_value)))
        y_coord = int(round(float(y_value)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Jaw mask point for {label} must be numeric.") from exc

    if not np.isfinite(x_value) or not np.isfinite(y_value):
        raise ValueError(f"Jaw mask point for {label} contains a non-finite coordinate.")

    if x_coord < 0 or y_coord < 0 or x_coord >= width or y_coord >= height:
        raise ValueError(
            f"Jaw mask point for {label}={point!r} is outside the image bounds {width}x{height}."
        )

    return x_coord, y_coord


def build_jaw_mask(
    image_shape: tuple[int, int],
    landmarks: "JawLandmarks",
    *,
    feather_radius: int = 25,
) -> np.ndarray:
    """Build a feathered mask for the jaw treatment region.

    Args:
        image_shape: (height, width) of the source image.
        landmarks: Jaw-specific landmarks in pixel coordinates.
        feather_radius: Gaussian blur radius used to soften the mask edge.

    Returns:
        Float mask in [0, 1] with shape (H, W).
    """
    logger.info("build_jaw_mask called with image_shape=%s, feather_radius=%d", image_shape, feather_radius)

    if not isinstance(image_shape, tuple) or len(image_shape) != 2:
        raise ValueError("image_shape must be a (height, width) tuple.")

    height, width = image_shape
    if not isinstance(height, int) or not isinstance(width, int):
        raise ValueError("image_shape values must be ints.")
    if height <= 0 or width <= 0:
        raise ValueError(f"image_shape must be positive, got {image_shape!r}.")
    if feather_radius < 0:
        raise ValueError(f"feather_radius must be non-negative, got {feather_radius!r}.")
    if landmarks is None:
        raise ValueError("Jaw mask requires valid landmarks.")
    if not landmarks.left_contour or not landmarks.right_contour:
        raise ValueError("Jaw mask requires non-empty left and right contour landmark lists.")

    chin = _validate_point(landmarks.chin, "chin", width, height)
    jaw_angle_left = _validate_point(landmarks.jaw_angle_left, "jaw_angle_left", width, height)
    jaw_angle_right = _validate_point(landmarks.jaw_angle_right, "jaw_angle_right", width, height)

    left_contour = [_validate_point(point, "left_contour", width, height) for point in landmarks.left_contour]
    right_contour = [_validate_point(point, "right_contour", width, height) for point in landmarks.right_contour]

    polygon: list[tuple[int, int]] = []
    for point in left_contour:
        polygon.append(point)
    for point in reversed(right_contour):
        if polygon and point == polygon[-1]:
            continue
        polygon.append(point)

    if len(polygon) < 3:
        raise ValueError("Jaw mask polygon must contain at least three valid points.")

    # Ensure the polygon closes at the chin and avoids a duplicate final vertex.
    if polygon[0] == polygon[-1]:
        polygon.pop()

    if len(polygon) < 3:
        raise ValueError("Jaw mask polygon collapsed to an invalid shape.")

    # Add the explicit chin anchor only once, at the lower center of the contour.
    if polygon[-1] != chin:
        polygon.append(chin)
    elif polygon[-2] == chin:
        polygon.pop()

    polygon_array = np.array(polygon, dtype=np.int32)
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillPoly(mask, [polygon_array], 255)

    if feather_radius > 0:
        kernel_size = max(3, feather_radius * 2 + 1)
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(
            mask.astype(np.float32),
            (kernel_size, kernel_size),
            sigmaX=max(feather_radius / 3.0, 1.0),
            sigmaY=max(feather_radius / 3.0, 1.0),
        )
        mask = np.clip(blurred / 255.0, 0.0, 1.0).astype(np.float32)
    else:
        mask = np.clip(mask.astype(np.float32) / 255.0, 0.0, 1.0)

    if not np.isfinite(mask).all():
        raise ValueError("Jaw mask contains non-finite values.")

    return mask.astype(np.float32)
