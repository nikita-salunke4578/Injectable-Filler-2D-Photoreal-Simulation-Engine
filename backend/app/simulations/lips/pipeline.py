import numpy as np

from app.common.face_detection import FaceDetector
from app.simulations.lips.landmarks import extract_lip_landmarks
from app.simulations.lips.mask import build_lip_mask
from app.simulations.lips.deformation import apply_lip_deformation
from app.simulations.lips.refinement import refine_lip_region

def run_lips_pipeline(
    image: np.ndarray,
    volume_ml: float,
    intensity: float,
    upper_lower_balance: float = 0.0,
    face_detector: FaceDetector = None
) -> np.ndarray:
    """
    Executes the complete Lips simulation pipeline.
    
    Stages:
    1. Face Detection & Landmark Extraction
    2. Lip Mask Generation
    3. Thin Plate Spline (TPS) Deformation
    4. Local Refinement (Simulated AI)
    5. Poisson Blending
    
    Args:
        image: BGR numpy array (original photo).
        volume_ml: Target volume.
        intensity: Normalised intensity (0-1).
        upper_lower_balance: -100 to 100 weighting.
        face_detector: Instance of FaceDetector to avoid re-initializing.
        
    Returns:
        The simulated BGR image.
    """
    if face_detector is None:
        face_detector = FaceDetector()
        
    # 1. Face Detection & Landmark Extraction
    face_pts = face_detector.get_landmarks(image)
    lip_pts = extract_lip_landmarks(face_pts)
    
    # 2. Lip Mask Generation
    # We use a slight feathering so the blend is smooth.
    mask = build_lip_mask(image.shape, lip_pts, feather_amount=15)
    
    # 3. Deformation (TPS)
    deformed_img = apply_lip_deformation(
        image=image,
        lip_pts=lip_pts,
        volume=volume_ml,
        intensity=intensity,
        upper_lower_balance=upper_lower_balance
    )
    
    # 4. Refinement (Simulated Generative AI cleanup)
    refined_img = refine_lip_region(deformed_img, mask)
    
    # 5. Alpha Blending (Merge the refined lip back into the original image seamlessly)
    mask_norm = mask.astype(np.float32) / 255.0
    if len(mask_norm.shape) == 2:
        mask_norm = np.expand_dims(mask_norm, axis=-1)
    
    final_img = (refined_img * mask_norm + image * (1.0 - mask_norm)).astype(np.uint8)
    
    # 6. Dotted Line Overlay
    # Draw a dotted/dashed line of the original outer_lips to show the "before" state
    import cv2
    original_pts = lip_pts['outer_lips'].reshape((-1, 1, 2)).astype(np.int32)
    
    # Simple hack for dashed lines using cv2.polylines is hard, 
    # but we can draw circles at the landmark points and connect them or just draw small segments.
    # We will just draw a thin translucent line for simplicity and aesthetics.
    overlay = final_img.copy()
    cv2.polylines(overlay, [original_pts], isClosed=True, color=(255, 255, 255), thickness=1, lineType=cv2.LINE_AA)
    
    # Make the line slightly transparent
    alpha = 0.6
    final_img = cv2.addWeighted(overlay, alpha, final_img, 1 - alpha, 0)
    
    return final_img
