import cv2
import numpy as np

def build_lip_mask(image_shape: tuple[int, ...], lip_pts: dict[str, np.ndarray], feather_amount: int = 11) -> np.ndarray:
    """
    Creates a binary mask for the lip region (vermilion only) and applies Gaussian feathering.
    
    Args:
        image_shape: Shape of the image (H, W, C).
        lip_pts: Dictionary containing 'outer_lips' and 'inner_lips'.
        feather_amount: Amount of Gaussian blur to apply for smooth edges.
        
    Returns:
        (H, W) numpy array representing the mask with values [0, 255].
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    # Fill the outer polygon defined by lip points
    outer_pts = lip_pts['outer_lips'].reshape((-1, 1, 2)).astype(np.int32)
    cv2.fillPoly(mask, [outer_pts], 255)
    
    # Subtract (fill with black) the inner polygon
    inner_pts = lip_pts['inner_lips'].reshape((-1, 1, 2)).astype(np.int32)
    cv2.fillPoly(mask, [inner_pts], 0)
    
    # Feather the edges
    if feather_amount > 0:
        ksize = feather_amount if feather_amount % 2 == 1 else feather_amount + 1
        mask = cv2.GaussianBlur(mask, (ksize, ksize), 0)
        
    return mask
