"""
Lips simulation module.

Owner: Jayam

This package contains the complete lips treatment simulation pipeline.
It is responsible for:
    - Extracting lip-specific landmarks from the shared face mesh
    - Building the lip treatment region mask
    - Applying controlled geometric deformation
    - Running optional AI refinement
    - Producing the simulation result

Shared infrastructure (MediaPipe initialisation, image I/O, blending)
belongs in ``app.common``.  This module only contains lips-specific
logic.

Module layout:
    pipeline.py    – Orchestrates the full lips simulation
    landmarks.py   – Lip-specific landmark extraction
    mask.py        – Lip treatment region / ROI mask generation
    deformation.py – Controlled geometric lip deformation (TPS)
    refinement.py  – Masked AI refinement for photorealism
"""
