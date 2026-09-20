"""
Controlled jaw contour deformation.

Owner: Team Member

Applies intensity-controlled geometric deformation to simulate jawline
definition and angle enhancement.

Unlike the lips (volumetric expansion) and cheeks (midface volume), the
jaw simulation focuses on contour sharpening.  The ``definition``
parameter controls the degree of angularity introduced along the
jawline.

Usage:
    from app.simulations.jaw.deformation import apply_jaw_deformation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from .landmarks import JawLandmarks

logger = logging.getLogger(__name__)


def _coerce_jaw_path(landmarks: "JawLandmarks") -> np.ndarray:
    """Build a consistent jaw contour path from left contour, right contour and chin."""
    left = np.asarray(landmarks.left_contour, dtype=np.float32)
    right = np.asarray(landmarks.right_contour, dtype=np.float32)
    chin = np.asarray(landmarks.chin, dtype=np.float32)

    if left.size == 0 or right.size == 0:
        raise ValueError("Jaw deformation requires both left and right contour points.")

    path = np.vstack([left[:-1], chin, right[:-1][::-1]])
    if path.shape[0] == 0:
        raise ValueError("Jaw deformation contour is empty.")

    # Remove duplicate consecutive points, especially around the chin junction.
    deduped = [path[0]]
    for point in path[1:]:
        if not np.allclose(point, deduped[-1]):
            deduped.append(point)

    ordered = np.asarray(deduped, dtype=np.float32)
    if ordered.shape[0] < 3:
        raise ValueError("Jaw deformation contour must contain at least 3 points.")

    return ordered


def _calculate_jaw_field(
    landmarks: "JawLandmarks",
    height: int,
    width: int,
    definition: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int, int, int, np.ndarray] | None:
    contour = _coerce_jaw_path(landmarks)
    if contour.shape[0] < 3:
        raise ValueError("Jaw deformation requires at least 3 contour points.")

    left_angle = np.asarray(landmarks.jaw_angle_left, dtype=np.float32)
    right_angle = np.asarray(landmarks.jaw_angle_right, dtype=np.float32)
    chin = np.asarray(landmarks.chin, dtype=np.float32)

    if left_angle.size < 2 or right_angle.size < 2 or chin.size < 2:
        raise ValueError("Jaw deformation requires jaw-angle and chin coordinates.")

    padding = 35
    x_min = max(0, int(np.floor(np.min(contour[:, 0])) - padding))
    x_max = min(width, int(np.ceil(np.max(contour[:, 0])) + padding))
    y_min = max(0, int(np.floor(np.min(contour[:, 1])) - padding))
    y_max = min(height, int(np.ceil(np.max(contour[:, 1])) + padding))

    if x_max <= x_min or y_max <= y_min:
        return None

    face_center = np.mean(np.vstack([left_angle, right_angle, chin]), axis=0).astype(np.float32)

    normals = np.zeros_like(contour, dtype=np.float32)
    for index in range(len(contour)):
        if index == 0:
            tangent = contour[1] - contour[0]
        elif index == len(contour) - 1:
            tangent = contour[-1] - contour[-2]
        else:
            tangent = contour[index + 1] - contour[index - 1]
        tangent = np.asarray(tangent, dtype=np.float32)
        current = contour[index]
        tangent_norm = np.linalg.norm(tangent)
        if tangent_norm < 1e-6:
            continue
        tangent /= tangent_norm
        normal = np.array([-tangent[1], tangent[0]], dtype=np.float32)
        if np.dot(normal, face_center - current) < 0.0:
            normal *= -1.0
        normals[index] = normal

    yy, xx = np.mgrid[y_min:y_max, x_min:x_max]
    absolute_points = np.stack([xx.astype(np.float32), yy.astype(np.float32)], axis=-1)

    segment_start = contour[:-1, None, None, :]
    segment_vector = (contour[1:] - contour[:-1])[:, None, None, :]
    segment_length_sq = np.sum(segment_vector * segment_vector, axis=-1)
    point_delta = absolute_points[None, :, :, :] - segment_start
    projection = np.sum(point_delta * segment_vector, axis=-1)
    projection = np.divide(
        projection,
        segment_length_sq,
        out=np.zeros_like(projection),
        where=segment_length_sq > 1e-12,
    )
    projection = np.clip(projection, 0.0, 1.0)

    closest_points = segment_start + projection[..., None] * segment_vector
    segment_delta = absolute_points[None, :, :, :] - closest_points
    distances_sq = np.sum(segment_delta * segment_delta, axis=-1)
    nearest_segment = np.argmin(distances_sq, axis=0)
    nearest_dist = np.sqrt(np.min(distances_sq, axis=0))

    segment_projection = np.take_along_axis(
        projection,
        nearest_segment[None, :, :],
        axis=0,
    )[0]
    nearest_point = np.take_along_axis(
        closest_points,
        nearest_segment[None, :, :, None],
        axis=0,
    )[0]
    start_normals = normals[:-1][nearest_segment]
    end_normals = normals[1:][nearest_segment]
    nearest_normal = (
        start_normals * (1.0 - segment_projection[..., None])
        + end_normals * segment_projection[..., None]
    )
    nearest_normal_norm = np.linalg.norm(nearest_normal, axis=-1, keepdims=True)
    nearest_normal = np.divide(
        nearest_normal,
        nearest_normal_norm,
        out=np.zeros_like(nearest_normal),
        where=nearest_normal_norm > 1e-6,
    )

    definition_factor = float(definition) / 100.0
    sigma = 18.0 + 32.0 * definition_factor
    falloff = np.exp(-(nearest_dist ** 2) / (2.0 * sigma ** 2))
    influence = np.clip(falloff, 0.0, 1.0)

    edge_distance = np.minimum.reduce(
        (
            xx - x_min,
            (x_max - 1) - xx,
            yy - y_min,
            (y_max - 1) - yy,
        )
    )
    edge_fade = np.clip(edge_distance / float(padding), 0.0, 1.0)
    edge_fade = edge_fade * edge_fade * (3.0 - 2.0 * edge_fade)
    influence *= edge_fade

    signed_side = np.sum(
        (absolute_points - nearest_point) * nearest_normal,
        axis=-1,
    )
    side_fade = 0.5 * (1.0 + np.tanh(signed_side / max(sigma, 1.0)))
    influence *= side_fade
    face_depth = np.maximum(signed_side, 0.0)
    face_side_taper = np.exp(
        -(face_depth ** 2) / (2.0 * (padding * 0.5) ** 2)
    )
    influence *= face_side_taper

    return contour, nearest_normal, xx, yy, x_min, x_max, y_min, y_max, influence


def build_jaw_deformation_influence(
    image_shape: tuple[int, int],
    landmarks: "JawLandmarks",
    *,
    definition: int = 50,
) -> np.ndarray:
    """Return the full-frame influence used by jaw deformation and blending."""
    if not isinstance(image_shape, tuple) or len(image_shape) != 2:
        raise ValueError("image_shape must be a (height, width) tuple.")
    height, width = image_shape
    if not isinstance(height, int) or not isinstance(width, int):
        raise ValueError("image_shape values must be ints.")
    if height <= 0 or width <= 0:
        raise ValueError(f"image_shape must be positive, got {image_shape!r}.")
    if not 0 <= int(definition) <= 100:
        raise ValueError(f"definition must be in [0, 100], got {definition!r}.")
    if landmarks is None:
        raise ValueError("Jaw deformation requires valid JawLandmarks.")

    field = _calculate_jaw_field(landmarks, height, width, int(definition))
    full_frame_influence = np.zeros((height, width), dtype=np.float32)
    if field is not None:
        _, _, xx, yy, x_min, x_max, y_min, y_max, influence = field
        full_frame_influence[y_min:y_max, x_min:x_max] = influence
    return full_frame_influence


def apply_jaw_deformation(
    image: "np.ndarray",
    landmarks: "JawLandmarks",
    *,
    intensity: float = 0.5,
    definition: int = 50,
) -> "np.ndarray":
    """Apply a localized jawline deformation that sharpens the mandibular contour.

    A deterministic displacement field is generated around the lower jaw contour,
    then applied with a local remap. The transformation is intentionally limited to
    the jaw region so the rest of the face remains visually stable.
    """
    logger.info(
        "apply_jaw_deformation called with intensity=%.3f, definition=%d",
        float(intensity),
        int(definition),
    )

    if image is None:
        raise ValueError("Jaw deformation requires a valid image array.")

    image_array = np.asarray(image)
    if image_array.ndim != 3 or image_array.shape[2] != 3:
        raise ValueError("Jaw deformation requires an HxWx3 image array.")
    if image_array.dtype != np.uint8:
        raise ValueError("Jaw deformation requires uint8 image data.")

    if not 0.0 <= float(intensity) <= 1.0:
        raise ValueError(f"intensity must be in [0, 1], got {intensity!r}.")
    if not 0 <= int(definition) <= 100:
        raise ValueError(f"definition must be in [0, 100], got {definition!r}.")

    if intensity == 0.0 or definition == 0:
        logger.info("Jaw deformation skipped because intensity or definition is zero.")
        return image_array.copy()

    if landmarks is None:
        raise ValueError("Jaw deformation requires valid JawLandmarks.")

    height, width = image_array.shape[:2]
    field = _calculate_jaw_field(landmarks, height, width, int(definition))
    if field is None:
        logger.warning("Jaw deformation ROI collapsed; returning original image.")
        return image_array.copy()

    contour, nearest_normal, xx, yy, x_min, x_max, y_min, y_max, influence = field
    definition_factor = float(definition) / 100.0
    strength = (3.0 + 22.0 * definition_factor) * float(intensity)
    displacement = nearest_normal * strength * influence[..., None]

    # Full-frame maps keep the image size unchanged while limiting deformation to
    # the jaw area. In OpenCV remap, output(x, y) samples input(map_x, map_y), so
    # the displacement must be applied in the inverse direction to push the jaw
    # contour outward in the visible output.
    map_x = np.tile(np.arange(width, dtype=np.float32)[None, :], (height, 1))
    map_y = np.tile(np.arange(height, dtype=np.float32)[:, None], (1, width))

    x_local = xx.astype(np.float32) - displacement[:, :, 0]
    y_local = yy.astype(np.float32) - displacement[:, :, 1]

    map_x[y_min:y_max, x_min:x_max] = x_local
    map_y[y_min:y_max, x_min:x_max] = y_local

    warped = cv2.remap(
        image_array,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    logger.info(
        "Jaw deformation applied to ROI [%d:%d, %d:%d] with strength %.3f.",
        y_min,
        y_max,
        x_min,
        x_max,
        float(strength),
    )
    return warped.astype(np.uint8, copy=False)
