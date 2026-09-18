"""
Cheek-specific landmark extraction and anatomical mapping.

Defines MediaPipe indices for midface sub-zones (CK1, CK2, CK3),
rigid anchor points, and tear trough / lower orbital exclusion cages.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

CHEEK_LANDMARKS = {
    "left": {
        "lateral_ck1": [234, 127, 162],
        "malar_ck2": [116,  123, 187],
        "submalar_ck3": [205, 203, 206, 207],
    },
    "right": {
        "lateral_ck1": [454, 356, 389],
        "malar_ck2": [345,  352, 411],
        "submalar_ck3": [425, 423, 426, 427],
    },
    "anchors": [
        33,   # Left Eye Outer
        133,  # Left Eye Inner
        263,  # Right Eye Outer
        362,  # Right Eye Inner
        6,    # Nose Bridge
        0,    # Upper Lip Center
        152,  # Chin / Jaw Bottom
    ],
}

# Eyelid & Tear Trough Safety Cage indices (to prevent tear trough smudging)
EYE_EXCLUSION_LANDMARKS = {
    "left": [111, 117, 118, 119, 120, 121],
    "right": [340, 346, 347, 348, 349, 350],
}

# Extra perimeter anchors to prevent displacement bleeding outside midface
ADDITIONAL_ANCHORS = [
    10,   # Forehead top center
    67,   # Left eyebrow outer
    297,  # Right eyebrow outer
    2,    # Nose columella base
    61,   # Mouth left corner
    291,  # Mouth right corner
    148,  # Left mandibular body
    377,  # Right mandibular body
    172,  # Left jaw angle
    397,  # Right jaw angle
]


@dataclass
class CheekLandmarks:
    """Processed cheek-specific landmarks in pixel coordinates."""

    left_ck1: np.ndarray
    left_ck2: np.ndarray
    left_ck3: np.ndarray
    right_ck1: np.ndarray
    right_ck2: np.ndarray
    right_ck3: np.ndarray
    anchors: np.ndarray
    nose_bridge: np.ndarray
    left_eye_exclusion: np.ndarray
    right_eye_exclusion: np.ndarray
    left_all: np.ndarray
    right_all: np.ndarray
    left_apex: np.ndarray
    right_apex: np.ndarray


def extract_cheek_landmarks(face_landmarks: np.ndarray) -> CheekLandmarks:
    """
    Extracts cheek-specific anatomical sub-zones, anchors, and exclusion points.

    Args:
        face_landmarks: (N, 2) numpy array of face landmarks in pixel coordinates (e.g. 468 or 478 points).

    Returns:
        CheekLandmarks dataclass instance containing all designated sub-zone arrays.
    """
    if len(face_landmarks) < 468:
        raise ValueError(f"Insufficient face landmarks: expected at least 468, got {len(face_landmarks)}")

    left_ck1 = face_landmarks[CHEEK_LANDMARKS["left"]["lateral_ck1"]]
    left_ck2 = face_landmarks[CHEEK_LANDMARKS["left"]["malar_ck2"]]
    left_ck3 = face_landmarks[CHEEK_LANDMARKS["left"]["submalar_ck3"]]

    right_ck1 = face_landmarks[CHEEK_LANDMARKS["right"]["lateral_ck1"]]
    right_ck2 = face_landmarks[CHEEK_LANDMARKS["right"]["malar_ck2"]]
    right_ck3 = face_landmarks[CHEEK_LANDMARKS["right"]["submalar_ck3"]]

    all_anchor_indices = CHEEK_LANDMARKS["anchors"] + ADDITIONAL_ANCHORS
    anchors = face_landmarks[all_anchor_indices]

    nose_bridge = face_landmarks[6]

    left_eye_excl = face_landmarks[EYE_EXCLUSION_LANDMARKS["left"]]
    right_eye_excl = face_landmarks[EYE_EXCLUSION_LANDMARKS["right"]]

    left_all = np.vstack([left_ck1, left_ck2, left_ck3])
    right_all = np.vstack([right_ck1, right_ck2, right_ck3])

    left_apex = np.mean(left_ck2, axis=0)
    right_apex = np.mean(right_ck2, axis=0)

    return CheekLandmarks(
        left_ck1=left_ck1,
        left_ck2=left_ck2,
        left_ck3=left_ck3,
        right_ck1=right_ck1,
        right_ck2=right_ck2,
        right_ck3=right_ck3,
        anchors=anchors,
        nose_bridge=nose_bridge,
        left_eye_exclusion=left_eye_excl,
        right_eye_exclusion=right_eye_excl,
        left_all=left_all,
        right_all=right_all,
        left_apex=left_apex,
        right_apex=right_apex,
    )
