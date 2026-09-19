"""
Eyeglasses detection and hard protection mask generation for midface simulations.

Performs single-pass edge density and contrast structural checks in the orbital margin
zone to detect frame presence and extract a binary protection mask.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.simulations.cheeks.landmarks import CheekLandmarks

# Lower orbital / eye frame indices from MediaPipe mesh
INFRAORBITAL_INDICES = {
    "left": [33, 7, 163, 144, 145, 153, 154, 155, 133, 243, 190, 56, 28],
    "right": [362, 382, 381, 380, 374, 373, 390, 249, 263, 463, 414, 286],
}


def detect_glasses(
    image: np.ndarray,
    landmarks: CheekLandmarks,
    edge_threshold: float = 12.0,
) -> tuple[bool, np.ndarray | None]:
    """
    Detects if the user is wearing eyeglasses and generates a hard binary protection mask.

    Args:
        image: Original BGR input image (H, W, 3).
        landmarks: CheekLandmarks dataclass instance.
        edge_threshold: Canny structural edge density threshold inside the orbital zone.

    Returns:
        tuple (glasses_detected, glasses_mask)
        - glasses_detected: bool
        - glasses_mask: np.ndarray of shape (H, W), dtype uint8 (255 where glasses exist, 0 elsewhere),
          or None if no glasses are detected.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Define orbital protection region using eye anchors and local exclusions
    orbital_zone_mask = np.zeros((h, w), dtype=np.uint8)

    eye_l = landmarks.anchors[0]
    eye_r = landmarks.anchors[2]
    inter_ocular_dist = max(float(np.linalg.norm(eye_r - eye_l)), 30.0)
    face_scale = inter_ocular_dist / 140.0

    # Build convex hull over eye landmarks and expand downward over potential frames
    for side_key in ("left", "right"):
        excl_pts = (
            landmarks.left_eye_exclusion
            if side_key == "left"
            else landmarks.right_eye_exclusion
        )
        if len(excl_pts) >= 3:
            hull = cv2.convexHull(excl_pts.astype(np.int32))
            cv2.fillConvexPoly(orbital_zone_mask, hull, 255)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (int(21 * face_scale) | 1, int(31 * face_scale) | 1),
    )
    dilated_orbital_zone = cv2.dilate(orbital_zone_mask, kernel, iterations=1)

    # 2. Compute Canny edge density strictly inside orbital region
    edges = cv2.Canny(gray, 50, 150)
    zone_pixel_count = np.sum(dilated_orbital_zone > 0)
    if zone_pixel_count == 0:
        return False, None

    edge_pixels_in_zone = np.sum(edges[dilated_orbital_zone > 0] > 0)
    edge_density = (edge_pixels_in_zone / float(zone_pixel_count)) * 100.0

    # 3. If edge density is below threshold, no glasses are present
    if edge_density < edge_threshold:
        return False, None

    # 4. Create Hard Binary Glasses Mask
    # Threshold dark/structured frame elements within orbital region
    _, dark_pixels = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)

    # Adaptive threshold to capture tortoiseshell, wire, or non-black frames
    adaptive_thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        4,
    )

    combined_frame_structure = cv2.bitwise_or(dark_pixels, adaptive_thresh)
    combined_frame_structure = cv2.bitwise_and(
        combined_frame_structure, dilated_orbital_zone
    )

    # Dilate slightly to catch anti-aliased frame edges
    frame_dilation_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (5, 5)
    )
    glasses_mask = cv2.dilate(
        combined_frame_structure, frame_dilation_kernel, iterations=1
    )

    return True, glasses_mask