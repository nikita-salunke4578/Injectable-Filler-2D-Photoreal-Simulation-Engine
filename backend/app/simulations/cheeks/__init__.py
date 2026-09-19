"""
Cheeks simulation module.

Contains the midface/cheek treatment simulation pipeline:
    landmarks.py   – Cheek-specific landmark extraction, sub-zones & local anchor subsets
    glasses.py     – Eyeglasses detection & hard binary mask generation
    mask.py        – Orbital-safe cheek mask generation with glasses occlusion subtraction
    deformation.py – Isolated per-side geometric cheek deformation (RBF + TPS)
    refinement.py  – Displacement-driven LAB relighting and high-pass pore injection
    pipeline.py    – Orchestrates end-to-end simulation, validation & feathered alpha blending
"""

from app.simulations.cheeks.landmarks import (
    CHEEK_LANDMARKS,
    EYE_EXCLUSION_LANDMARKS,
    LOCAL_ANCHOR_INDICES,
    CheekLandmarks,
    extract_cheek_landmarks,
)
from app.simulations.cheeks.glasses import detect_glasses
from app.simulations.cheeks.mask import build_cheek_mask
from app.simulations.cheeks.deformation import apply_cheek_deformation
from app.simulations.cheeks.refinement import refine_cheek_region
from app.simulations.cheeks.pipeline import (
    CheeksSimulationConfig,
    CheeksSimulationResult,
    run_cheeks_pipeline,
    run_cheeks_simulation,
)

__all__ = [
    "CHEEK_LANDMARKS",
    "EYE_EXCLUSION_LANDMARKS",
    "LOCAL_ANCHOR_INDICES",
    "CheekLandmarks",
    "extract_cheek_landmarks",
    "detect_glasses",
    "build_cheek_mask",
    "apply_cheek_deformation",
    "refine_cheek_region",
    "CheeksSimulationConfig",
    "CheeksSimulationResult",
    "run_cheeks_pipeline",
    "run_cheeks_simulation",
]