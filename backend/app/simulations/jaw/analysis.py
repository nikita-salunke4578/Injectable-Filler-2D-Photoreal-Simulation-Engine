"""
Jawline facial proportion analysis.

Uses the existing Jaw landmark extractor to calculate basic geometric
jawline metrics and generate simulation parameters.
"""

from __future__ import annotations

import numpy as np

from app.common.face_detection import FaceDetector
from app.simulations.jaw.landmarks import extract_jaw_landmarks


def _distance(p1, p2) -> float:
    return float(np.linalg.norm(np.asarray(p1) - np.asarray(p2)))


def _angle(p1, vertex, p2) -> float:
    a = np.asarray(p1, dtype=float) - np.asarray(vertex, dtype=float)
    b = np.asarray(p2, dtype=float) - np.asarray(vertex, dtype=float)

    denom = np.linalg.norm(a) * np.linalg.norm(b)

    if denom == 0:
        return 0.0

    cosine = np.clip(np.dot(a, b) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def analyze_jaw_proportions(
    image: np.ndarray,
    face_detector: FaceDetector | None = None,
) -> dict:
    """
    Analyze jawline geometry and return simulation-ready parameters.
    """

    if face_detector is None:
        face_detector = FaceDetector()

    try:
        face_pts = face_detector.get_landmarks(image)
    except ValueError:
        return {"error": "No face detected in the image."}

    jaw = extract_jaw_landmarks(face_pts)

    if jaw is None:
        return {"error": "Jaw landmarks could not be extracted."}

    # ---------------------------------------------------------
    # 1. Jaw width
    # ---------------------------------------------------------
    jaw_width = _distance(
        jaw.jaw_angle_left,
        jaw.jaw_angle_right,
    )

    # ---------------------------------------------------------
    # 2. Chin position / lower-face height
    # ---------------------------------------------------------
    chin_to_left_angle = _distance(
        jaw.chin,
        jaw.jaw_angle_left,
    )

    chin_to_right_angle = _distance(
        jaw.chin,
        jaw.jaw_angle_right,
    )

    average_lower_face_length = (
        chin_to_left_angle + chin_to_right_angle
    ) / 2.0

    # ---------------------------------------------------------
    # 3. Jaw symmetry
    # ---------------------------------------------------------
    left_length = sum(
        _distance(a, b)
        for a, b in zip(
            jaw.left_contour[:-1],
            jaw.left_contour[1:],
        )
    )

    right_length = sum(
        _distance(a, b)
        for a, b in zip(
            jaw.right_contour[:-1],
            jaw.right_contour[1:],
        )
    )

    max_side = max(left_length, right_length, 1.0)

    symmetry_score = (
        100.0
        * (1.0 - abs(left_length - right_length) / max_side)
    )

    symmetry_score = float(
        np.clip(symmetry_score, 0.0, 100.0)
    )

    # ---------------------------------------------------------
    # 4. Left/right jaw angles
    # ---------------------------------------------------------
    left_angle = _angle(
        jaw.left_contour[0],
        jaw.jaw_angle_left,
        jaw.chin,
    )

    right_angle = _angle(
        jaw.right_contour[0],
        jaw.jaw_angle_right,
        jaw.chin,
    )

    average_jaw_angle = (left_angle + right_angle) / 2.0

    # ---------------------------------------------------------
    # 5. Derive simulation parameters
    # ---------------------------------------------------------
    #
    # These are simulation defaults rather than clinical
    # treatment recommendations.
    #

    definition = 50

    if average_jaw_angle < 125:
        definition = 65
    elif average_jaw_angle > 145:
        definition = 40

    if symmetry_score < 90:
        definition = min(definition, 55)

    volume_ml = 1.0

    # Keep within the JawSimulationConfig limits.
    volume_ml = float(np.clip(volume_ml, 0.0, 3.0))

    if symmetry_score < 85:
        primary_concern = "jaw-asymmetry"
    elif average_jaw_angle < 125:
        primary_concern = "jaw-definition"
    else:
        primary_concern = "jaw-contour"

    return {
        "zone": "jaw",
        "metrics": {
            "jaw_width_px": float(round(jaw_width, 1)),
            "lower_face_length_px": float(
                round(average_lower_face_length, 1)
            ),
            "left_jaw_angle": float(round(left_angle, 1)),
            "right_jaw_angle": float(round(right_angle, 1)),
            "average_jaw_angle": float(
                round(average_jaw_angle, 1)
            ),
            "jaw_symmetry_score": float(
                round(symmetry_score, 1)
            ),
        },
        "recommendation": {
            "text": (
                f"Jaw contour analysis completed. "
                f"Detected jaw symmetry score of "
                f"{symmetry_score:.0f}% and an average jaw angle "
                f"of {average_jaw_angle:.1f} degrees."
            ),
            "suggested_volume_ml": volume_ml,
        },
        "suggested_parameters": {
            "volumeMl": volume_ml,
            "definition": definition,
        },
        "suggested_answers": {
            "gender": "female",
            "ageRange": "30-45",
            "primaryConcern": primary_concern,
            "experience": "first-time",
            "desiredOutcome": "natural",
            "symmetryConcern": (
                "significant"
                if symmetry_score < 80
                else "mild"
                if symmetry_score < 90
                else "none"
            ),
        },
    }