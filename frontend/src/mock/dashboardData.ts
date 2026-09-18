import type { TreatmentZone } from '../types/simulation'

/**
 * Sections displayed in the top-level navigation.
 * 'overview' shows all regions; zone sections show individual detail.
 */
export type DashboardSection = 'overview' | TreatmentZone

export interface RegionInfo {
  id: TreatmentZone
  label: string
  tagline: string
  description: string
  owner: string
  status: 'In Development' | 'Under Development' | 'Ready'
  features: string[]
  pipelineSteps: string[]
  backendPath: string
}

/**
 * Static metadata for each treatment region.
 *
 * This drives the dashboard cards and region detail sections.
 * Do not invent fake progress — mark unimplemented regions honestly.
 */
export const REGION_INFO: Record<TreatmentZone, RegionInfo> = {
  lips: {
    id: 'lips',
    label: 'Lips',
    tagline: 'Volume & contour simulation',
    description:
      'Simulates controlled lip volume enhancement and contour changes using intensity-based TPS deformation with landmark-anchored displacement vectors.',
    owner: 'Jayam',
    status: 'In Development',
    features: [
      'Lip volume parameter (0–2.0 mL)',
      'Enhancement level (subtle / natural / full)',
      'Upper / lower balance control',
      'Key landmarks: 61, 291, 0, 17',
      'Thin Plate Spline (TPS) deformation',
      'Masked AI refinement',
    ],
    pipelineSteps: [
      'MediaPipe Landmarks',
      'Lip ROI',
      'Lip Mask (Delaunay + Gaussian feather)',
      'TPS Deformation',
      'Masked AI Refinement',
      'Poisson / Seamless Blending',
      'Validation',
    ],
    backendPath: 'backend/app/simulations/lips/',
  },

  cheeks: {
    id: 'cheeks',
    label: 'Cheeks',
    tagline: 'Midface volume simulation',
    description:
      'Simulates midface volume enhancement for cheek contouring. Supports bilateral and unilateral treatment with controlled deformation.',
    owner: 'Team Member',
    status: 'In Development',
    features: [
      'Cheek volume parameter (0–4.0 mL)',
      'Side selection (left / right / bilateral)',
      'Cheek-specific landmark region',
      'Controlled midface deformation',
      'Optional AI refinement',
    ],
    pipelineSteps: [
      'MediaPipe Landmarks',
      'Cheek ROI',
      'Cheek Mask',
      'Controlled Deformation',
      'Optional AI Refinement',
      'Blending',
      'Validation',
    ],
    backendPath: 'backend/app/simulations/cheeks/',
  },

  jaw: {
    id: 'jaw',
    label: 'Jaw',
    tagline: 'Contour & definition simulation',
    description:
      'Simulates lower-face contour enhancement and jawline definition. Focuses on contour sharpening rather than volumetric expansion.',
    owner: 'Team Member',
    status: 'Under Development',
    features: [
      'Jaw volume parameter (0–3.0 mL)',
      'Jawline definition control (0–100%)',
      'Mandible contour landmark region',
      'Contour-sharpening deformation',
      'Optional AI refinement',
    ],
    pipelineSteps: [
      'MediaPipe Landmarks',
      'Jaw ROI',
      'Jaw Mask',
      'Controlled Contour Deformation',
      'Optional AI Refinement',
      'Blending',
      'Validation',
    ],
    backendPath: 'backend/app/simulations/jaw/',
  },
}

/**
 * Ordered list of region IDs for consistent rendering.
 */
export const REGION_ORDER: TreatmentZone[] = ['lips', 'cheeks', 'jaw']
