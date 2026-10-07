"""
Cheek / midface proportion analysis.

Measures the face from MediaPipe landmarks (in the face's own rolled frame, so
head tilt does not matter) and turns the numbers into:

  * display metrics               -> ``metrics``        (keys used by Consultation.tsx)
  * a clinical-style summary      -> ``recommendation``
  * auto-fill slider values       -> ``suggested_parameters``  (CheekParameters in types/simulation.ts)
  * auto-selected quiz answers    -> ``suggested_answers``

NOTE: thresholds are geometric heuristics, not clinically validated. Tune
them against your own reviewed photo set (see the constants below).

Left/right in ``suggested_parameters`` refer to the PATIENT's cheeks (same as
the UI labels); that is the opposite of the image side for a normal photo.
"""
from __future__ import annotations

import numpy as np

from app.simulations.cheeks.detector import detect_landmarks
from app.simulations.cheeks.landmarks import extract_cheek_landmarks

# ---- tunable thresholds ---------------------------------------------------
SYMMETRY_FLAG_BELOW = 88.0       # % ; below -> suggest asymmetry mode
MAX_YAW_RATIO_FOR_ASYM = 0.75    # min/max edge distance; below = head turned, ignore asymmetry
HOLLOW_FLAG_ABOVE = 15.0         # submalar_concavity_score
FLAT_MALAR_BELOW = 0.50          # malar_projection_ratio
NARROW_ZYGOMA_BELOW = 1.20       # zygoma_to_jaw_ratio
HOLLOW_SCORE_GAIN = 3.0          # 1% of bizygomatic width of inward bow == score 3.0
PATIENT_SIDE_IS_MIRRORED = True  # keep in sync with pipeline.PATIENT_SIDE_IS_MIRRORED


def _inward_bow(p, edge: int, mids: list[int], jaw: int, toward_mid: np.ndarray) -> float:
    """Distance (px) the lower-cheek contour bows INWARD from the zygoma->jaw chord (+ = hollow)."""
    a, b = p[edge], p[jaw]
    ch = b - a
    n = np.array([-ch[1], ch[0]], np.float32) / max(float(np.linalg.norm(ch)), 1e-6)
    if float(n @ toward_mid) < 0:
        n = -n
    return float(np.mean([(p[m] - a) @ n for m in mids]))


def analyze_cheek_proportions(image: np.ndarray, face_detector=None) -> dict:
    try:
        face_pts = detect_landmarks(image, face_detector)
    except ValueError:
        return {"error": "No face detected in the image."}

    p = face_pts.astype(np.float32)
    lm = extract_cheek_landmarks(p)
    u, v, o = lm.roll_u, lm.roll_v, p[6]

    def T(i):    # signed distance along the eye line from the midline (+ = image right)
        return float((p[i] - o) @ u)

    def S(i):    # signed distance "down" the face from the nose bridge
        return float((p[i] - o) @ v)

    # 1. widths ---------------------------------------------------------------
    bizygomatic = max(abs(T(454) - T(234)), 1.0)
    bigonial = max(abs(T(397) - T(172)), 1.0)
    zyg_jaw = bizygomatic / bigonial

    # 2. symmetry (distance of paired contour points from the midline) --------
    pairs = [(234, 454), (93, 323), (58, 288), (61, 291)]
    diffs = []
    for l, r in pairs:
        dl, dr = abs(T(l)), abs(T(r))
        diffs.append(abs(dl - dr) / max(dl, dr, 1.0))
    symmetry = float(np.clip(100.0 * (1.0 - float(np.mean(diffs)) * 1.5), 0.0, 100.0))
    dl_edge, dr_edge = abs(T(234)), abs(T(454))
    yaw_ratio = min(dl_edge, dr_edge) / max(dl_edge, dr_edge, 1.0)

    # 3. submalar hollow (contour bows inward between zygoma and jaw) ---------
    bow_l = _inward_bow(p, 234, [93, 132], 58, u)        # image-left cheek: midline is toward +u
    bow_r = _inward_bow(p, 454, [323, 361], 288, -u)     # image-right cheek: midline is toward -u
    concavity = max(0.0, 100.0 * ((bow_l + bow_r) / 2.0) / bizygomatic) * HOLLOW_SCORE_GAIN

    # 4. malar projection: how high the widest point (zygoma) sits between nose base and eye line
    eye_s, nose_s = (S(33) + S(263)) / 2.0, S(2)
    zyg_s = (S(234) + S(454)) / 2.0
    malar_ratio = (nose_s - zyg_s) / max(nose_s - eye_s, 1.0)

    # 5. apex elevation: mouth corner -> malar apex ---------------------------
    angles = []
    for apex, mouth in ((lm.left_apex, p[61]), (lm.right_apex, p[291])):
        d = apex - mouth
        angles.append(np.degrees(np.arctan2(-(d @ v), max(abs(float(d @ u)), 1.0))))
    apex_angle = float(np.mean(angles))

    # 6. suggestions ----------------------------------------------------------
    ck1, ck2, ck3 = 1.0, 0.6, 0.0
    concern = "midface-sagging"
    asym, patient_l, patient_r = False, 1.0, 1.0

    if symmetry < SYMMETRY_FLAG_BELOW and yaw_ratio >= MAX_YAW_RATIO_FOR_ASYM:
        asym, concern = True, "cheek-asymmetry"
        narrower_img = "left" if dl_edge < dr_edge else "right"
        narrower_patient = ("right" if narrower_img == "left" else "left") if PATIENT_SIDE_IS_MIRRORED else narrower_img
        # correct ONLY the deficient (narrower) side; the reference side stays at 1.0.
        # boost grows with the measured asymmetry (1 - symmetry), clamped to a clinically sane range.
        boost = round(float(np.clip(1.0 + 2.5 * (1.0 - symmetry / 100.0), 1.15, 1.6)), 2)
        patient_l, patient_r = (boost, 1.0) if narrower_patient == "left" else (1.0, boost)

    if concavity > HOLLOW_FLAG_ABOVE:
        ck3 = round(float(min(1.4, 0.4 + (concavity - HOLLOW_FLAG_ABOVE) / 20.0)), 1)
        if not asym:
            concern = "submalar-hollow"

    if malar_ratio < FLAT_MALAR_BELOW:
        ck2 = 1.2
        if not asym and ck3 < 0.8:
            concern = "flat-malar"

    if zyg_jaw < NARROW_ZYGOMA_BELOW:
        ck1 = 1.5

    total = round(ck1 + ck2 + ck3, 1)

    if concern == "submalar-hollow":
        text = (f"Detected hollowing beneath the cheekbone (submalar score {concavity:.1f}). "
                f"We recommend {ck3} mL in the submalar zone (CK3) with {ck1} mL on the lateral arch (CK1) "
                "to soften the lower cheek while preserving skeletal contour.")
    elif concern == "flat-malar":
        text = ("Detected limited forward projection of the malar prominence. "
                f"We recommend {ck2} mL on the malar apex (CK2) for projection and light reflection, "
                f"supported by {ck1} mL on the lateral arch (CK1) for midface lift.")
    elif concern == "cheek-asymmetry":
        text = (f"Detected midface asymmetry (symmetry score {symmetry:.0f}%). "
                "Asymmetry Mode is suggested: only the deficient cheek is augmented; the reference cheek is left unchanged.")
    else:
        text = (f"Bizygomatic-to-jaw ratio is 1:{zyg_jaw:.2f}. A balanced enhancement "
                f"({ck1} mL lateral lift + {ck2} mL malar projection) will accentuate the cheekbone apex "
                "and restore midface support.")
    if yaw_ratio < MAX_YAW_RATIO_FOR_ASYM:
        text += " Note: the head appears turned; a straight-on photo gives more reliable symmetry readings."

    # skin_elasticity = the UI "Skin Elasticity Scale" (kernel spread): 0.9 tight/youthful .. 1.1 mature/lax
    elasticity, age_range = 1.0, "30-45"
    if concavity > 20.0:
        elasticity, age_range = 1.1, "45-60"
    elif malar_ratio > 0.60 and symmetry > 92.0 and concavity < 5.0:
        elasticity, age_range = 0.9, "18-30"

    return {
        "zone": "cheeks",
        "metrics": {
            "bizygomatic_width_px": float(round(bizygomatic, 1)),
            "malar_projection_ratio": float(round(malar_ratio, 2)),
            "submalar_concavity_score": float(round(concavity, 1)),
            "midface_symmetry_score": float(round(symmetry, 1)),
            "apex_elevation_angle": float(round(apex_angle, 1)),
            "zygoma_to_jaw_ratio": float(round(zyg_jaw, 2)),
        },
        "recommendation": {"text": text, "suggested_volume_ml": total},
        "suggested_parameters": {
            "lateral_volume_ck1": ck1,
            "medial_volume_ck2": ck2,
            "submalar_volume_ck3": ck3,
            "asymmetry_mode": asym,
            "left_cheek_multiplier": patient_l,
            "right_cheek_multiplier": patient_r,
            "skin_elasticity": elasticity,
            "volumeMl": total,
        },
        "suggested_answers": {
            "gender": "female",
            "ageRange": age_range,
            "primaryConcern": concern,
            "experience": "first-time",
            "desiredOutcome": "contour" if ck1 >= 1.5 else "natural",
            "skinElasticity": "lax" if elasticity > 1.05 else ("tight" if elasticity < 0.95 else "normal"),
            "symmetryConcern": "significant" if symmetry < 80 else ("mild" if symmetry < 90 else "none"),
        },
    }
