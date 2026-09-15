import cv2
import numpy as np
from scipy.interpolate import Rbf

def apply_lip_deformation(
    image: np.ndarray,
    lip_pts: dict[str, np.ndarray],
    volume: float,
    intensity: float,
    upper_lower_balance: float
) -> np.ndarray:
    """
    Applies Thin Plate Spline (TPS) deformation to the lip region to simulate volume enhancement.
    
    Args:
        image: Original BGR image.
        lip_pts: Dictionary containing 'outer_lips' and 'inner_lips'.
        volume: Target volume in mL. Determines max displacement.
        intensity: Normalized intensity (0 to 1).
        upper_lower_balance: -100 to 100. <0 weights upper lip, >0 weights lower lip.
        
    Returns:
        Deformed image as a numpy array.
    """
    if volume <= 0 or intensity <= 0:
        return image.copy()
        
    h, w = image.shape[:2]
    outer_pts = lip_pts['outer_lips']
    inner_pts = lip_pts['inner_lips']
    
    # Define a bounding box with padding around the lips
    x_min, y_min = np.min(outer_pts, axis=0) - 50
    x_max, y_max = np.max(outer_pts, axis=0) + 50
    x_min, y_min = max(x_min, 0), max(y_min, 0)
    x_max, y_max = min(x_max, w), min(y_max, h)
    
    # Calculate lip center based on outer contour
    center_x = np.mean(outer_pts[:, 0])
    center_y = np.mean(outer_pts[:, 1])
    
    # Anchors: 
    # 1. Bounding box edges (so the whole face doesn't warp)
    # 2. Inner lip points (so teeth and mouth opening remain rigid)
    anchors_bbox = np.array([
        [x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max],
        [center_x, y_min], [center_x, y_max], [x_min, center_y], [x_max, center_y]
    ])
    anchors = np.vstack([anchors_bbox, inner_pts])
    
    src_pts = np.vstack([outer_pts, anchors])
    dst_pts = np.copy(src_pts).astype(np.float64)
    
    # Max displacement in pixels
    max_disp = volume * intensity * 4.0 
    
    # Normalize balance from [-100, 100] to [0, 2] weight multipliers
    upper_weight = 1.0 + (upper_lower_balance / -100.0) if upper_lower_balance < 0 else 1.0 - (upper_lower_balance / 100.0)
    lower_weight = 1.0 + (upper_lower_balance / 100.0) if upper_lower_balance > 0 else 1.0 - (upper_lower_balance / -100.0)
    
    # Displace ONLY the outer lip points
    for i in range(len(outer_pts)):
        px, py = dst_pts[i]
        
        weight = upper_weight if py < center_y else lower_weight
        
        dx = px - center_x
        dy = py - center_y
        dist = np.sqrt(dx**2 + dy**2) + 1e-6
        
        # Pushing outward
        dst_pts[i, 0] += (dx / dist) * max_disp * weight
        dst_pts[i, 1] += (dy / dist) * max_disp * weight
        
    grid_x, grid_y = np.meshgrid(np.arange(x_min, x_max), np.arange(y_min, y_max))
    
    rbf_x = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 0], function='thin_plate')
    rbf_y = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 1], function='thin_plate')
    
    map_x = rbf_x(grid_x, grid_y).astype(np.float32)
    map_y = rbf_y(grid_x, grid_y).astype(np.float32)
    
    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    result = image.copy()
    result[y_min:y_max, x_min:x_max] = warped_roi
    
    return result
