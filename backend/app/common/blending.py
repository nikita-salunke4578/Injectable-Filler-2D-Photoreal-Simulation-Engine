import cv2
import numpy as np


def poisson_blend(
    foreground: np.ndarray,
    background: np.ndarray,
    mask: np.ndarray,
    *,
    split_bilateral: bool = False,
) -> np.ndarray:
    """
    Seamlessly blends the foreground into the background using Poisson image editing.
    The mask defines the region of the foreground to blend.

    Args:
        foreground: BGR image that contains the modified region.
        background: BGR image to blend into.
        mask: uint8 mask (0-255) defining the blend region.
        split_bilateral: If True, detects two separate connected components in the mask
            and applies seamlessClone independently for each half. Eliminates the
            color-shift artifact that occurs near the ears when a single center point
            is used for a bilateral cheek mask.
    """
    # Ensure mask is 8-bit single channel
    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    mask_u8 = mask.astype(np.uint8)

    y_indices, x_indices = np.where(mask_u8 > 0)
    if len(x_indices) == 0 or len(y_indices) == 0:
        return background.copy()

    if split_bilateral:
        return _split_poisson_blend(foreground, background, mask_u8)

    # Single-region fallback
    center_x = int(np.mean(x_indices))
    center_y = int(np.mean(y_indices))
    try:
        return cv2.seamlessClone(
            foreground, background, mask_u8, (center_x, center_y), cv2.NORMAL_CLONE
        )
    except Exception as e:
        print(f"Poisson blend failed: {e}. Falling back to alpha blend.")
        return _alpha_blend(foreground, background, mask_u8)


def _split_poisson_blend(
    foreground: np.ndarray,
    background: np.ndarray,
    mask_u8: np.ndarray,
) -> np.ndarray:
    """
    Applies seamlessClone independently to each connected component of the mask.

    For bilateral cheek simulations, this eliminates the ear-adjacent color-shift
    artifact that results from Poisson solving across a wide bilateral region with
    a single center point. Each cheek is blended with its own localized center so
    the solver stays within the correct skin color context.
    """
    # Threshold to binary for connected-component analysis
    _, binary = cv2.threshold(mask_u8, 10, 255, cv2.THRESH_BINARY)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # If only background (label 0) or a single component, fall back to standard blend
    if n_labels <= 1:
        y_indices, x_indices = np.where(mask_u8 > 0)
        center_x = int(np.mean(x_indices))
        center_y = int(np.mean(y_indices))
        try:
            return cv2.seamlessClone(foreground, background, mask_u8, (center_x, center_y), cv2.NORMAL_CLONE)
        except Exception as e:
            print(f"Single-region blend failed: {e}. Alpha fallback.")
            return _alpha_blend(foreground, background, mask_u8)

    result = background.copy()

    for label_id in range(1, n_labels):
        # Build isolated mask for this component
        component_mask = np.zeros_like(mask_u8)
        component_mask[labels == label_id] = mask_u8[labels == label_id]

        comp_y, comp_x = np.where(component_mask > 0)
        if len(comp_x) < 4:
            continue

        # Use the centroid from connectedComponentsWithStats for accuracy
        cx = int(centroids[label_id][0])
        cy = int(centroids[label_id][1])

        # Clamp center to valid interior (seamlessClone requires center inside non-zero mask)
        h, w = mask_u8.shape
        cx = int(np.clip(cx, 1, w - 2))
        cy = int(np.clip(cy, 1, h - 2))

        try:
            result = cv2.seamlessClone(
                foreground, result, component_mask, (cx, cy), cv2.NORMAL_CLONE
            )
        except Exception as e:
            print(f"Component {label_id} seamlessClone failed: {e}. Alpha fallback for this component.")
            result = _alpha_blend(foreground, result, component_mask)

    return result


def _alpha_blend(
    foreground: np.ndarray,
    background: np.ndarray,
    mask_u8: np.ndarray,
) -> np.ndarray:
    """Simple alpha blend as fallback when Poisson fails."""
    mask_norm = mask_u8.astype(np.float32) / 255.0
    if len(mask_norm.shape) == 2:
        mask_norm = np.expand_dims(mask_norm, axis=-1)
    return (foreground.astype(np.float32) * mask_norm + background.astype(np.float32) * (1.0 - mask_norm)).astype(np.uint8)
