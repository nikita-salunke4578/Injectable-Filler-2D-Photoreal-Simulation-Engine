"""
End-to-end cheek filler simulation.

    landmarks -> zone geometry -> volumes (per side/zone)
              -> geometric deformation (protected: eyes, lips, nose wing, glasses)
              -> blend mask -> photometric refinement -> result
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

from .landmarks import extract_cheek_landmarks
from .deformation import apply_cheek_deformation, elasticity_response, MAX_VOLUME_ML
from .mask import build_cheek_mask
from .refinement import refine_cheek_region

logger = logging.getLogger(__name__)

# The UI talks about the PATIENT's left/right cheek. In a normal (non-mirrored)
# photo the patient's left cheek is on the IMAGE right. The engine works in
# image-sides internally, so API-level sides are swapped when this is True.
PATIENT_SIDE_IS_MIRRORED = True

# Heavy per-pixel maths runs on the face region only, capped to this size.
MAX_PROCESS_PX = 1400


@dataclass
class CheeksSimulationConfig:
    lateral_volume_ck1: float = 1.0      # mL per side
    medial_volume_ck2: float = 0.6       # mL per side (malar apex)
    submalar_volume_ck3: float = 0.0     # mL per side
    side: str = "bilateral"              # "left" | "right" | "bilateral"  (image side)
    asymmetry_mode: bool = False
    left_cheek_multiplier: float = 1.0
    right_cheek_multiplier: float = 1.0
    skin_elasticity: float = 1.0         # UI 'Skin Elasticity Scale' 0.8 tight/youthful (localised, crisp) .. 1.2 mature/lax (broad, soft)
    shading_gain: float = 1.0
    # explicit per-side volumes (IMAGE sides), e.g. {"left": {"ck1": 2.0, "ck2": 0, "ck3": 0}, "right": {...}}.
    # When given, it replaces the shared volumes / side / multipliers: each cheek gets exactly what was requested.
    side_volumes: dict | None = None


@dataclass
class CheeksSimulationResult:
    image: np.ndarray
    mask: np.ndarray
    peak_shift_px: tuple[float, float]
    total_volume_ml: float
    warnings: list[str] = field(default_factory=list)
    debug: dict = field(default_factory=dict)


def _volumes(cfg: CheeksSimulationConfig, side: str) -> dict:
    if cfg.side_volumes is not None:
        sv = cfg.side_volumes.get(side) or {}
        return {k: float(np.clip(float(sv.get(k, 0.0)), 0.0, MAX_VOLUME_ML)) for k in ("ck1", "ck2", "ck3")}
    active = cfg.side in ("bilateral", side)
    if not active:
        return {"ck1": 0.0, "ck2": 0.0, "ck3": 0.0}
    m = 1.0
    if cfg.asymmetry_mode:
        m = cfg.left_cheek_multiplier if side == "left" else cfg.right_cheek_multiplier
    cap = lambda v: float(np.clip(v * m, 0.0, MAX_VOLUME_ML))
    return {"ck1": cap(cfg.lateral_volume_ck1), "ck2": cap(cfg.medial_volume_ck2),
            "ck3": cap(cfg.submalar_volume_ck3)}


def run_cheeks_simulation(image: np.ndarray, face_landmarks: np.ndarray,
                          config: CheeksSimulationConfig | None = None,
                          glasses_mask: np.ndarray | None = None) -> CheeksSimulationResult:
    cfg = config or CheeksSimulationConfig()
    if cfg.side not in ("left", "right", "bilateral"):
        raise ValueError("side must be 'left', 'right' or 'bilateral'")
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("image must be an HxWx3 BGR uint8 array")

    warnings: list[str] = []
    lm = extract_cheek_landmarks(face_landmarks)
    vl, vr = _volumes(cfg, "left"), _volumes(cfg, "right")
    total = sum(vl.values()) + sum(vr.values())

    # yaw sanity: nose bridge should sit near the midpoint of the cheeks' edges
    p = lm.pts
    dl, dr = abs(p[1][0] - p[234][0]), abs(p[454][0] - p[1][0])
    if min(dl, dr) / max(dl, dr, 1.0) < 0.6:
        warnings.append("Head is turned noticeably; results are most realistic on near-frontal photos.")

    # clinical sanity: typical midface totals are ~1-3 mL PER SIDE (deep 0.7-2.4 + superficial); beyond that
    # the result looks overfilled ("pillow face") and the simulation is no longer representative.
    for nm, vv in (("left", vl), ("right", vr)):
        if sum(vv.values()) > 3.0:
            warnings.append(f"{nm.capitalize()} cheek total {sum(vv.values()):.1f} mL exceeds the usual 1-3 mL per side; "
                            "risk of an overfilled look.")

    if total <= 1e-4:
        return CheeksSimulationResult(image.copy(), np.zeros(image.shape[:2], np.uint8), (0.0, 0.0), 0.0, warnings)

    d = apply_cheek_deformation(image, lm, volumes_left=vl, volumes_right=vr,
                                glasses_mask=glasses_mask, elasticity=cfg.skin_elasticity)
    mask = build_cheek_mask(image.shape, lm, d["zone_protect"], volumes_left=vl, volumes_right=vr,
                            glasses_mask=glasses_mask, elasticity=cfg.skin_elasticity)
    out = refine_cheek_region(d["image"], image, mask, lm, d["dx"], d["dy"], d["height"],
                              fill=d["fill"], transition=d["transition"], shading_gain=cfg.shading_gain,
                              crispness=elasticity_response(cfg.skin_elasticity)["crisp"])
    if glasses_mask is not None:                       # frames / lenses stay bit-identical to the input
        gm = glasses_mask if glasses_mask.ndim == 2 else glasses_mask[..., 0]
        out[gm > 127] = image[gm > 127]
    if d["fold_scale"] < 1.0:
        warnings.append(f"Volume was auto-limited to {d['fold_scale']:.0%} to avoid distortion.")
    pl = max(d["peak_left"].values(), default=0.0)
    pr = max(d["peak_right"].values(), default=0.0)
    return CheeksSimulationResult(out, mask, (float(pl), float(pr)), float(total), warnings,
                                  debug={"dx": d["dx"], "dy": d["dy"], "protect": d["protect"], "zone_protect": d["zone_protect"],
                                         "height": d["height"], "fill": d["fill"], "landmarks": lm})


def _to_image_side(side: str) -> str:
    if side == "bilateral" or not PATIENT_SIDE_IS_MIRRORED:
        return side
    return "right" if side == "left" else "left"


def _face_roi(shape, pts: np.ndarray, pad: float = 0.25) -> tuple[int, int, int, int]:
    h, w = shape[:2]
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    p = pad * max(x1 - x0, y1 - y0)
    return (max(0, int(x0 - p)), max(0, int(y0 - p)),
            min(w, int(np.ceil(x1 + p))), min(h, int(np.ceil(y1 + p))))


def _draw_modified_outline(img: np.ndarray, mask: np.ndarray, level: int = 96) -> np.ndarray:
    """Thin white border around the area the simulation changed - same style as the lips overlay
    (1px anti-aliased white polyline, blended at 60% opacity). The contour comes from the blend mask,
    one closed line per modified region (one per cheek)."""
    h, w = mask.shape[:2]
    binary = (mask > level).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, k)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in contours:
        if cv2.contourArea(c) < 80:
            continue
        eps = max(0.75, 0.0015 * cv2.arcLength(c, True))
        polys.append(cv2.approxPolyDP(c, eps, True).astype(np.int32))
    if not polys:
        return img
    thick = max(1, int(round(min(h, w) / 1400)))        # 1px up to ~1400px images, scales for big photos
    overlay = img.copy()
    cv2.polylines(overlay, polys, isClosed=True, color=(255, 255, 255), thickness=thick, lineType=cv2.LINE_AA)
    return cv2.addWeighted(overlay, 0.6, img, 0.4, 0)


def run_cheeks_pipeline_detailed(
    image: np.ndarray,
    lateral_volume_ck1: float = 1.0,
    medial_volume_ck2: float = 0.6,
    submalar_volume_ck3: float = 0.0,
    asymmetry_mode: bool = False,
    left_cheek_multiplier: float = 1.0,
    right_cheek_multiplier: float = 1.0,
    skin_elasticity: float = 1.0,
    show_outline: bool = False,
    side: str = "bilateral",
    face_detector=None,
    protect_glasses: bool = True,
    volumes_by_side: dict | None = None,
) -> CheeksSimulationResult:
    """Full pipeline: detect -> glasses mask -> ROI crop -> simulate -> paste back.

    ``left``/``right`` (``side``, the multipliers and ``volumes_by_side``) refer to the PATIENT's
    cheeks, matching the UI labels.

    ``volumes_by_side`` = {"left": {"ck1": mL, "ck2": mL, "ck3": mL}, "right": {...}} gives every cheek its own
    volumes (e.g. Left +2 mL / Right +0 mL, or Left 2 / Right 1). A missing/zero side is left bit-identical.
    It overrides the shared volumes, ``side`` and the multipliers. The baseline asymmetry of the face is always
    preserved: each side is deformed from its own landmarks, nothing is mirrored or symmetrised.
    """
    from .detector import detect_landmarks
    from .glasses import detect_glasses

    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("image must be an HxWx3 BGR uint8 array")

    pts = detect_landmarks(image, face_detector).astype(np.float32)

    # patient-side -> image-side
    img_side = _to_image_side(side)
    l_mult, r_mult = left_cheek_multiplier, right_cheek_multiplier
    if PATIENT_SIDE_IS_MIRRORED:
        l_mult, r_mult = r_mult, l_mult
    cfg = CheeksSimulationConfig(
        lateral_volume_ck1=lateral_volume_ck1, medial_volume_ck2=medial_volume_ck2,
        submalar_volume_ck3=submalar_volume_ck3, side=img_side,
        asymmetry_mode=asymmetry_mode, left_cheek_multiplier=l_mult,
        right_cheek_multiplier=r_mult, skin_elasticity=float(np.clip(skin_elasticity, 0.8, 1.2)),
    )
    if volumes_by_side is not None:
        pv = {s: volumes_by_side.get(s) or {} for s in ("left", "right")}
        if PATIENT_SIDE_IS_MIRRORED:                         # patient side -> image side
            pv = {"left": pv["right"], "right": pv["left"]}
        cfg.side_volumes = pv

    warnings: list[str] = []
    glasses_full = None
    if protect_glasses:
        try:
            found, gmask = detect_glasses(image, extract_cheek_landmarks(pts))
            if found and gmask is not None:
                k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
                glasses_full = cv2.dilate(gmask, k)          # small safety margin around frames
                warnings.append("Eyeglasses detected - frames were left untouched.")
        except Exception:                                    # glasses are optional; never fail the sim
            logger.exception("Glasses detection failed; continuing without it.")

    # ---- crop to face ROI (and cap size) -------------------------------
    x0, y0, x1, y1 = _face_roi(image.shape, pts)
    roi = image[y0:y1, x0:x1]
    roi_pts = pts - np.array([x0, y0], np.float32)
    roi_gl = None if glasses_full is None else glasses_full[y0:y1, x0:x1]
    rh, rw = roi.shape[:2]
    f = min(1.0, MAX_PROCESS_PX / max(rh, rw))
    if f < 1.0:
        proc = cv2.resize(roi, (int(rw * f), int(rh * f)), interpolation=cv2.INTER_AREA)
        roi_pts = roi_pts * f
        if roi_gl is not None:
            roi_gl = cv2.resize(roi_gl, (proc.shape[1], proc.shape[0]), interpolation=cv2.INTER_NEAREST)
    else:
        proc = roi

    res = run_cheeks_simulation(proc, roi_pts, cfg, roi_gl)
    warnings = res.warnings + warnings

    out_roi, mask_roi = res.image, res.mask
    if f < 1.0:
        a = cv2.resize(mask_roi, (rw, rh), interpolation=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255.0
        up = cv2.resize(out_roi, (rw, rh), interpolation=cv2.INTER_CUBIC).astype(np.float32)
        out_roi = np.clip(up * a + roi.astype(np.float32) * (1 - a), 0, 255).astype(np.uint8)
        mask_roi = (a[..., 0] * 255).astype(np.uint8)

    final = image.copy()
    final[y0:y1, x0:x1] = out_roi
    full_mask = np.zeros(image.shape[:2], np.uint8)
    full_mask[y0:y1, x0:x1] = mask_roi

    if show_outline and res.total_volume_ml > 1e-4:
        final = _draw_modified_outline(final, full_mask)

    return CheeksSimulationResult(final, full_mask, res.peak_shift_px, res.total_volume_ml, warnings, res.debug)


def run_cheeks_pipeline(image: np.ndarray, **kwargs) -> np.ndarray:
    """Thin wrapper returning only the BGR image (same style as ``run_lips_pipeline``)."""
    return run_cheeks_pipeline_detailed(image, **kwargs).image
