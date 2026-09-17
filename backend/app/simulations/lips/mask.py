import cv2
import numpy as np

def build_lip_mask(image_shape: tuple[int, ...], lip_pts: dict[str, np.ndarray], feather_amount: int = 45) -> np.ndarray:
    """
    Creates a binary mask for the lip region and surrounding skin, allowing
    skin deformations (like philtral shortening) to be visible when blended.
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    outer_pts = lip_pts['outer_lips']
    inner_pts = lip_pts['inner_lips']
    nose_base = lip_pts.get('nose_base', np.array([]))
    
    all_pts = np.vstack([outer_pts, inner_pts])
    if len(nose_base) > 0:
        all_pts = np.vstack([all_pts, nose_base])
        
    # Create a bounding box covering the nose to the chin
    x_min, y_min = np.min(all_pts, axis=0) - 60
    x_max, y_max = np.max(all_pts, axis=0) + 60
    
    x_min = max(int(x_min), 0)
    y_min = max(int(y_min), 0)
    x_max = min(int(x_max), image_shape[1])
    y_max = min(int(y_max), image_shape[0])
    
    # Draw a solid white rectangle in the ROI
    cv2.rectangle(mask, (x_min, y_min), (x_max, y_max), 255, -1)
    
    # Heavy feathering to blend the rectangular boundaries seamlessly
    if feather_amount > 0:
        ksize = feather_amount if feather_amount % 2 == 1 else feather_amount + 1
        mask = cv2.GaussianBlur(mask, (ksize, ksize), 0)
        
    return mask
