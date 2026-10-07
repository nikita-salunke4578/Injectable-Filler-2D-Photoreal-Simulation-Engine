"""
Geometric cheek deformation - three DIFFERENT, mode-specific displacement fields.

Backward mapping per pixel:  src(p) = p - d(p)   (so content moves by +d)

    d(p) = sum over zones  G_z(p) * gate_z(p) * medial(p) * half(p) * protect_z(p) *
                           amp_z * [ w_radial * r_z(p)  +  w_push * push_z ]

  r_z  = normalised radial offset in the zone's elliptical frame (dome / "forward" expansion;
         in a frontal photo anterior projection shows up as local magnification)
  push = a fixed unit direction (lateral, up, or toward the contour chord)

  CK1 ZYGOMATIC  w_push 0.85 (outward 0.90 + up 0.30), w_radial 0.15, gated OFF below the arch
                 -> widens/raises the upper-lateral contour, lower cheek untouched
  CK2 MALAR      w_radial 0.85, w_push 0.15 (up) -> pure forward dome, no net lateral drift;
                 ellipse leans to the infra-orbital rim, plus a photometric under-eye blend
  CK3 SUBMALAR   w_push 0.70 (outward normal of the zygoma->gonion chord) + w_radial 0.30,
                 gated OFF above the apex, amplitude capped by the MEASURED hollow depth
                 -> concavity correction, no upward lift, no new cheekbone

Shared safety: elliptical Gaussian falloff, mid-cheek safety line (medial canthus -> gonion),
per-side half-plane (unilateral work stays on its own cheek), frozen eyelids / tear trough /
lips / nose wing / glasses, nothing above the eye line, per-zone face-outline support (lateral
zones may move the silhouette a little, CK2 may not), and a fold check on the backward map
(min det(I - J) >= 0.35, else the whole field is scaled down).
"""
from __future__ import annotations

import cv2
import numpy as np

from .landmarks import CheekLandmarks, SideGeometry

# mL (per side, per zone) -> peak displacement as a fraction of inter-ocular distance.
# Sub-linear (power 0.8): the 2nd mL looks like less than 2x the 1st.
_MM_PER_ML = {"ck1": 0.070, "ck2": 0.075, "ck3": 0.055}
# per-mode mix of radial (forward dome) vs directional push. This is what makes the modes differ.
_MIX = {"ck1": dict(radial=0.15, push=0.85),
        "ck2": dict(radial=0.85, push=0.15),
        "ck3": dict(radial=0.30, push=0.70)}
# how much of the displacement survives AT the face outline. CK1/CK3 move the silhouette (zygomatic
# width, filled lower-cheek contour); CK2 is anterior projection and must not drag skin over the background.
_OUTLINE_FLOOR = {"ck1": 0.65, "ck2": 0.22, "ck3": 0.55}
ZONES = ("ck1", "ck2", "ck3")
MAX_VOLUME_ML = 3.0

# Skin elasticity semantics = the UI's "Skin Elasticity Scale" slider (0.8x .. 1.2x): it scales the kernel SPREAD radius.
# 0.8 = tight youthful skin  -> tighter, more localised, crisper contour
# 1.2 = mature lax skin      -> broader, softer deformation, less crisp projection


def elasticity_response(scale: float) -> dict:
    """Tissue response from the Skin Elasticity Scale (clipped to 0.8 .. 1.2).

    spread : multiplier on every zone's footprint = the slider value itself (kernel spread radius)
    peak   : peak-displacement multiplier (lax bolus is spread wider, so it also looks less projected)
    crisp  : multiplier on the crest highlight (definition of the projection)
    """
    e = float(np.clip(scale, 0.8, 1.2))
    return dict(spread=e, peak=1.0 - 0.6 * (e - 1.0), crisp=1.0 - 1.5 * (e - 1.0))


def zone_sigma(z, ml: float) -> float:
    """Larger boluses spread wider (also keeps the warp unfolded)."""
    return z.sigma * (1.0 + 0.15 * float(np.clip(ml, 0.0, MAX_VOLUME_ML)))


def side_half_weight(shape, lm: CheekLandmarks, side: str) -> np.ndarray:
    """0 at/after the facial midline, 1 well inside this side. Keeps unilateral work on its own cheek."""
    h, w = shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    mid = lm.pts[6]
    t = (xx - mid[0]) * lm.roll_u[0] + (yy - mid[1]) * lm.roll_u[1]      # + toward image-right
    t = -t if side == "left" else t
    r = np.clip((t - 0.08 * lm.scale) / (0.14 * lm.scale), 0.0, 1.0)
    return (r * r * (3 - 2 * r)).astype(np.float32)


def volume_to_px(ml: float, zone: str, scale: float, elasticity: float = 1.0) -> float:
    """Peak displacement (px) for a volume, before the tissue-response factor (see effective_amp)."""
    ml = float(np.clip(ml, 0.0, MAX_VOLUME_ML))
    raw = (ml ** 0.8) * _MM_PER_ML[zone] * scale
    cap = 0.16 * scale                      # soft ceiling: tissue can only bulge so far
    return cap * float(np.tanh(raw / cap))


def _poly_mask(shape, pts, dilate_px=0):
    m = np.zeros(shape, np.uint8)
    if pts is not None and len(pts) >= 3:
        cv2.fillConvexPoly(m, cv2.convexHull(np.round(pts).astype(np.int32)), 255)
    if dilate_px > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dilate_px + 1,) * 2)
        m = cv2.dilate(m, k)
    return m


def build_protect_maps(shape, lm: CheekLandmarks, glasses_mask=None) -> dict:
    """{zone: float32 [0,1]} - 1 = free to deform, 0 = frozen. Same frozen set for every zone,
    different face-outline support (see _OUTLINE_FLOOR)."""
    h, w = shape[:2]
    s = lm.scale
    frozen = np.zeros((h, w), np.uint8)

    for sg in (lm.left, lm.right):
        # eyelids + tear trough, extended downward under the lower lid
        eye = _poly_mask((h, w), sg.eye_pts, dilate_px=int(0.04 * s))
        trough = _poly_mask((h, w), np.vstack([sg.lower_lid, sg.lower_lid - sg.up * (0.10 * s)]), dilate_px=int(0.03 * s))
        frozen |= eye | trough
    frozen |= _poly_mask((h, w), lm.lips, dilate_px=int(0.10 * s))
    for side in ("left", "right"):
        frozen |= _poly_mask((h, w), lm.nose_wing[side], dilate_px=int(0.03 * s))
    if glasses_mask is not None:
        gm = glasses_mask if glasses_mask.ndim == 2 else glasses_mask[..., 0]
        frozen |= (gm > 127).astype(np.uint8) * 255

    sig = max(3.0, 0.05 * s)
    fz = cv2.GaussianBlur(frozen.astype(np.float32) / 255.0, (0, 0), sig)       # 0.5 on the (dilated) polygon edge
    protect = _smooth((0.6 - fz) / 0.6)                                           # exactly 0 for fz >= 0.6: frozen core

    # Nothing above the eye line (brows, lids, temples) may move: smooth ramp starting just below the eyes.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    eye_mid = 0.5 * (lm.pts[33] + lm.pts[263])
    t = (xx - eye_mid[0]) * lm.roll_v[0] + (yy - eye_mid[1]) * lm.roll_v[1]   # signed px below eye line
    protect = protect * _smooth((t - 0.06 * s) / (0.14 * s))

    # Face-support: displacement is damped to `floor` AT the outline (skin is never dragged far over hair /
    # background), rising to full strength ~0.10*scale inside it, fading to 0 just outside.
    face = _poly_mask((h, w), lm.oval)
    d_in = cv2.distanceTransform(face, cv2.DIST_L2, 3)
    d_out = cv2.distanceTransform(255 - face, cv2.DIST_L2, 3)
    t_in = _smooth(d_in / (0.10 * s))
    t_out = _smooth(d_out / (0.05 * s))
    out = {}
    for name in ZONES:
        floor = _OUTLINE_FLOOR[name]
        support = np.where(face > 0, floor + (1 - floor) * t_in, floor * (1 - t_out)).astype(np.float32)
        support = cv2.GaussianBlur(support, (0, 0), max(2.0, 0.02 * s))
        out[name] = (protect * support).astype(np.float32)
    return out


def build_protect_map(shape, lm: CheekLandmarks, glasses_mask=None) -> np.ndarray:
    """Conservative single map (the lowest outline floor). Kept for callers that want one array."""
    m = build_protect_maps(shape, lm, glasses_mask)
    return np.minimum.reduce(list(m.values()))


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def medial_weight(xx, yy, sg: SideGeometry, scale: float) -> np.ndarray:
    """1 lateral to the mid-cheek safety line, fading to 0 about 0.12*scale medial to it."""
    a, b = sg.medial_line
    ch = (b - a) / max(float(np.linalg.norm(b - a)), 1e-6)
    n = np.array([-ch[1], ch[0]], np.float32)
    if float(n @ sg.outward) < 0:
        n = -n
    d = (xx - a[0]) * n[0] + (yy - a[1]) * n[1]            # + = lateral of the line
    return _smooth((d + 0.12 * scale) / (0.20 * scale)).astype(np.float32)


def zone_gate(xx, yy, z) -> np.ndarray:
    """Smooth half-plane confinement of a zone (ck1: not below the arch, ck3: not above the apex)."""
    if z.gate is None:
        return 1.0
    gates = z.gate if isinstance(z.gate, list) else [z.gate]
    out = 1.0
    for n, ref, offset, width in gates:
        d = (xx - ref[0]) * n[0] + (yy - ref[1]) * n[1]
        out = out * _smooth((d + offset) / max(width, 1e-6))
    return out.astype(np.float32) if hasattr(out, "astype") else out


def zone_weight(xx, yy, z, ml: float, widen: float = 1.0):
    """Elliptical Gaussian footprint of a zone x its gate. Returns (g, na, nb, axis): weight and the
    normalised offsets along / across the zone axis (dimensionless, ~1 at one sigma)."""
    ax = z.axis if z.axis is not None else np.array([1.0, 0.0], np.float32)
    sb = zone_sigma(z, ml) * widen
    sa = sb * float(max(z.aspect, 1.0))
    rx, ry = xx - z.center[0], yy - z.center[1]
    a = rx * ax[0] + ry * ax[1]
    b = -rx * ax[1] + ry * ax[0]
    na, nb = a / sa, b / sb
    g = np.exp(-0.5 * (na * na + nb * nb)) * zone_gate(xx, yy, z)
    return g.astype(np.float32), na.astype(np.float32), nb.astype(np.float32), ax


def effective_amp(z, ml: float, scale: float, elasticity: float = 1.0) -> float:
    """Peak displacement (px). CK3 is a concavity correction, so it is bounded by how deep the hollow
    really is: with no measurable hollow only a small residual smoothing remains."""
    amp = volume_to_px(ml, z.name, scale) * elasticity_response(elasticity)["peak"]
    if z.name == "ck3":
        amp = min(amp, 0.35 * amp + 1.1 * float(z.hollow_px))
    return amp


def side_field(shape, sg: SideGeometry, lm: CheekLandmarks, volumes: dict[str, float],
               zone_protect: dict, elasticity: float = 1.0):
    """One side. Returns dict(dx, dy, height, fill, transition, peak_px).

    height      projection bump (ck1 + ck2) -> crest highlight / lit-shade-side shading
    fill        concavity-fill footprint (ck3) -> shadow softening ONLY (never a highlight)
    transition  ck2 under-eye -> cheek blend footprint (upper half) -> shadow softening
    """
    scale = lm.scale
    h, w = shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = np.zeros((h, w), np.float32)
    dy = np.zeros((h, w), np.float32)
    height = np.zeros((h, w), np.float32)
    fill = np.zeros((h, w), np.float32)
    transition = np.zeros((h, w), np.float32)
    peak_px = {}
    half = side_half_weight(shape, lm, sg.side) * medial_weight(xx, yy, sg, scale)
    for name, z in sg.zones.items():
        ml = volumes.get(name, 0.0)
        if ml <= 1e-4:
            peak_px[name] = 0.0
            continue
        amp = effective_amp(z, ml, scale, elasticity)
        peak_px[name] = amp
        spread = elasticity_response(elasticity)["spread"]
        g, na, nb, ax = zone_weight(xx, yy, z, ml, widen=spread)
        gp = g * half * zone_protect[name]
        mix = _MIX[name]
        # radial term, in the zone's own elliptical frame: tissue expands away from the bolus (forward dome)
        bx = na * ax[0] - nb * ax[1]
        by = na * ax[1] + nb * ax[0]
        # never push tissue MEDIALLY (toward the nasolabial fold / nose): damp that half of the dome. Without this the
        # medial side compresses against the safety-line cut-off and leaves a vertical crease.
        c = bx * sg.outward[0] + by * sg.outward[1]
        cm = np.minimum(c, 0.0) * 0.75
        bx = bx - cm * sg.outward[0]
        by = by - cm * sg.outward[1]
        dx += gp * amp * (mix["radial"] * bx + mix["push"] * z.push_dir[0])
        dy += gp * amp * (mix["radial"] * by + mix["push"] * z.push_dir[1])
        if name == "ck3":
            fill += gp * float(np.clip(ml, 0.0, 1.0))
        else:
            height += gp * amp
        if name == "ck2":
            # under-eye -> cheek blend: wider footprint, upper half only (photometric, no displacement)
            gt = zone_weight(xx, yy, z, ml, widen=1.5 * spread)[0]
            rx, ry = xx - z.center[0], yy - z.center[1]
            up_w = _smooth((-(rx * lm.roll_v[0] + ry * lm.roll_v[1]) + 0.05 * scale) / (0.15 * scale))
            transition += gt * up_w * half * zone_protect[name]
    return dict(dx=dx, dy=dy, height=height, fill=fill, transition=transition, peak_px=peak_px)


def _fix_folds(dx, dy, min_det=0.35):
    """Backward map src = p - d folds where det(I - J(d)) <= 0. Scale d down until min det >= min_det."""
    def mindet(k):
        a = np.gradient(dx * k, axis=1); b = np.gradient(dx * k, axis=0)
        c = np.gradient(dy * k, axis=1); d = np.gradient(dy * k, axis=0)
        return float(((1 - a) * (1 - d) - b * c).min())
    if mindet(1.0) >= min_det:
        return dx, dy, 1.0
    lo, hi = 0.0, 1.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if mindet(mid) >= min_det:
            lo = mid
        else:
            hi = mid
    return dx * lo, dy * lo, lo


def apply_cheek_deformation(
    image: np.ndarray,
    lm: CheekLandmarks,
    *,
    volumes_left: dict[str, float],
    volumes_right: dict[str, float],
    glasses_mask: np.ndarray | None = None,
    elasticity: float = 1.0,
):
    """
    Returns dict(image, dx, dy, height, fill, transition, protect, zone_protect,
                 peak_left, peak_right, fold_scale)
    Left and right fields are computed independently and summed, so a
    unilateral treatment never leaks to the other cheek.
    """
    h, w = image.shape[:2]
    zone_protect = build_protect_maps((h, w), lm, glasses_mask)

    L = side_field((h, w), lm.left, lm, volumes_left, zone_protect, elasticity)
    R = side_field((h, w), lm.right, lm, volumes_right, zone_protect, elasticity)

    # fold fix PER SIDE: the two fields have disjoint support, and a stronger (asymmetry-boosted) side must
    # never shrink the reference side.
    dxl, dyl, kl = _fix_folds(L["dx"], L["dy"])
    dxr, dyr, kr = _fix_folds(R["dx"], R["dy"])
    dx, dy, k = dxl + dxr, dyl + dyr, min(kl, kr)
    height = L["height"] * kl + R["height"] * kr
    fill = L["fill"] + R["fill"]
    transition = L["transition"] + R["transition"]

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = cv2.remap(image, xx - dx, yy - dy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
    return dict(image=out, dx=dx, dy=dy, height=height, fill=fill, transition=transition,
                protect=np.maximum.reduce(list(zone_protect.values())), zone_protect=zone_protect,
                peak_left=L["peak_px"], peak_right=R["peak_px"], fold_scale=k)
