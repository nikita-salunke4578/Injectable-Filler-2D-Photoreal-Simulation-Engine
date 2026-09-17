import cv2
import numpy as np

def build_lip_mask(image_shape: tuple[int, ...], lip_pts: dict[str, np.ndarray], feather_amount: int = 35) -> np.ndarray:
    """
    Creates a lip-contour mask that tightly hugs the lips.
    
    Uses a dilated convex hull of the outer lip landmarks so the mask
    covers ONLY the lips and a thin band of surrounding skin — never
    reaching the nose, mustache, beard, or chin.
    """
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    outer_pts = lip_pts['outer_lips']
    inner_pts = lip_pts['inner_lips']
    
    # Combine outer + inner lip points → convex hull
    all_lip_pts = np.vstack([outer_pts, inner_pts]).astype(np.int32)
    hull = cv2.convexHull(all_lip_pts)
    
    # Fill the convex hull
    cv2.fillConvexPoly(mask, hull, 255)
    
    # Dilate slightly so the blend covers the lip border + ~15px of skin.
    # This is enough for a seamless edge without reaching the nose.
    dilate_px = 15
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    # Gaussian feather for smooth alpha-blend boundary
    if feather_amount > 0:
        ksize = feather_amount if feather_amount % 2 == 1 else feather_amount + 1
        mask = cv2.GaussianBlur(mask, (ksize, ksize), 0)
        
    return mask
