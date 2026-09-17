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
    
    # ── ROI Bounding Box ───────────────────────────────────────────
    # Keep large enough for smooth RBF but the MASK will restrict visibility
    all_pts = np.vstack([outer_pts, inner_pts])
    if len(nose_base) > 0:
        all_pts = np.vstack([all_pts, nose_base])
        
    x_min, y_min = np.min(all_pts, axis=0) - 60
    x_max, y_max = np.max(all_pts, axis=0) + 60
    x_min, y_min = max(int(x_min), 0), max(int(y_min), 0)
    x_max, y_max = min(int(x_max), w), min(int(y_max), h)
    
    roi_w = x_max - x_min
    roi_h = y_max - y_min
    if roi_w < 10 or roi_h < 10:
        return image.copy(), mask.copy()
    
    # Lip geometry references
    center_x = np.mean(outer_pts[:, 0])
    center_y = np.mean(outer_pts[:, 1])
    lip_top_y = np.min(outer_pts[:, 1])
    lip_bot_y = np.max(outer_pts[:, 1])
    lip_left_x = np.min(outer_pts[:, 0])
    lip_right_x = np.max(outer_pts[:, 0])
    lip_half_w = (lip_right_x - lip_left_x) / 2.0 + 1e-6
    
    # Separate inner lip points
    lower_inner = np.array([p for p in inner_pts if p[1] > center_y])
    upper_inner = np.array([p for p in inner_pts if p[1] <= center_y])
    
    # ── Anchor points (MUST NOT move) ──────────────────────────────
    # Bounding box corners + midpoints
    anchors_bbox = np.array([
        [x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max],
        [center_x, y_min], [center_x, y_max], [x_min, center_y], [x_max, center_y]
    ])
    
    anchors = anchors_bbox.copy()
    
    # Pin nose base — these absolutely must not move
    if len(nose_base) > 0:
        anchors = np.vstack([anchors, nose_base])
    
    # Pin lower inner lip (mouth opening line)
    if len(lower_inner) > 0:
        anchors = np.vstack([anchors, lower_inner])
    
    # ── Freeze zone ABOVE lips (protect nose, mustache) ────────────
    # Dense rows of fixed points between nose base and upper lip
    nose_y = np.min(nose_base[:, 1]) if len(nose_base) > 0 else lip_top_y - 30
    n_freeze = 12
    freeze_xs = np.linspace(lip_left_x - 30, lip_right_x + 30, n_freeze)
    
    # Three rows: at nose base, 1/3 down, 2/3 down
    for frac in [0.0, 0.33, 0.66]:
        fy = nose_y + (lip_top_y - nose_y) * frac
        freeze_row = np.column_stack([freeze_xs, np.full(n_freeze, fy)])
        anchors = np.vstack([anchors, freeze_row])
    
    # ── Freeze zone BELOW lips (protect chin, beard) ───────────────
    chin_y = lip_bot_y + 40  # ~40px below lower lip
    for frac in [0.33, 0.66, 1.0]:
        fy = lip_bot_y + (chin_y - lip_bot_y) * frac
        freeze_row = np.column_stack([freeze_xs, np.full(n_freeze, fy)])
        anchors = np.vstack([anchors, freeze_row])
    
    # ── Freeze zone on SIDES (protect cheeks, nasolabial folds) ────
    side_ys = np.linspace(lip_top_y - 10, lip_bot_y + 10, 6)
    for sy in side_ys:
        anchors = np.vstack([anchors, [[lip_left_x - 35, sy], [lip_right_x + 35, sy]]])
    
    # ── Build src/dst control point arrays ─────────────────────────
    src_pts = np.vstack([outer_pts, upper_inner, anchors])
    dst_pts = np.copy(src_pts).astype(np.float64)
    
    # Normalise slider values from 0-100 to 0-1
    s_phil = philtral_shortening / 100.0
    s_verm = vermilion_show / 100.0
    s_cupid = cupids_bow / 100.0
    s_dental = dental_show / 100.0
    s_column = philtral_column / 100.0
    
    # Conservative pixel displacements for natural results.
    # Real filler injections produce subtle changes (2-8mm = ~6-20px at typical resolution).
    max_upward = 12.0     # philtral shortening (was 45 — way too much)
    max_outward = 10.0    # vermilion expansion (was 30)
    max_cupid = 8.0       # cupid's bow lift (was 20)
    max_dental = 8.0      # dental show (was 25)
    max_column_spread = 5.0  # philtral column (was 12)
    
    n_outer = len(outer_pts)
    n_upper_inner = len(upper_inner)
    
    # ── 1. Vermilion Show ──────────────────────────────────────────
    # Upper lip points move UP only. Lower lip points move DOWN only.
    # NO lateral expansion — this keeps the lip width natural and
    # prevents pushing into nasolabial folds or mustache area.
    if s_verm > 0:
        for i in range(n_outer):
            py = dst_pts[i, 1]
            if py < center_y:
                # Upper lip — move upward only, stronger at center
                dist_from_center_x = abs(dst_pts[i, 0] - center_x)
                falloff = max(0, 1.0 - (dist_from_center_x / lip_half_w) ** 2)
                dst_pts[i, 1] -= s_verm * max_outward * falloff
            else:
                # Lower lip — move downward only, stronger at center
                dist_from_center_x = abs(dst_pts[i, 0] - center_x)
                falloff = max(0, 1.0 - (dist_from_center_x / lip_half_w) ** 2)
                dst_pts[i, 1] += s_verm * max_outward * falloff
            
    # ── 2. Philtral Shortening ─────────────────────────────────────
    # Only moves upper lip points upward with center-weighted falloff.
    if s_phil > 0:
        for i in range(n_outer):
            py = dst_pts[i, 1]
            if py < center_y:
                dist_from_center_x = abs(dst_pts[i, 0] - center_x)
                falloff = max(0, 1.0 - (dist_from_center_x / lip_half_w))
                dst_pts[i, 1] -= s_phil * max_upward * falloff
                
    # ── 3. Cupid's Bow ─────────────────────────────────────────────
    # Lifts the two cupid's bow peaks slightly with Gaussian falloff
    if s_cupid > 0 and len(cupids_bow_pts) == 2:
        for cb in cupids_bow_pts:
            dists_to_cb = np.sqrt(np.sum((outer_pts - cb)**2, axis=1))
            
            for i in range(n_outer):
                d = dists_to_cb[i]
                sigma = 12.0
                weight = np.exp(-(d**2) / (2 * sigma**2))
                if weight < 0.05:
                    continue
                # Mostly vertical lift, very slight horizontal separation
                px = dst_pts[i, 0]
                dir_x = 1.0 if px < center_x else -1.0
                dst_pts[i, 0] += dir_x * (s_cupid * max_cupid * 0.15) * weight
                dst_pts[i, 1] -= (s_cupid * max_cupid) * weight

    # ── 4. Philtral Column Enhancement ─────────────────────────────
    if s_column > 0 and len(philtrum_cols) > 0:
        col_src = philtrum_cols.copy().astype(np.float64)
        col_dst = col_src.copy()
        
        for i in range(len(col_dst)):
            px = col_dst[i, 0]
            dir_x = 1.0 if px < center_x else -1.0
            col_dst[i, 0] += dir_x * (s_column * max_column_spread)
        
        src_pts = np.vstack([src_pts, col_src])
        dst_pts = np.vstack([dst_pts, col_dst])
    
    # ── 5. Dental Show ─────────────────────────────────────────────
    if s_dental > 0 and n_upper_inner > 0:
        idx_offset = n_outer
        upper_inner_x = upper_inner[:, 0]
        max_inner_width = (np.max(upper_inner_x) - np.min(upper_inner_x)) / 2.0 + 1e-6
        for i in range(n_upper_inner):
            px = dst_pts[idx_offset + i, 0]
            dist_from_center = abs(px - center_x)
            falloff = max(0, 1.0 - (dist_from_center / max_inner_width))
            dst_pts[idx_offset + i, 1] -= s_dental * max_dental * falloff

    # ── Build RBF warp mapping ─────────────────────────────────────
    
    # Deduplicate to prevent singular matrix
    _, unique_indices = np.unique(src_pts, axis=0, return_index=True)
    src_pts = src_pts[unique_indices]
    dst_pts = dst_pts[unique_indices]
    
    if len(src_pts) < 4:
        return image.copy(), mask.copy()

    # Build grid in ROI-LOCAL coordinates for cv2.remap
    grid_x_local, grid_y_local = np.meshgrid(
        np.arange(roi_w, dtype=np.float64), 
        np.arange(roi_h, dtype=np.float64)
    )
    grid_x_abs = grid_x_local + x_min
    grid_y_abs = grid_y_local + y_min
    
    # RBF: maps from destination coords to source coords
    rbf_x = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 0], function='thin_plate')
    rbf_y = Rbf(dst_pts[:, 0], dst_pts[:, 1], src_pts[:, 1], function='thin_plate')
    
    src_x_abs = rbf_x(grid_x_abs, grid_y_abs)
    src_y_abs = rbf_y(grid_x_abs, grid_y_abs)
    
    # Convert to ROI-local for cv2.remap
    map_x = (src_x_abs - x_min).astype(np.float32)
    map_y = (src_y_abs - y_min).astype(np.float32)
    
    # Apply remap to ROI only
    roi = image[y_min:y_max, x_min:x_max]
    warped_roi = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    result = image.copy()
    result[y_min:y_max, x_min:x_max] = warped_roi
    
    # Warp mask in same way
    mask_roi = mask[y_min:y_max, x_min:x_max]
    warped_mask_roi = cv2.remap(mask_roi, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    
    result_mask = mask.copy()
    result_mask[y_min:y_max, x_min:x_max] = warped_mask_roi
    
    return result, result_mask
