"""
Cheek and midface facial proportion analysis.

Extracts anatomical midface metrics (bizygomatic width, malar projection,
submalar gauntness, and midface symmetry) from MediaPipe landmarks
to generate personalized clinical filler recommendations and auto-fill slider values.
"""

from __future__ import annotations

import numpy as np

from app.common.face_detection import FaceDetector
from app.simulations.cheeks.landmarks import extract_cheek_landmarks


def _euclidean(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))


def analyze_cheek_proportions(image: np.ndarray, face_detector: FaceDetector | None = None) -> dict:
    """
    Scans the face and computes mathematical midface and cheekbone proportions.
    Returns rich metrics, clinical analysis text, and auto-suggested cheek parameters.
    """
    if face_detector is None:
        face_detector = FaceDetector()

    try:
        face_pts = face_detector.get_landmarks(image)
    except ValueError:
        return {"error": "No face detected in the image."}

    landmarks = extract_cheek_landmarks(face_pts)

    # 1. Bizygomatic Width (outermost zygomatic landmarks 234 and 454)
    left_zygoma = face_pts[234]
    right_zygoma = face_pts[454]
    bizygomatic_width = _euclidean(left_zygoma, right_zygoma)

    # 2. Bigonial (Jaw) Width (landmarks 172 and 397)
    left_jaw = face_pts[172]
    right_jaw = face_pts[397]
    bigonial_width = _euclidean(left_jaw, right_jaw)
    zygoma_to_jaw_ratio = bizygomatic_width / max(bigonial_width, 1.0)

    # 3. Malar Apex Projection & Position
    left_apex = landmarks.left_apex
    right_apex = landmarks.right_apex
    nose_bridge = landmarks.nose_bridge

    # Midface centerline x
    center_x = float(nose_bridge[0])

    # Left and right lateral arch distances
    left_lateral_dist = abs(left_zygoma[0] - center_x)
    right_lateral_dist = abs(right_zygoma[0] - center_x)

    # 4. Midface Symmetry Score (compare left vs right cheek projection and lateral width)
    max_lat = max(left_lateral_dist, right_lateral_dist, 1.0)
    lat_diff = abs(left_lateral_dist - right_lateral_dist) / max_lat

    left_apex_dist = abs(left_apex[0] - center_x)
    right_apex_dist = abs(right_apex[0] - center_x)
    max_apex = max(left_apex_dist, right_apex_dist, 1.0)
    apex_diff = abs(left_apex_dist - right_apex_dist) / max_apex

    symmetry_score = max(0.0, min(100.0, 100.0 * (1.0 - 0.5 * (lat_diff + apex_diff))))

    # 5. Submalar Concavity / Gauntness Score
    # Distance from malar apex down to submalar hollow
    left_submalar = np.mean(landmarks.left_ck3, axis=0)
    right_submalar = np.mean(landmarks.right_ck3, axis=0)

    # Concavity: how far inward submalar is relative to zygomatic arch
    left_inward = abs(left_zygoma[0] - left_submalar[0])
    right_inward = abs(right_zygoma[0] - right_submalar[0])
    avg_inward = (left_inward + right_inward) / 2.0
    concavity_ratio = avg_inward / max(bizygomatic_width, 1.0)

    # 6. Malar Projection Ratio (Apex height relative to midface vertical height)
    eye_line_y = (face_pts[33][1] + face_pts[263][1]) / 2.0
    nose_base_y = float(face_pts[2][1])
    midface_height = max(abs(nose_base_y - eye_line_y), 1.0)

    avg_apex_y = (left_apex[1] + right_apex[1]) / 2.0
    malar_projection_ratio = (nose_base_y - avg_apex_y) / midface_height

    # 7. Apex Elevation Angle (angle of line from mouth corner to cheek apex)
    mouth_left = face_pts[61]
    mouth_right = face_pts[291]
    dx_l = abs(left_apex[0] - mouth_left[0])
    dy_l = mouth_left[1] - left_apex[1]  # positive when apex is higher than mouth
    angle_l = np.degrees(np.arctan2(dy_l, max(dx_l, 1.0)))

    dx_r = abs(right_apex[0] - mouth_right[0])
    dy_r = mouth_right[1] - right_apex[1]
    angle_r = np.degrees(np.arctan2(dy_r, max(dx_r, 1.0)))
    avg_angle = (angle_l + angle_r) / 2.0

    # 8. Clinical Classification & Suggestion Logic
    # High cheekbone ideal: zygoma-to-jaw ratio ~ 1.25-1.35, malar projection ratio ~ 0.55-0.65
    suggested_ck1 = 1.0
    suggested_ck2 = 0.6
    suggested_ck3 = 0.0
    primary_concern = "midface-sagging"
    asymmetry_mode = False
    left_mult = 1.0
    right_mult = 1.0

    if symmetry_score < 88.0:
        asymmetry_mode = True
        primary_concern = "cheek-asymmetry"
        if left_lateral_dist < right_lateral_dist:
            left_mult = 1.25
            right_mult = 0.85
        else:
            left_mult = 0.85
            right_mult = 1.25

    if concavity_ratio > 0.08:
        # Noticeable gauntness in submalar region
        suggested_ck3 = round(min(1.4, concavity_ratio * 12.0), 1)
        if not asymmetry_mode:
            primary_concern = "submalar-hollow"

    if malar_projection_ratio < 0.50:
        # Flat malar apex
        suggested_ck2 = 1.2
        if not asymmetry_mode and suggested_ck3 < 0.8:
            primary_concern = "flat-malar"

    if zygoma_to_jaw_ratio < 1.20:
        # Narrow zygoma, would benefit from lateral lift
        suggested_ck1 = 1.5

    total_rec_vol = round(suggested_ck1 + suggested_ck2 + suggested_ck3, 1)

    # Clinical recommendation text
    if primary_concern == "submalar-hollow":
        recommendation_text = (
            f"Detected moderate gauntness in the lower submalar hollow (inward concavity ratio {concavity_ratio:.2f}). "
            f"We recommend {suggested_ck3} mL in the submalar zone (CK3) combined with {suggested_ck1} mL lateral arch (CK1) "
            "to soften lower cheek hollows while preserving natural skeletal contour."
        )
    elif primary_concern == "flat-malar":
        recommendation_text = (
            "Detected mild flattening of the anterior malar prominence. "
            f"We recommend focusing {suggested_ck2} mL on the malar apex (CK2) for forward light-reflection projection, "
            f"supported by {suggested_ck1} mL on the outer zygoma (CK1) for structural midface lift."
        )
    elif primary_concern == "cheek-asymmetry":
        recommendation_text = (
            f"Detected midface volume asymmetry (symmetry score {symmetry_score:.0f}%). "
            "We recommend Asymmetry Mode with differential left vs. right volume multipliers "
            "to balance lateral projection and achieve bilateral facial harmony."
        )
    else:
        recommendation_text = (
            f"Your bizygomatic-to-jaw ratio is 1:{zygoma_to_jaw_ratio:.2f}. "
            "A balanced multi-vector enhancement (1.0 mL lateral lift + 0.5 mL malar projection) "
            "will accentuate the high cheekbone apex and restore youthful midface dynamics."
        )

    # Estimate age range & elasticity
    skin_elasticity = 1.0
    age_range = "30-45"
    if concavity_ratio > 0.10:
        age_range = "45-60"
        skin_elasticity = 1.1
    elif malar_projection_ratio > 0.60 and symmetry_score > 92.0:
        age_range = "18-30"
        skin_elasticity = 0.9

    return {
        "zone": "cheeks",
        "metrics": {
            "bizygomatic_width_px": float(round(bizygomatic_width, 1)),
            "malar_projection_ratio": float(round(malar_projection_ratio, 2)),
            "submalar_concavity_score": float(round(concavity_ratio * 100.0, 1)),
            "midface_symmetry_score": float(round(symmetry_score, 1)),
            "apex_elevation_angle": float(round(avg_angle, 1)),
            "zygoma_to_jaw_ratio": float(round(zygoma_to_jaw_ratio, 2)),
        },
        "recommendation": {
            "text": recommendation_text,
            "suggested_volume_ml": total_rec_vol,
        },
        "suggested_parameters": {
            "lateral_volume_ck1": suggested_ck1,
            "medial_volume_ck2": suggested_ck2,
            "submalar_volume_ck3": suggested_ck3,
            "asymmetry_mode": asymmetry_mode,
            "left_cheek_multiplier": left_mult,
            "right_cheek_multiplier": right_mult,
            "skin_elasticity": skin_elasticity,
            "volumeMl": total_rec_vol,
        },
        "suggested_answers": {
            "gender": "female",
            "ageRange": age_range,
            "primaryConcern": primary_concern,
            "experience": "first-time",
            "desiredOutcome": "contour" if suggested_ck1 >= 1.5 else "natural",
            "skinElasticity": "lax" if skin_elasticity > 1.05 else ("tight" if skin_elasticity < 0.95 else "normal"),
            "symmetryConcern": "significant" if symmetry_score < 80 else ("mild" if symmetry_score < 90 else "none"),
        },
    }
