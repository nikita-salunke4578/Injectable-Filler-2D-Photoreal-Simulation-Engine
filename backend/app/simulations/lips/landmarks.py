import numpy as np

# MediaPipe Face Mesh indices for outer lips
OUTER_LIP_INDICES = [
    61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 
    409, 270, 269, 267, 0, 37, 39, 40
]

# MediaPipe Face Mesh indices for inner lips (where lips meet)
INNER_LIP_INDICES = [
    78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308,
    415, 310, 311, 312, 13, 82, 81, 80
]

NOSE_BASE_INDICES = [2, 94, 324] # Columella and nostril bases roughly
CUPIDS_BOW_INDICES = [37, 267] # The two upper peaks
MOUTH_CORNERS = [61, 291] # Left and right corners

# Additional landmarks for enhanced analysis
PHILTRUM_COLUMN_INDICES = [164, 165, 167, 393, 391, 396]  # Left and right philtral ridges
NOSE_TIP_INDEX = 1  # Nose tip for philtrum length reference
CHIN_INDEX = 152  # Bottom of chin for face height
LEFT_UPPER_LIP_INDICES = [37, 39, 40, 61]  # Left side of upper lip
RIGHT_UPPER_LIP_INDICES = [267, 269, 270, 291]  # Right side of upper lip
LEFT_LOWER_LIP_INDICES = [146, 91, 181, 84]  # Left side of lower lip
RIGHT_LOWER_LIP_INDICES = [314, 405, 321, 375]  # Right side of lower lip
UPPER_LIP_TOP_CENTER = 0  # Center top of upper lip
LOWER_LIP_BOTTOM_CENTER = 17  # Center bottom of lower lip

def extract_lip_landmarks(face_landmarks: np.ndarray) -> dict[str, np.ndarray]:
    """
    Extracts the outer and inner lip polygons, and other key structural landmarks.
    
    Args:
        face_landmarks: (478, 2) numpy array of face landmarks.
        
    Returns:
        Dictionary containing arrays for 'outer_lips', 'inner_lips', 'nose_base', 'cupids_bow', 'corners',
        and additional landmarks for analysis.
    """
    return {
        'outer_lips': face_landmarks[OUTER_LIP_INDICES],
        'inner_lips': face_landmarks[INNER_LIP_INDICES],
        'nose_base': face_landmarks[NOSE_BASE_INDICES],
        'cupids_bow': face_landmarks[CUPIDS_BOW_INDICES],
        'corners': face_landmarks[MOUTH_CORNERS],
        'philtrum_columns': face_landmarks[PHILTRUM_COLUMN_INDICES],
        'nose_tip': face_landmarks[NOSE_TIP_INDEX],
        'chin': face_landmarks[CHIN_INDEX],
        'left_upper': face_landmarks[LEFT_UPPER_LIP_INDICES],
        'right_upper': face_landmarks[RIGHT_UPPER_LIP_INDICES],
        'left_lower': face_landmarks[LEFT_LOWER_LIP_INDICES],
        'right_lower': face_landmarks[RIGHT_LOWER_LIP_INDICES],
        'upper_center': face_landmarks[UPPER_LIP_TOP_CENTER],
        'lower_center': face_landmarks[LOWER_LIP_BOTTOM_CENTER],
    }
