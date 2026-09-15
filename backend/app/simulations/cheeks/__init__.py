"""
Cheeks simulation module.

Owner: Team Member

This package contains the cheek treatment simulation pipeline.
It is responsible for:
    - Extracting cheek-specific landmarks from the shared face mesh
    - Building the cheek treatment region mask
    - Applying controlled geometric deformation for midface volume
    - Running optional AI refinement
    - Producing the simulation result

Shared infrastructure (MediaPipe initialisation, image I/O, blending)
belongs in ``app.common``.  This module only contains cheek-specific
logic.

Module layout:
    pipeline.py    – Orchestrates the full cheeks simulation
    landmarks.py   – Cheek-specific landmark extraction
    mask.py        – Cheek treatment region / ROI mask generation
    deformation.py – Controlled geometric cheek deformation
    refinement.py  – Masked AI refinement for photorealism
"""
