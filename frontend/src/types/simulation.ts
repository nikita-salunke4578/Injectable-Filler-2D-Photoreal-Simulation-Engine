export type TreatmentZone = 'lips' | 'cheeks' | 'jaw'

export type AgeRange = '18-30' | '30-45' | '45-60' | '60+'

export type FillerExperience = 'first-time' | 'maintenance' | 'correction'

export type Gender = 'female' | 'male'

export type PrimaryConcern = 
  | 'long-upper-lip'
  | 'thin-vermilion'
  | 'downturned-corners'
  | 'aging-rejuvenation'

export type DesiredOutcome = 'natural' | 'glamorous' | 'dramatic'

export type LipShapePreference = 'heart' | 'round' | 'wide' | 'current'

export type SymmetryConcern = 'none' | 'mild' | 'significant'

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

export interface AnalysisMetrics {
  upper_height_px: number
  lower_height_px: number
  current_ratio: number
  ideal_ratio: number
  lip_width_px: number
  philtrum_length_px: number
  vermilion_thickness: 'thin' | 'medium' | 'full'
  symmetry_score: number
  cupids_bow_definition: 'flat' | 'moderate' | 'defined'
  mouth_corner_angle: number
}

export interface AnalysisSuggestedAnswers {
  gender: Gender
  ageRange: AgeRange
  primaryConcern: PrimaryConcern
  experience: FillerExperience
  desiredOutcome: DesiredOutcome
  lipShape: LipShapePreference
  symmetryConcern: SymmetryConcern
}

export interface AnalysisResult {
  metrics: AnalysisMetrics
  recommendation: {
    text: string
    suggested_volume_ml: number
    suggested_upper_lower_balance: number
  }
  suggested_parameters: LipParameters
  suggested_answers: AnalysisSuggestedAnswers
}

export interface AssessmentState {
  gender: Gender | null
  ageRange: AgeRange | null
  primaryConcern: PrimaryConcern | null
  experience: FillerExperience | null
  desiredOutcome: DesiredOutcome | null
  lipShape: LipShapePreference | null
  symmetryConcern: SymmetryConcern | null
  analysisResult: AnalysisResult | null
  analysisLoading: boolean
  analysisError: string | null
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
