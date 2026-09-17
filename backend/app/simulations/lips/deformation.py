import cv2
import numpy as np
from scipy.interpolate import Rbf

def apply_lip_deformation(
    image: np.ndarray,
    mask: np.ndarray,
    lip_pts: dict[str, np.ndarray],
    philtral_shortening: float,
    vermilion_show: float,
    cupids_bow: float,
    philtral_column: float,
    dental_show: float
) -> tuple[np.ndarray, np.ndarray]:
    h, w = image.shape[:2]
    outer_pts = lip_pts['outer_lips']
    inner_pts = lip_pts['inner_lips']
    nose_base = lip_pts.get('nose_base', np.array([]))
    cupids_bow_pts = lip_pts.get('cupids_bow', np.array([]))
    corners = lip_pts.get('corners', np.array([]))
    
    all_pts = np.vstack([outer_pts, inner_pts])
    if len(nose_base) > 0:
        all_pts = np.vstack([all_pts, nose_base])
        
    x_min, y_min = np.min(all_pts, axis=0) - 80
    x_max, y_max = np.max(all_pts, axis=0) + 80
    x_min, y_min = max(x_min, 0), max(y_min, 0)
    x_max, y_max = min(x_max, w), min(y_max, h)
    
    center_x = np.mean(outer_pts[:, 0])
    center_y = np.mean(outer_pts[:, 1])
    
    anchors_bbox = np.array([
        [x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max],
        [center_x, y_min], [center_x, y_max], [x_min, center_y], [x_max, center_y]
    ])
    
    lower_inner = np.array([p for p in inner_pts if p[1] > center_y])
    upper_inner = np.array([p for p in inner_pts if p[1] <= center_y])
    
    anchors = anchors_bbox
    if len(nose_base) > 0:
        anchors = np.vstack([anchors, nose_base])
    if len(lower_inner) > 0:
        anchors = np.vstack([anchors, lower_inner])
        
    src_pts = np.vstack([outer_pts, upper_inner, anchors])
    dst_pts = np.copy(src_pts).astype(np.float64)
    
    s_phil = philtral_shortening / 100.0
    s_verm = vermilion_show / 100.0
    s_cupid = cupids_bow / 100.0
    s_dental = dental_show / 100.0
    s_column = philtral_column / 100.0
    
    max_upward = 45.0
    max_outward = 30.0
    max_cupid = 20.0
    max_dental = 25.0
    
    if s_verm > 0:
        for i in range(len(outer_pts)):
            px, py = dst_pts[i]
            dx = px - center_x
            dy = py - center_y
            dist = np.sqrt(dx**2 + dy**2) + 1e-6
            dst_pts[i, 0] += (dx / dist) * (s_verm * max_outward)
            dst_pts[i, 1] += (dy / dist) * (s_verm * max_outward)
            
    if s_phil > 0:
        for i in range(len(outer_pts)):
            px, py = dst_pts[i]
            if py < center_y:
                dist_from_center = abs(px - center_x)
                max_width = (np.max(outer_pts[:, 0]) - np.min(outer_pts[:, 0])) / 2.0
                falloff = max(0, 1.0 - (dist_from_center / max_width))
                dst_pts[i, 1] -= (s_phil * max_upward) * falloff
                
    if s_cupid > 0 and len(cupids_bow_pts) == 2:
        for i in range(len(outer_pts)):
            px, py = dst_pts[i]
            for cb in cupids_bow_pts:
                if abs(px - cb[0]) < 2 and abs(py - cb[1]) < 2:
                    dir_x = 1 if px < center_x else -1
                    dst_pts[i, 0] += dir_x * (s_cupid * max_cupid * 0.5)
                    dst_pts[i, 1] -= (s_cupid * max_cupid)
                    
    if s_dental > 0:
        idx_offset = len(outer_pts)
        for i in range(len(upper_inner)):
            px, py = dst_pts[idx_offset + i]
            dist_from_center = abs(px - center_x)
            max_width = (np.max(upper_inner[:, 0]) - np.min(upper_inner[:, 0])) / 2.0 + 1e-6
            falloff = max(0, 1.0 - (dist_from_center / max_width))
            dst_pts[idx_offset + i, 1] -= (s_dental * max_dental) * falloff

    grid_x, grid_y = np.meshgrid(np.arange(x_min, x_max), np.arange(y_min, y_max))
    
    # Deduplicate src_pts to prevent Rbf from failing with singular matrix
    # The same point (e.g., mouth corner) might exist in both outer_pts and inner_pts
    _, unique_indices = np.unique(src_pts, axis=0, return_index=True)
    src_pts = src_pts[unique_indices]
    dst_pts = dst_pts[unique_indices]

    
    rbf_x = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 0], function='thin_plate')
    rbf_y = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 1], function='thin_plate')
    
    map_x = rbf_x(grid_x, grid_y).astype(np.float32)
    map_y = rbf_y(grid_x, grid_y).astype(np.float32)
    
    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    result = image.copy()
    result[y_min:y_max, x_min:x_max] = warped_roi
    
    mask_roi = mask[y_min:y_max, x_min:x_max]
    warped_mask_roi = cv2.remap(mask_roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    
    result_mask = mask.copy()
    result_mask[y_min:y_max, x_min:x_max] = warped_mask_roi
    
    return result, result_mask
