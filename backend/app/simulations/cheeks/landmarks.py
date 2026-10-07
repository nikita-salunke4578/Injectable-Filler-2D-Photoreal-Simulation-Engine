"""
Cheek landmarks and anatomical zone geometry.

Input : (N>=468, 2) MediaPipe face-mesh landmarks in pixel coordinates.
Output: per-side geometry for three filler zones, all expressed relative to
        the face's own scale and roll so it works for any resolution / tilt.

Naming: "left" / "right" refer to the IMAGE side (left = smaller x), which is
what the sliders in the UI show. (MediaPipe index 234 is on the image-left.)

Zones (per side) - placed the way an injector marks them. Each mode has its OWN
behaviour (see deformation.py), they are not three sizes of the same bump:

    ck1  ZYGOMATIC (lateral). Upper-lateral cheek on the tragus->apex line.
         Moves tissue OUTWARD + slightly up; fades out below the arch so the
         lower cheek is never swollen.                -> cheekbone width / definition
    ck2  MALAR (central). Malar apex located with HINDERER'S LINES: intersection of
         (a) lateral canthus -> oral commissure and (b) tragus -> superior ala.
         Moves tissue FORWARD (frontal view: dome magnification, no net lateral
         drift) + slightly up; elongated toward the infra-orbital rim so the
         under-eye -> cheek transition is smooth.     -> central fullness / projection
    ck3  SUBMALAR (concavity). Below the apex, lateral to the mid-cheek safety
         line (medial canthus -> gonion). A FILL, not a lift: pushes the local
         depression OUTWARD toward the zygoma->gonion contour chord; gated to zero
         above the apex so it can never build a new cheekbone; amplitude is bounded
         by the measured hollow depth (``Zone.hollow_px``).

Each zone is an ELLIPTICAL footprint oriented along its anatomical axis. ``gate`` is
an optional smooth half-plane (n, ref, offset, width) that confines a zone to one
side of a face-frame line (ck1: not below the arch, ck3: not above the apex).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

# image-left / image-right MediaPipe indices
SIDE_IDX = {
    "left": dict(eye_outer=33, eye_inner=133, mouth=61, ala=129, edge=234,
                 jaw=58, temple=127, brow=105,
                 lower_lid=[33, 7, 163, 144, 145, 153, 154, 155, 133],
                 upper_lid=[246, 161, 160, 159, 158, 157, 173], submalar=[93, 132]),
    "right": dict(eye_outer=263, eye_inner=362, mouth=291, ala=358, edge=454,
                  jaw=288, temple=356, brow=334,
                  lower_lid=[263, 249, 390, 373, 374, 380, 381, 382, 362],
                  upper_lid=[466, 388, 387, 386, 385, 384, 398], submalar=[323, 361]),
}
LIPS_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
NOSE_WING = {"left": [129, 49, 64, 98, 240, 219, 218, 237], "right": [358, 279, 294, 327, 460, 439, 438, 457]}
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400,
             377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]


@dataclass
class Zone:
    name: str                 # ck1 / ck2 / ck3
    center: np.ndarray        # (2,) px
    sigma: float              # px (Gaussian radius)
    push_dir: np.ndarray      # (2,) unit vector: where the volume pushes the skin (px space)
    axis: np.ndarray = None   # (2,) unit major axis of the elliptical footprint
    aspect: float = 1.0       # sigma_major / sigma_minor
    gate: object = None       # (n, ref, offset, width) px or a list of them: smooth half-plane weights, see zone_gate()
    hollow_px: float = 0.0    # ck3: measured inward bow of the contour (px) = how much concavity exists


@dataclass
class SideGeometry:
    side: str
    zones: dict[str, Zone]
    outward: np.ndarray       # unit vector pointing from midline to this cheek (lateral)
    up: np.ndarray            # unit vector "up" in the face frame
    eye_pts: np.ndarray       # lower+upper eyelid polygon pts
    lower_lid: np.ndarray
    edge: np.ndarray
    medial_line: tuple = None  # (medial canthus, gonion): mid-cheek safety line, never injected medially
    tragus: np.ndarray = None  # tragus proxy (landmark at the ear-side cheek edge)
    hinderer_ok: bool = True   # False if the Hinderer intersection was implausible and a fallback was used


@dataclass
class CheekLandmarks:
    pts: np.ndarray
    scale: float              # inter-ocular distance (outer canthi), px
    roll_u: np.ndarray        # unit vector along the eye line (image-left -> image-right)
    roll_v: np.ndarray        # unit vector "down" in face frame
    left: SideGeometry
    right: SideGeometry
    lips: np.ndarray
    nose_wing: dict
    oval: np.ndarray
    apexes: tuple = field(default=None)

    # ---- convenience views (used by glasses.py and analysis.py) ----------
    @property
    def anchors(self) -> np.ndarray:
        """Face outline + brows: defines the crop handed to the glasses parser."""
        brows = self.pts[[105, 334, 55, 285, 107, 336]]
        return np.vstack([self.oval, brows]).astype(np.float32)

    @property
    def left_apex(self) -> np.ndarray:
        return self.left.zones["ck2"].center

    @property
    def right_apex(self) -> np.ndarray:
        return self.right.zones["ck2"].center

    @property
    def nose_bridge(self) -> np.ndarray:
        return self.pts[6]

    @property
    def left_ck3(self) -> np.ndarray:
        return self.left.zones["ck3"].center.reshape(1, 2)

    @property
    def right_ck3(self) -> np.ndarray:
        return self.right.zones["ck3"].center.reshape(1, 2)

    @property
    def left_all(self) -> np.ndarray:
        return np.vstack([z.center for z in self.left.zones.values()] + [self.left.edge])

    @property
    def right_all(self) -> np.ndarray:
        return np.vstack([z.center for z in self.right.zones.values()] + [self.right.edge])

    @property
    def left_eye_exclusion(self) -> np.ndarray:
        return self.left.eye_pts

    @property
    def right_eye_exclusion(self) -> np.ndarray:
        return self.right.eye_pts


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-6 else v


def _intersect(a1, a2, b1, b2):
    """Intersection of line a1->a2 with line b1->b2, or None if (near) parallel."""
    d1, d2 = a2 - a1, b2 - b1
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(float(den)) < 1e-6 * max(float(np.linalg.norm(d1) * np.linalg.norm(d2)), 1e-6):
        return None
    w = b1 - a1
    t = (w[0] * d2[1] - w[1] * d2[0]) / den
    return a1 + t * d1


def _hollow_depth(pts, edge, mids, jaw, toward_mid):
    """Inward bow (px, >=0) of the zygoma->gonion contour, and the OUTWARD unit normal of that chord."""
    a, b = pts[edge], pts[jaw]
    ch = b - a
    n = np.array([-ch[1], ch[0]], np.float32) / max(float(np.linalg.norm(ch)), 1e-6)
    if float(n @ toward_mid) < 0:
        n = -n                                         # n now points toward the midline
    bow = float(np.mean([(pts[m] - a) @ n for m in mids]))
    return max(0.0, bow), (-n).astype(np.float32)


def _side(pts, side, scale, u, v):
    ix = SIDE_IDX[side]
    E, M, Z = pts[ix["eye_outer"]], pts[ix["mouth"]], pts[ix["edge"]]
    J, ALA, MC = pts[ix["jaw"]], pts[ix["ala"]], pts[ix["eye_inner"]]
    T = Z                              # tragus proxy: MediaPipe 234/454 sit at the ear-side cheek edge
    sgn = -1.0 if side == "left" else 1.0
    out = u * sgn                      # lateral direction for this side
    up = -v

    # --- ck2: malar apex from Hinderer's lines ---------------------------------
    legacy = E + 0.52 * (M - E) + out * 0.03 * scale
    apex = _intersect(E, M, T, ALA)
    ok = apex is not None
    if ok:
        rel = apex - E
        depth = float(rel @ v) / scale                 # below the eye line, in face scales
        lat = float(rel @ (-out)) / scale              # medial offset from the outer canthus
        # a smile / head turn can push the intersection outside the anatomical window
        ok = 0.22 <= depth <= 0.62 and -0.10 <= lat <= 0.42
        if not ok:
            depth, lat = float(np.clip(depth, 0.30, 0.55)), float(np.clip(lat, -0.02, 0.30))
            apex = E + v * depth * scale + (-out) * lat * scale
            apex = 0.5 * apex + 0.5 * legacy
    else:
        apex = legacy
    c2 = apex.astype(np.float32)

    arch = _unit(T - c2)               # direction along the zygomatic arch toward the ear
    # --- ck1: upper-lateral cheek, mid-arch, a touch above the apex line (before the lateral safety line)
    c1 = c2 + 0.60 * (T - c2) + up * 0.05 * scale
    # --- ck3: below the apex, lateral to the NLF / mid-cheek safety line, above the commissure
    c3 = c2 + 0.42 * (M + out * 0.10 * scale - c2) + 0.08 * (J - c2) + out * 0.04 * scale
    # the submalar hollow reaches the contour: pull the centre part-way toward the contour's concave point
    c3 = c3 + 0.35 * (pts[ix["submalar"]].mean(axis=0) - c3)
    slope = _unit(c2 - c3)             # apex -> hollow axis (orientation of the submalar ellipse)

    # ck3 measures the real concavity of the contour and fills toward its chord (outward normal)
    hollow_px, chord_out = _hollow_depth(pts, ix["edge"], ix["submalar"], ix["jaw"], -out)

    zones = {
        # CK1 outward + slightly up; confined ABOVE the arch (weight fades to 0 ~0.2*scale below c1)
        "ck1": Zone("ck1", c1, 0.16 * scale, _unit(out * 0.90 + up * 0.30), axis=arch, aspect=1.6,
                    gate=(-v.astype(np.float32), c1.copy(), 0.26 * scale, 0.34 * scale)),
        # CK2 forward (radial dome) + slight up; ellipse leans toward the infra-orbital rim for the under-eye blend
        "ck2": Zone("ck2", c2, 0.18 * scale, _unit(up.astype(np.float32)),
                    axis=_unit(up * 0.85 - out * 0.15), aspect=1.12),
        # CK3 outward fill of the concavity; zero above the apex (never builds a cheekbone)
        "ck3": Zone("ck3", c3, 0.18 * scale, chord_out, axis=slope, aspect=1.5,
                    gate=[(v.astype(np.float32), c2.copy(), -0.05 * scale, 0.16 * scale),      # not above the apex
                          (-v.astype(np.float32), J.copy(), 0.0, 0.12 * scale)],           # not at/below the gonion (jaw)
                    hollow_px=hollow_px),
    }
    return SideGeometry(
        side=side, zones=zones, outward=out, up=up,
        eye_pts=pts[ix["lower_lid"] + ix["upper_lid"]],
        lower_lid=pts[ix["lower_lid"]], edge=Z,
        medial_line=(MC.copy(), J.copy()), tragus=T.copy(), hinderer_ok=bool(ok),
    )


def extract_cheek_landmarks(face_landmarks: np.ndarray) -> CheekLandmarks:
    p = np.asarray(face_landmarks, dtype=np.float32)[:, :2]
    if len(p) < 468:
        raise ValueError(f"expected >=468 landmarks, got {len(p)}")
    eye_l, eye_r = p[33], p[263]
    scale = float(max(np.linalg.norm(eye_r - eye_l), 30.0))
    u = _unit(eye_r - eye_l)
    v = np.array([-u[1], u[0]], dtype=np.float32)   # perpendicular, pointing down when upright
    if v[1] < 0:
        v = -v
    L, R = _side(p, "left", scale, u, v), _side(p, "right", scale, u, v)
    return CheekLandmarks(
        pts=p, scale=scale, roll_u=u, roll_v=v, left=L, right=R,
        lips=p[LIPS_OUTER], nose_wing={s: p[NOSE_WING[s]] for s in NOSE_WING},
        oval=p[FACE_OVAL],
        apexes=(L.zones["ck2"].center.copy(), R.zones["ck2"].center.copy()),
    )