"""
Cheeks simulation module.

Contains the midface/cheek treatment simulation pipeline:
    landmarks.py   – Cheek-specific landmark extraction & anatomical zones
    mask.py        – Orbital-safe cheek treatment region mask generation
    deformation.py – Controlled geometric cheek deformation (RBF + TPS)
    refinement.py  – Non-AI LAB relighting, micro specular sheen, and high-pass pore injection
    pipeline.py    – Orchestrates end-to-end simulation and Poisson blending
"""

from app.simulations.cheeks.landmarks import (
    CHEEK_LANDMARKS,
    EYE_EXCLUSION_LANDMARKS,
    CheekLandmarks,
    extract_cheek_landmarks,
)
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
    "CheekLandmarks",
    "extract_cheek_landmarks",
    "build_cheek_mask",
    "apply_cheek_deformation",
    "refine_cheek_region",
    "CheeksSimulationConfig",
    "CheeksSimulationResult",
    "run_cheeks_pipeline",
    "run_cheeks_simulation",
]
