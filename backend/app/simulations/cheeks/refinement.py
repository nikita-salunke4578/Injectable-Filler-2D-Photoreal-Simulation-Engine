"""
Photometric refinement (classical 2D, not a 3D renderer).

1. Shading: the added volume is a smooth height bump. Its gradient dotted with
   a light direction (estimated from the face itself) gives lit-side / shade-side
   modulation of LAB lightness. Convex crests (curvature of the bump) catch a
   soft highlight and the concave rim gets a faint shadow, so the effect is
   zero-mean and never turns into a flat brightening wash.
2. Shadow softening: filler fills hollows, so locally dark pixels (infraorbital
   hollow edge, submalar shadow, upper nasolabial fold) are pulled toward the
   local mean lightness, in proportion to the added volume.
   CK3 is a concavity FILL: it contributes no crest highlight and no directional
   shading (that would read as a new cheekbone); it only softens the hollow's
   shadow, with a stronger gain than the projection modes. CK2 additionally
   softens the under-eye -> cheek shadow edge (``transition``).
3. Texture: remapping magnifies skin and softens pores. The local high-frequency
   energy the original skin had at the source position is measured and exactly
   that much detail is restored (energy-matched, never over-sharpened).
4. Crispness: the crest highlight is scaled by the tissue response (firm skin =
   crisper definition, lax skin = softer).
"""
from __future__ import annotations

import cv2
import numpy as np

from .landmarks import CheekLandmarks


def estimate_light_dir(image: np.ndarray, lm: CheekLandmarks) -> np.ndarray:
    """Unit 2D vector (image coords) pointing TOWARD the light. Defaults to top-left-ish."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
    r = int(0.12 * lm.scale)

    def patch(c):
        x, y = int(c[0]), int(c[1])
        h, w = lab.shape
        return float(lab[max(0, y - r):min(h, y + r), max(0, x - r):min(w, x + r)].mean())

    l_left = patch(lm.left.zones["ck2"].center)
    l_right = patch(lm.right.zones["ck2"].center)
    lx = (l_right - l_left) / max(l_left + l_right, 1.0)          # >0: lit from image-right
    sx = float(np.clip(lx * 6.0, -0.9, 0.9))
    sy = -0.55                                                      # assume overhead-ish light
    v = np.array([sx, sy], np.float32)
    return v / max(np.linalg.norm(v), 1e-6)


def refine_cheek_region(
    deformed: np.ndarray,
    original: np.ndarray,
    mask: np.ndarray,
    lm: CheekLandmarks,
    dx: np.ndarray,
    dy: np.ndarray,
    height: np.ndarray,
    *,
    fill: np.ndarray | None = None,
    transition: np.ndarray | None = None,
    shading_gain: float = 1.0,
    crispness: float = 1.0,
) -> np.ndarray:
    h, w = deformed.shape[:2]
    a = (mask.astype(np.float32) / 255.0)
    s = lm.scale

    # ---- shading from height bump --------------------------------------
    hs = cv2.GaussianBlur(height, (0, 0), max(2.0, 0.04 * s))
    hx = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    hy = cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    light = estimate_light_dir(original, lm)
    shade = -(hx * light[0] + hy * light[1])                       # >0: facing the light

    # curvature of a wider-smoothed bump: convex crest > 0, concave rim < 0 (zero-mean overall)
    sig_c = max(3.0, 0.09 * s)
    hw_ = cv2.GaussianBlur(height, (0, 0), sig_c)
    curv = -(cv2.Laplacian(hw_, cv2.CV_32F, ksize=3))             # = -lap : positive on crests
    curv_n = curv * (sig_c ** 2) / max(0.05 * s, 1e-6)             # ~ +-1 for a typical bolus
    crest = np.clip(curv_n, 0.0, 1.5)
    rim = np.clip(-curv_n, 0.0, 1.0)

    lab = cv2.cvtColor(deformed.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    L = lab[..., 0]                                                 # 0..100
    dL = shading_gain * (60.0 * shade * 0.35 + 2.4 * crispness * crest - 1.0 * rim)
    dL = np.clip(dL, -4.0, 4.0)

    # ---- shadow softening: lift locally dark skin (hollows / folds) --------
    # Shadows are measured on a lightly smoothed lightness so pore-scale texture is NOT treated as shadow (lifting
    # every darker pixel would act as a local-contrast compressor and flatten the skin).
    L_s = cv2.GaussianBlur(L, (0, 0), max(2.0, 0.035 * s))
    L_bg = cv2.GaussianBlur(L, (0, 0), max(4.0, 0.22 * s))
    deficit = np.clip(L_bg - L_s, 0.0, 12.0)
    presence = np.clip(cv2.GaussianBlur(height, (0, 0), max(3.0, 0.10 * s)) / (0.03 * s), 0.0, 1.0)
    dL = dL + shading_gain * 0.35 * deficit * presence
    soft = None
    if fill is not None:
        soft = fill
    if transition is not None:
        soft = 0.6 * transition if soft is None else soft + 0.6 * transition
    if soft is not None:                                           # hollow / under-eye shadow removal
        presence_f = np.clip(cv2.GaussianBlur(soft, (0, 0), max(2.0, 0.06 * s)), 0.0, 1.0)
        # the hollow is a broad shadow, so compare with a WIDER face-only local mean (the background must not
        # count as "bright skin"): normalised convolution inside the face outline.
        face = np.zeros((h, w), np.float32)
        cv2.fillConvexPoly(face, cv2.convexHull(np.round(lm.oval).astype(np.int32)), 1.0)
        sg_f = max(5.0, 0.30 * s)
        L_ref = cv2.GaussianBlur(L * face, (0, 0), sg_f) / np.maximum(cv2.GaussianBlur(face, (0, 0), sg_f), 1e-3)
        deficit_f = np.clip(L_ref - L_s, 0.0, 18.0)
        dL = dL + shading_gain * np.minimum(0.70 * deficit_f * presence_f, 10.0)

    lab[..., 0] = np.clip(L + dL * a, 0, 100)
    relit = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR) * 255.0

    # ---- texture restoration where skin was magnified -------------------
    # Energy-matched: the warp low-passes skin where it magnifies. Measure the local high-frequency energy the ORIGINAL
    # skin had at the source position, and add back exactly the missing detail (never more than was there).
    def _gray(im):
        return cv2.cvtColor(np.clip(im, 0, 255).astype(np.float32), cv2.COLOR_BGR2GRAY)

    def _hf_energy(g):
        hf = g - cv2.GaussianBlur(g, (0, 0), 1.3)
        return cv2.GaussianBlur(hf * hf, (0, 0), max(3.0, 0.05 * s))

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e_target = cv2.remap(_hf_energy(_gray(original.astype(np.float32))), xx - dx, yy - dy, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT_101)
    e_now = _hf_energy(_gray(relit))
    gain = np.clip(np.sqrt(e_target / np.maximum(e_now, 1e-3)), 1.0, 1.8)
    gain = cv2.GaussianBlur(gain, (0, 0), 2.0)
    blur = cv2.GaussianBlur(relit, (0, 0), 1.3)
    relit = relit + ((gain - 1.0) * a)[..., None] * (relit - blur)

    # Outside the photometric mask keep the WARPED skin wherever it was displaced (blending with the un-warped original
    # would superimpose two misaligned copies of the same texture = ghosting / texture cancellation in the feather).
    # Where the displacement is ~0 the original is used, so untouched pixels stay bit-identical.
    wd = np.clip(np.hypot(dx, dy) / 0.05, 0.0, 1.0)
    wd = (wd * wd * (3 - 2 * wd))[..., None]
    base = original.astype(np.float32) * (1 - wd) + deformed.astype(np.float32) * wd
    out = relit * a[..., None] + base * (1 - a[..., None])
    return np.clip(out, 0, 255).astype(np.uint8)