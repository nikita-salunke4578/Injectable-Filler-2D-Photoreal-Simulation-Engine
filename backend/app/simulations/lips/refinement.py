import cv2
import numpy as np

def refine_lip_region(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Applies a mild unsharp mask to the lip region to restore texture that might 
    have been slightly softened during TPS deformation. Avoids the heavy "plastic" 
    blur of a bilateral filter.
    
    Args:
        image: Deformed BGR image.
        mask: Binary mask of the vermilion region.
        
    Returns:
        Refined image.
    """
    # Create a slightly blurred version
    gaussian = cv2.GaussianBlur(image, (5, 5), 2.0)
    
    # Calculate unsharp mask: original + (original - blurred) * amount
    # We use addWeighted: alpha * src1 + beta * src2 + gamma
    # Unsharp mask formula: refined = original + (original - gaussian) * amount
    # Rearranged: refined = original * (1 + amount) + gaussian * (-amount)
    amount = 0.5
    unsharp = cv2.addWeighted(image, 1.0 + amount, gaussian, -amount, 0)
    
    # Only apply the sharpening where the mask is active
    # Normalize mask to [0, 1] for alpha blending
    mask_norm = mask.astype(np.float32) / 255.0
    if len(mask_norm.shape) == 2:
        mask_norm = np.expand_dims(mask_norm, axis=-1)
        
    # Blend the sharpened region over the original deformed image
    refined = (unsharp * mask_norm + image * (1.0 - mask_norm)).astype(np.uint8)
    
    return refined
