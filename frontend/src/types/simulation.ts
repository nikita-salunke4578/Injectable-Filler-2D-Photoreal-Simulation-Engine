export type TreatmentZone = 'lips' | 'cheeks' | 'jaw'

export type AgeRange = '18-30' | '30-45' | '45-60' | '60+'

export type FillerExperience = 'first-time' | 'maintenance' | 'correction'

export type WizardStep = 'photo' | 'assessment' | 'configure' | 'preview'

export interface StepDefinition {
  id: WizardStep
  label: string
  order: number
}

export interface PatientPhotoState {
  file: File | null
  previewUrl: string | null
  consentGiven: boolean
  captureMethod: 'upload' | 'camera' | null
}

export interface AnalysisResult {
  metrics: {
    upper_height_px: number
    lower_height_px: number
    current_ratio: number
    ideal_ratio: number
  }
  recommendation: {
    text: string
    suggested_volume_ml: number
    suggested_upper_lower_balance: number
  }
}

export type Gender = 'female' | 'male'

export type PrimaryConcern = 
  | 'long-upper-lip'
  | 'thin-vermilion'
  | 'downturned-corners'
  | 'aging-rejuvenation'

export interface AssessmentState {
  gender: Gender | null
  ageRange: AgeRange | null
  primaryConcern: PrimaryConcern | null
  experience: FillerExperience | null
  analysisResult: AnalysisResult | null
}

export interface LipParameters {
  philtralShortening: number
  vermilionShow: number
  cupidsBow: number
  philtralColumn: number
  dentalShow: number
}

export type CheekSide = 'left' | 'right' | 'bilateral'

export interface CheekParameters {
  volumeMl: number
  side: CheekSide
}

export interface JawParameters {
  volumeMl: number
  definition: number // 0-100, softness -> sharp definition
}

export interface ZoneParameterMap {
  lips: LipParameters
  cheeks: CheekParameters
  jaw: JawParameters
}

export interface ConfigurationState {
  activeZone: TreatmentZone
  enabledZones: Record<TreatmentZone, boolean>
  parameters: ZoneParameterMap
  showOutline: boolean
}

/**
 * Structured payload the simulation engine will eventually consume.
 * Keep this shape stable — it is the frontend/backend contract.
 */
export interface SimulationRequestPayload {
  zone: TreatmentZone
  volume: number
  intensity: number
  meta: Record<string, unknown>
}

export type SimulationStatus = 'idle' | 'loading' | 'success' | 'error'

export interface SimulationResult {
  id: string
  beforeImageUrl: string
  afterImageUrl: string
  generatedAt: string
  requestPayload: SimulationRequestPayload[]
  estimatedCostUsd: [number, number]
  totalVolumeMl: number
  disclaimer: string
}

export interface ZoneMeta {
  id: TreatmentZone
  label: string
  description: string
}
