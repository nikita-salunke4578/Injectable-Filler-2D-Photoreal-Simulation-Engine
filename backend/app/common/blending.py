import cv2
import numpy as np

def poisson_blend(foreground: np.ndarray, background: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Seamlessly blends the foreground into the background using Poisson image editing.
    The mask defines the region of the foreground to blend.
    """
    # Find the bounding box of the mask to get the center
    y_indices, x_indices = np.where(mask > 0)
    if len(x_indices) == 0 or len(y_indices) == 0:
        return background

    center_x = int(np.mean(x_indices))
    center_y = int(np.mean(y_indices))
    
    # Ensure mask is 8-bit single channel, as required by cv2.seamlessClone
    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    mask = mask.astype(np.uint8)
    
    # Apply seamless clone
    try:
        blended = cv2.seamlessClone(foreground, background, mask, (center_x, center_y), cv2.NORMAL_CLONE)
        return blended
    except Exception as e:
        # Fallback to alpha blending if seamlessClone fails
        print(f"Poisson blend failed: {e}. Falling back to alpha blend.")
        mask_norm = mask.astype(np.float32) / 255.0
        if len(mask_norm.shape) == 2:
            mask_norm = np.expand_dims(mask_norm, axis=-1)
        return (foreground * mask_norm + background * (1 - mask_norm)).astype(np.uint8)
