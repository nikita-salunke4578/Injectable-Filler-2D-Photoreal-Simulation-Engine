"""
Shared Pydantic schemas for the simulation API.

These models define the contract between the React frontend and the
FastAPI backend.  Keep this file in sync with the TypeScript types in
``frontend/src/types/simulation.ts``.

Updating either side without updating the other will break the
integration contract.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enumerations ────────────────────────────────────────────────────


class TreatmentZone(str, Enum):
    """The three supported facial treatment regions."""

    LIPS = "lips"
    CHEEKS = "cheeks"
    JAW = "jaw"


# ── Request models ──────────────────────────────────────────────────


class ZoneSimulationRequest(BaseModel):
    """Parameters for a single treatment zone within a simulation."""

    zone: TreatmentZone
    volume: float = Field(ge=0, description="Simulation volume parameter (mL equivalent)")
    intensity: float = Field(ge=0, le=1, description="Normalised intensity 0-1")
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Zone-specific parameters (e.g. enhancementLevel, side, definition)",
    )


class CheekParameters(BaseModel):
    """Specific input parameters for cheek simulation."""

    lateral_volume_ck1: float = Field(default=1.0, ge=0.0, le=2.5, description="Lateral zygomatic volume (mL)")
    medial_volume_ck2: float = Field(default=0.5, ge=0.0, le=2.5, description="Malar apex volume (mL)")
    submalar_volume_ck3: float = Field(default=0.0, ge=0.0, le=2.0, description="Submalar hollow volume (mL)")
    asymmetry_mode: bool = Field(default=False, description="Enable independent left/right cheek multipliers")
    left_cheek_multiplier: float = Field(default=1.0, ge=0.0, le=2.0, description="Multiplier for left cheek volume")
    right_cheek_multiplier: float = Field(default=1.0, ge=0.0, le=2.0, description="Multiplier for right cheek volume")
    skin_elasticity: float = Field(default=1.0, ge=0.8, le=1.2, description="Skin elasticity spread factor")


class CheekSimulationRequest(BaseModel):
    """Direct request payload for /api/simulations/cheeks."""

    zone: str = Field(default="cheeks")
    image_base64: str = Field(description="Base64 encoded image data string")
    parameters: CheekParameters = Field(default_factory=CheekParameters)
    show_outline: bool = Field(default=False, description="Whether to draw cheek contour overlay")


class SimulationRequest(BaseModel):
    """
    Top-level simulation request sent by the frontend.

    Contains the image reference and one or more zone configurations.
    """

    image_url: str = Field(description="URL of the uploaded patient photo", default="")
    image_base64: str | None = Field(default=None, description="Base64 encoded image data string")
    show_outline: bool = Field(default=True, description="Whether to draw the dotted outline on the after image")
    zones: list[ZoneSimulationRequest] = Field(min_length=1)


# ── Response models ─────────────────────────────────────────────────


class SimulationResponse(BaseModel):
    """
    Response returned to the frontend after a simulation run.

    Mirrors the ``SimulationResult`` TypeScript interface.
    """

    id: str
    before_image_url: str
    after_image_url: str
    generated_at: datetime
    request_payload: list[ZoneSimulationRequest]
    estimated_cost_usd: tuple[float, float]
    total_volume_ml: float
    disclaimer: str = (
        "This is a simulated preview for planning and educational purposes only. "
        "Actual results vary by anatomy, product and injector technique."
    )
