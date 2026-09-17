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
    philtrum_cols = lip_pts.get('philtrum_columns', np.array([]))
    
    all_pts = np.vstack([outer_pts, inner_pts])
    if len(nose_base) > 0:
        all_pts = np.vstack([all_pts, nose_base])
        
    x_min, y_min = np.min(all_pts, axis=0) - 80
    x_max, y_max = np.max(all_pts, axis=0) + 80
    x_min, y_min = max(int(x_min), 0), max(int(y_min), 0)
    x_max, y_max = min(int(x_max), w), min(int(y_max), h)
    
    roi_w = x_max - x_min
    roi_h = y_max - y_min
    if roi_w < 10 or roi_h < 10:
        return image.copy(), mask.copy()
    
    center_x = np.mean(outer_pts[:, 0])
    center_y = np.mean(outer_pts[:, 1])
    
    # Separate inner lip points
    lower_inner = np.array([p for p in inner_pts if p[1] > center_y])
    upper_inner = np.array([p for p in inner_pts if p[1] <= center_y])
    
    # Build anchor points on the bounding box (these MUST NOT move)
    anchors_bbox = np.array([
        [x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max],
        [center_x, y_min], [center_x, y_max], [x_min, center_y], [x_max, center_y]
    ])
    
    anchors = anchors_bbox
    if len(nose_base) > 0:
        anchors = np.vstack([anchors, nose_base])
    if len(lower_inner) > 0:
        anchors = np.vstack([anchors, lower_inner])
    
    # ── Dense anchor row between nose and lips ("freeze zone") ─────
    # This prevents the TPS warp from bleeding upward into the nose.
    # We create a row of fixed points just above the upper lip boundary
    # that the RBF must interpolate through with zero displacement.
    upper_lip_y = np.min(outer_pts[:, 1])  # topmost lip landmark
    nose_y = np.min(nose_base[:, 1]) if len(nose_base) > 0 else upper_lip_y - 30
    
    # Place anchors at 1/3 and 2/3 of the gap between nose and lip top
    freeze_y1 = nose_y + (upper_lip_y - nose_y) * 0.25
    freeze_y2 = nose_y + (upper_lip_y - nose_y) * 0.5
    freeze_y0 = nose_y  # Right at the nose base line
    
    lip_left = np.min(outer_pts[:, 0])
    lip_right = np.max(outer_pts[:, 0])
    n_freeze = 10  # Number of anchor points per row
    
    for fy in [freeze_y0, freeze_y1, freeze_y2]:
        freeze_xs = np.linspace(lip_left - 20, lip_right + 20, n_freeze)
        freeze_row = np.column_stack([freeze_xs, np.full(n_freeze, fy)])
        anchors = np.vstack([anchors, freeze_row])
        
    src_pts = np.vstack([outer_pts, upper_inner, anchors])
    dst_pts = np.copy(src_pts).astype(np.float64)
    
    # Normalise slider values from 0-100 to 0-1
    s_phil = philtral_shortening / 100.0
    s_verm = vermilion_show / 100.0
    s_cupid = cupids_bow / 100.0
    s_dental = dental_show / 100.0
    s_column = philtral_column / 100.0
    
    # Maximum pixel displacements
    max_upward = 45.0
    max_outward = 30.0
    max_cupid = 20.0
    max_dental = 25.0
    max_column_spread = 12.0
    
    n_outer = len(outer_pts)
    n_upper_inner = len(upper_inner)
    
    # ── 1. Vermilion Show (expand lips outward from center) ─────────
    if s_verm > 0:
        for i in range(n_outer):
            px, py = dst_pts[i]
            dx = px - center_x
            dy = py - center_y
            dist = np.sqrt(dx**2 + dy**2) + 1e-6
            dst_pts[i, 0] += (dx / dist) * (s_verm * max_outward)
            dst_pts[i, 1] += (dy / dist) * (s_verm * max_outward)
            
    # ── 2. Philtral Shortening (move upper lip points upward) ──────
    if s_phil > 0:
        max_width = (np.max(outer_pts[:, 0]) - np.min(outer_pts[:, 0])) / 2.0
        if max_width < 1:
            max_width = 1
        for i in range(n_outer):
            px, py = dst_pts[i]
            if py < center_y:
                dist_from_center = abs(px - center_x)
                falloff = max(0, 1.0 - (dist_from_center / max_width))
                dst_pts[i, 1] -= (s_phil * max_upward) * falloff
                
    # ── 3. Cupid's Bow (use nearest-point matching, not exact) ─────
    if s_cupid > 0 and len(cupids_bow_pts) == 2:
        # Find the outer_pts indices closest to each cupid's bow peak
        for cb in cupids_bow_pts:
            dists_to_cb = np.sqrt(np.sum((outer_pts - cb)**2, axis=1))
            closest_idx = np.argmin(dists_to_cb)
            
            # Also affect nearby points for smoother deformation
            for i in range(n_outer):
                d = dists_to_cb[i]
                # Gaussian falloff from the cupid's bow point
                sigma = 15.0  # pixels
                weight = np.exp(-(d**2) / (2 * sigma**2))
                if weight < 0.05:
                    continue
                    
                px = dst_pts[i, 0]
                dir_x = 1.0 if px < center_x else -1.0
                dst_pts[i, 0] += dir_x * (s_cupid * max_cupid * 0.5) * weight
                dst_pts[i, 1] -= (s_cupid * max_cupid) * weight

    # ── 4. Philtral Column Enhancement ─────────────────────────────
    if s_column > 0 and len(philtrum_cols) > 0:
        # Add philtral column points as additional control points
        # They should spread slightly outward to create visible ridges
        col_src = philtrum_cols.copy().astype(np.float64)
        col_dst = col_src.copy()
        
        for i in range(len(col_dst)):
            px = col_dst[i, 0]
            dir_x = 1.0 if px < center_x else -1.0
            # Slight outward push to accentuate the columns
            col_dst[i, 0] += dir_x * (s_column * max_column_spread)
        
        src_pts = np.vstack([src_pts, col_src])
        dst_pts = np.vstack([dst_pts, col_dst])
    
    # ── 5. Dental Show (lift upper inner lip to reveal teeth) ──────
    if s_dental > 0 and n_upper_inner > 0:
        idx_offset = n_outer
        upper_inner_x = upper_inner[:, 0]
        max_inner_width = (np.max(upper_inner_x) - np.min(upper_inner_x)) / 2.0 + 1e-6
        for i in range(n_upper_inner):
            px = dst_pts[idx_offset + i, 0]
            dist_from_center = abs(px - center_x)
            falloff = max(0, 1.0 - (dist_from_center / max_inner_width))
            dst_pts[idx_offset + i, 1] -= (s_dental * max_dental) * falloff

    # ── Build RBF warp mapping ─────────────────────────────────────
    
    # Deduplicate to prevent singular matrix
    _, unique_indices = np.unique(src_pts, axis=0, return_index=True)
    src_pts = src_pts[unique_indices]
    dst_pts = dst_pts[unique_indices]
    
    # Ensure we have enough unique points
    if len(src_pts) < 4:
        return image.copy(), mask.copy()

    # Build grid in ROI-LOCAL coordinates for cv2.remap
    grid_x_local, grid_y_local = np.meshgrid(
        np.arange(roi_w, dtype=np.float64), 
        np.arange(roi_h, dtype=np.float64)
    )
    # Convert to absolute coordinates for RBF evaluation
    grid_x_abs = grid_x_local + x_min
    grid_y_abs = grid_y_local + y_min
    
    # RBF: maps from destination coords to source coords
    # "Where in the source image does each destination pixel come from?"
    rbf_x = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 0], function='thin_plate')
    rbf_y = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 1], function='thin_plate')
    
    # Evaluate: for each pixel in the output, find where to sample from the source
    src_x_abs = rbf_x(grid_x_abs, grid_y_abs)
    src_y_abs = rbf_y(grid_x_abs, grid_y_abs)
    
    # Convert source coordinates to ROI-local for cv2.remap
    map_x = (src_x_abs - x_min).astype(np.float32)
    map_y = (src_y_abs - y_min).astype(np.float32)
    
    # Apply remap to ROI
    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    result = image.copy()
    result[y_min:y_max, x_min:x_max] = warped_roi
    
    # Warp the mask as well
    mask_roi = mask[y_min:y_max, x_min:x_max]
    warped_mask_roi = cv2.remap(mask_roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    
    result_mask = mask.copy()
    result_mask[y_min:y_max, x_min:x_max] = warped_mask_roi
    
    return result, result_mask
