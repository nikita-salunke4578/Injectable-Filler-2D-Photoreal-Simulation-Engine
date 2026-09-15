"""
Jaw simulation module.

Owner: Team Member

This package contains the jaw treatment simulation pipeline.
It is responsible for:
    - Extracting jaw-specific landmarks from the shared face mesh
    - Building the jaw/lower-face treatment region mask
    - Applying controlled contour deformation for jawline definition
    - Running optional AI refinement
    - Producing the simulation result

The jaw simulation focuses on lower-face contour changes rather than
volume addition.  The goal is to simulate jawline definition and angle
enhancement.

Shared infrastructure (MediaPipe initialisation, image I/O, blending)
belongs in ``app.common``.  This module only contains jaw-specific
logic.

Module layout:
    pipeline.py    – Orchestrates the full jaw simulation
    landmarks.py   – Jaw-specific landmark extraction
    mask.py        – Jaw treatment region / ROI mask generation
    deformation.py – Controlled geometric jaw deformation
    refinement.py  – Masked AI refinement for photorealism
"""
