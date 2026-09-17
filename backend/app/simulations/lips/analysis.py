import numpy as np
from app.common.face_detection import FaceDetector
from app.simulations.lips.landmarks import extract_lip_landmarks


def _euclidean(p1: np.ndarray, p2: np.ndarray) -> float:
    """Euclidean distance between two 2D points."""
    return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))


def _classify_vermilion(upper_h: float, lower_h: float, face_height: float) -> str:
    """Classify vermilion thickness relative to face height."""
    total_lip_h = upper_h + lower_h
    ratio = total_lip_h / face_height if face_height > 0 else 0
    if ratio < 0.06:
        return "thin"
    elif ratio < 0.10:
        return "medium"
    return "full"


def _classify_cupids_bow(bow_pts: np.ndarray, upper_center: np.ndarray) -> str:
    """Classify cupid's bow definition based on peak elevation above center."""
    if len(bow_pts) < 2:
        return "flat"
    avg_bow_y = np.mean(bow_pts[:, 1])
    center_y = upper_center[1]
    diff = center_y - avg_bow_y  # positive = bow peaks are above center
    if diff < 2:
        return "flat"
    elif diff < 6:
        return "moderate"
    return "defined"


def _compute_symmetry(left_pts: np.ndarray, right_pts: np.ndarray, center_x: float) -> float:
    """Compute symmetry score (0-100) by comparing left and right side distances from center."""
    if len(left_pts) == 0 or len(right_pts) == 0:
        return 50.0
    
    left_dists = np.abs(left_pts[:, 0] - center_x)
    right_dists = np.abs(right_pts[:, 0] - center_x)
    
    # Match corresponding pairs
    n = min(len(left_dists), len(right_dists))
    left_dists = np.sort(left_dists)[:n]
    right_dists = np.sort(right_dists)[:n]
    
    if n == 0:
        return 50.0
    
    max_dist = max(np.max(left_dists), np.max(right_dists), 1.0)
    differences = np.abs(left_dists - right_dists) / max_dist
    score = max(0.0, 100.0 * (1.0 - np.mean(differences)))
    return round(score, 1)


def _compute_corner_angle(corners: np.ndarray, center: np.ndarray) -> float:
    """Compute mouth corner angle in degrees. Negative = downturned, positive = upturned."""
    if len(corners) < 2:
        return 0.0
    # Average of left and right corner vertical offsets relative to center
    left_corner = corners[0]
    right_corner = corners[1]
    center_y = center[1]
    
    # Negative y offset means corners are above center (upturned)
    avg_offset = ((left_corner[1] - center_y) + (right_corner[1] - center_y)) / 2.0
    # Convert to approximate angle (using horizontal distance as reference)
    horiz_dist = abs(right_corner[0] - left_corner[0]) / 2.0
    if horiz_dist < 1:
        return 0.0
    angle_rad = np.arctan2(-avg_offset, horiz_dist)
    return round(float(np.degrees(angle_rad)), 1)


def _estimate_gender(philtrum_length: float, lip_ratio: float, face_height: float) -> str:
    """Estimate gender from facial proportions. Purely heuristic."""
    philtrum_ratio = philtrum_length / face_height if face_height > 0 else 0
    # Female philtrums tend to be proportionally shorter
    if philtrum_ratio < 0.09 and lip_ratio < 0.7:
        return "female"
    elif philtrum_ratio > 0.11:
        return "male"
    return "female"  # Default


def _estimate_age_range(symmetry: float, vermilion: str, philtrum_length: float, face_height: float) -> str:
    """Estimate age range from facial features. Purely heuristic."""
    philtrum_ratio = philtrum_length / face_height if face_height > 0 else 0
    if philtrum_ratio > 0.12 and vermilion == "thin":
        return "60+"
    elif philtrum_ratio > 0.10 and symmetry < 80:
        return "45-60"
    elif philtrum_ratio > 0.085:
        return "30-45"
    return "18-30"


def _determine_primary_concern(
    philtrum_length: float, face_height: float, 
    vermilion: str, corner_angle: float, 
    age_range: str
) -> str:
    """Determine the most likely primary concern from metrics."""
    philtrum_ratio = philtrum_length / face_height if face_height > 0 else 0
    
    if philtrum_ratio > 0.10:
        return "long-upper-lip"
    if vermilion == "thin":
        return "thin-vermilion"
    if corner_angle < -3.0:
        return "downturned-corners"
    if age_range in ("45-60", "60+"):
        return "aging-rejuvenation"
    return "thin-vermilion"


def _compute_suggested_parameters(
    philtrum_length: float, face_height: float,
    vermilion: str, cupids_bow_def: str,
    corner_angle: float, symmetry: float,
    primary_concern: str
) -> dict:
    """Compute suggested slider values (0-100) based on analysis metrics."""
    philtrum_ratio = philtrum_length / face_height if face_height > 0 else 0
    
    # Philtral shortening: higher when philtrum is long
    if philtrum_ratio > 0.12:
        phil_short = 70
    elif philtrum_ratio > 0.10:
        phil_short = 50
    elif philtrum_ratio > 0.085:
        phil_short = 30
    else:
        phil_short = 10
    
    # Vermilion show: higher when lips are thin
    verm_map = {"thin": 55, "medium": 30, "full": 10}
    verm_show = verm_map.get(vermilion, 30)
    
    # Cupid's bow: higher when bow is flat
    bow_map = {"flat": 60, "moderate": 30, "defined": 10}
    cupid = bow_map.get(cupids_bow_def, 30)
    
    # Philtral column: moderate default
    phil_col = 20 if vermilion == "thin" else 10
    
    # Dental show: mild for most, higher for aging
    dental = 15
    if primary_concern == "aging-rejuvenation":
        dental = 30
    
    # Adjust based on primary concern
    if primary_concern == "long-upper-lip":
        phil_short = max(phil_short, 60)
    elif primary_concern == "thin-vermilion":
        verm_show = max(verm_show, 50)
    elif primary_concern == "downturned-corners":
        phil_short = min(phil_short, 20)
        dental = 10
    
    return {
        "philtralShortening": phil_short,
        "vermilionShow": verm_show,
        "cupidsBow": cupid,
        "philtralColumn": phil_col,
        "dentalShow": dental,
    }


def _determine_lip_shape(cupids_bow_def: str, lip_ratio: float, lip_width: float, face_height: float) -> str:
    """Determine current lip shape classification."""
    width_ratio = lip_width / face_height if face_height > 0 else 0
    if cupids_bow_def == "defined" and lip_ratio < 0.65:
        return "heart"
    elif width_ratio > 0.35:
        return "wide"
    return "round"


def _determine_symmetry_concern(symmetry_score: float) -> str:
    """Determine symmetry concern level."""
    if symmetry_score >= 90:
        return "none"
    elif symmetry_score >= 75:
        return "mild"
    return "significant"


def analyze_facial_proportions(image: np.ndarray, face_detector: FaceDetector = None) -> dict:
    """
    Scans the face and computes the mathematical proportions of the lips to recommend a surgical plan.
    Uses the Golden Ratio (1:1.618) as the ideal standard for upper-to-lower lip height.
    
    Returns rich metrics including symmetry, vermilion classification, cupid's bow definition,
    mouth corner angle, and auto-suggested assessment answers + slider parameters.
    """
    if face_detector is None:
        face_detector = FaceDetector()
        
    try:
        face_pts = face_detector.get_landmarks(image)
    except ValueError:
        return {"error": "No face detected in the image."}
        
    lip_pts = extract_lip_landmarks(face_pts)
    outer_lips = lip_pts['outer_lips']
    inner_lips = lip_pts['inner_lips']
    corners = lip_pts['corners']
    cupids_bow_pts = lip_pts['cupids_bow']
    nose_base = lip_pts['nose_base']
    
    # ── Core Measurements ───────────────────────────────────────────
    
    center_x = np.mean(outer_lips[:, 0])
    center_y = np.mean(outer_lips[:, 1])
    center = np.array([center_x, center_y])
    
    # Upper lip height
    upper_outer_y = np.min(outer_lips[outer_lips[:, 1] < center_y][:, 1]) if np.any(outer_lips[:, 1] < center_y) else center_y
    upper_inner_y = np.max(inner_lips[inner_lips[:, 1] < center_y][:, 1]) if np.any(inner_lips[:, 1] < center_y) else center_y
    upper_height = abs(upper_inner_y - upper_outer_y)
    
    # Lower lip height
    lower_outer_y = np.max(outer_lips[outer_lips[:, 1] > center_y][:, 1]) if np.any(outer_lips[:, 1] > center_y) else center_y
    lower_inner_y = np.min(inner_lips[inner_lips[:, 1] > center_y][:, 1]) if np.any(inner_lips[:, 1] > center_y) else center_y
    lower_height = abs(lower_outer_y - lower_inner_y)
    
    if lower_height == 0:
        lower_height = 1
        
    current_ratio = upper_height / lower_height
    ideal_ratio = 1.0 / 1.618
    
    # Lip width (corner to corner)
    lip_width = _euclidean(corners[0], corners[1])
    
    # Philtrum length (nose base center to upper lip top center)
    nose_base_center = np.mean(nose_base, axis=0)
    upper_lip_top = lip_pts['upper_center']
    philtrum_length = _euclidean(nose_base_center, upper_lip_top)
    
    # Face height (nose tip to chin as reference)
    chin = lip_pts['chin']
    nose_tip = lip_pts['nose_tip']
    face_height = _euclidean(nose_tip, chin)
    if face_height < 1:
        face_height = 1
    
    # ── Derived Metrics ─────────────────────────────────────────────
    
    vermilion = _classify_vermilion(upper_height, lower_height, face_height)
    cupids_bow_def = _classify_cupids_bow(cupids_bow_pts, lip_pts['upper_center'])
    
    # Symmetry (compare left and right lip halves)
    left_all = np.vstack([lip_pts['left_upper'], lip_pts['left_lower']])
    right_all = np.vstack([lip_pts['right_upper'], lip_pts['right_lower']])
    symmetry_score = _compute_symmetry(left_all, right_all, center_x)
    
    # Corner angle
    corner_angle = _compute_corner_angle(corners, center)
    
    # ── Estimates & Suggestions ─────────────────────────────────────
    
    estimated_gender = _estimate_gender(philtrum_length, current_ratio, face_height)
    estimated_age = _estimate_age_range(symmetry_score, vermilion, philtrum_length, face_height)
    primary_concern = _determine_primary_concern(
        philtrum_length, face_height, vermilion, corner_angle, estimated_age
    )
    lip_shape = _determine_lip_shape(cupids_bow_def, current_ratio, lip_width, face_height)
    symmetry_concern = _determine_symmetry_concern(symmetry_score)
    
    suggested_params = _compute_suggested_parameters(
        philtrum_length, face_height, vermilion, cupids_bow_def,
        corner_angle, symmetry_score, primary_concern
    )
    
    # ── Recommendation Text ─────────────────────────────────────────
    
    ratio_diff = current_ratio - ideal_ratio
    
    if abs(ratio_diff) < 0.1:
        recommendation_text = (
            "Your lips are already very close to the ideal 'Golden Ratio' (1:1.618). "
            "We recommend a conservative approach (0.5ml - 1.0ml) distributed evenly to maintain natural symmetry while adding overall hydration and subtle plumpness."
        )
        suggested_volume = 0.8
        suggested_balance = 0
    elif ratio_diff > 0:
        recommendation_text = (
            f"Your current upper-to-lower lip ratio is approx. 1:{1/current_ratio:.1f}. "
            "The ideal surgical standard is 1:1.6 (the Golden Ratio). Since your upper lip is relatively fuller, "
            "we recommend focusing volume on the lower lip to balance the profile and achieve structural harmony."
        )
        suggested_balance = 50
        suggested_volume = 1.2
    else:
        recommendation_text = (
            f"Your current upper-to-lower lip ratio is approx. 1:{1/current_ratio:.1f}. "
            "The ideal surgical standard is 1:1.6 (the Golden Ratio). Since your lower lip is dominant, "
            "we recommend focusing volume on the upper lip. This will enhance the Cupid's Bow definition and improve overall facial balance."
        )
        suggested_balance = -50
        suggested_volume = 1.0
        
    return {
        "metrics": {
            "upper_height_px": float(upper_height),
            "lower_height_px": float(lower_height),
            "current_ratio": float(current_ratio),
            "ideal_ratio": float(ideal_ratio),
            "lip_width_px": float(lip_width),
            "philtrum_length_px": float(philtrum_length),
            "vermilion_thickness": vermilion,
            "symmetry_score": float(symmetry_score),
            "cupids_bow_definition": cupids_bow_def,
            "mouth_corner_angle": float(corner_angle),
        },
        "recommendation": {
            "text": recommendation_text,
            "suggested_volume_ml": suggested_volume,
            "suggested_upper_lower_balance": suggested_balance,
        },
        "suggested_parameters": suggested_params,
        "suggested_answers": {
            "gender": estimated_gender,
            "ageRange": estimated_age,
            "primaryConcern": primary_concern,
            "experience": "first-time",
            "desiredOutcome": "natural",
            "lipShape": lip_shape,
            "symmetryConcern": symmetry_concern,
        },
    }
