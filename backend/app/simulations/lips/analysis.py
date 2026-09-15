import numpy as np
from app.common.face_detection import FaceDetector
from app.simulations.lips.landmarks import extract_lip_landmarks

def analyze_facial_proportions(image: np.ndarray, face_detector: FaceDetector = None) -> dict:
    """
    Scans the face and computes the mathematical proportions of the lips to recommend a surgical plan.
    Uses the Golden Ratio (1:1.618) as the ideal standard for upper-to-lower lip height.
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
    
    # 1. Compute Heights
    # Upper lip height = distance from cupid's bow/top center to inner top center
    # Outer top center index in our list: 37, 0, 267 (0 is usually center)
    # Inner top center index: 13
    # Actually, simpler: find min/max y for upper and lower parts.
    
    center_x = np.mean(outer_lips[:, 0])
    center_y = np.mean(outer_lips[:, 1])
    
    # Upper lip points: py < center_y
    upper_outer_y = np.min(outer_lips[outer_lips[:, 1] < center_y][:, 1])
    upper_inner_y = np.max(inner_lips[inner_lips[:, 1] < center_y][:, 1])
    upper_height = abs(upper_inner_y - upper_outer_y)
    
    # Lower lip points: py > center_y
    lower_outer_y = np.max(outer_lips[outer_lips[:, 1] > center_y][:, 1])
    lower_inner_y = np.min(inner_lips[inner_lips[:, 1] > center_y][:, 1])
    lower_height = abs(lower_outer_y - lower_inner_y)
    
    if lower_height == 0:
        lower_height = 1
        
    current_ratio = upper_height / lower_height
    ideal_ratio = 1.0 / 1.618
    
    # 2. Formulate Surgical Recommendation
    # If current_ratio > ideal_ratio, upper lip is relatively large -> focus on lower lip.
    # If current_ratio < ideal_ratio, lower lip is relatively large -> focus on upper lip.
    
    recommendation_text = ""
    suggested_balance = 0
    suggested_volume = 1.0
    
    ratio_diff = current_ratio - ideal_ratio
    
    if abs(ratio_diff) < 0.1:
        recommendation_text = (
            "Your lips are already very close to the ideal 'Golden Ratio' (1:1.618). "
            "We recommend a conservative approach (0.5ml - 1.0ml) distributed evenly to maintain natural symmetry while adding overall hydration and subtle plumpness."
        )
        suggested_balance = 0
        suggested_volume = 0.8
    elif ratio_diff > 0:
        recommendation_text = (
            f"Your current upper-to-lower lip ratio is approx. 1:{1/current_ratio:.1f}. "
            "The ideal surgical standard is 1:1.6 (the Golden Ratio). Since your upper lip is relatively fuller, "
            "we recommend focusing volume on the lower lip to balance the profile and achieve structural harmony."
        )
        suggested_balance = 50  # Favor lower lip
        suggested_volume = 1.2
    else:
        recommendation_text = (
            f"Your current upper-to-lower lip ratio is approx. 1:{1/current_ratio:.1f}. "
            "The ideal surgical standard is 1:1.6 (the Golden Ratio). Since your lower lip is dominant, "
            "we recommend focusing volume on the upper lip. This will enhance the Cupid's Bow definition and improve overall facial balance."
        )
        suggested_balance = -50  # Favor upper lip
        suggested_volume = 1.0
        
    return {
        "metrics": {
            "upper_height_px": float(upper_height),
            "lower_height_px": float(lower_height),
            "current_ratio": float(current_ratio),
            "ideal_ratio": float(ideal_ratio)
        },
        "recommendation": {
            "text": recommendation_text,
            "suggested_volume_ml": suggested_volume,
            "suggested_upper_lower_balance": suggested_balance
        }
    }
