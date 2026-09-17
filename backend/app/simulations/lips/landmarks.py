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

def extract_lip_landmarks(face_landmarks: np.ndarray) -> dict[str, np.ndarray]:
    """
    Extracts the outer and inner lip polygons, and other key structural landmarks.
    
    Args:
        face_landmarks: (478, 2) numpy array of face landmarks.
        
    Returns:
        Dictionary containing arrays for 'outer_lips', 'inner_lips', 'nose_base', 'cupids_bow', 'corners'.
    """
    return {
        'outer_lips': face_landmarks[OUTER_LIP_INDICES],
        'inner_lips': face_landmarks[INNER_LIP_INDICES],
        'nose_base': face_landmarks[NOSE_BASE_INDICES],
        'cupids_bow': face_landmarks[CUPIDS_BOW_INDICES],
        'corners': face_landmarks[MOUTH_CORNERS],
    }
