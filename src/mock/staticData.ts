import type {
  AgeRange,
  FillerExperience,
  StepDefinition,
  TreatmentZone,
  ZoneMeta,
} from '../types/simulation'

export const WIZARD_STEPS: StepDefinition[] = [
  { id: 'photo', label: 'Photo', order: 1 },
  { id: 'assessment', label: 'Assessment', order: 2 },
  { id: 'configure', label: 'Configure', order: 3 },
  { id: 'preview', label: 'Preview', order: 4 },
]

export const ZONES: ZoneMeta[] = [
  { id: 'lips', label: 'Lips', description: 'Volume, shape and border definition' },
  { id: 'cheeks', label: 'Cheeks', description: 'Midface volume and contour' },
  { id: 'jaw', label: 'Jaw', description: 'Jawline definition and angle' },
]

export const AGE_RANGES: { id: AgeRange; label: string; helper: string }[] = [
  { id: '18-30', label: '18–30', helper: 'Enhancement-focused' },
  { id: '30-45', label: '30–45', helper: 'Early volume loss' },
  { id: '45-60', label: '45–60', helper: 'Moderate volume restoration' },
  { id: '60+', label: '60+', helper: 'Significant facial volume loss' },
]

export const EXPERIENCE_LEVELS: { id: FillerExperience; label: string; helper: string }[] = [
  { id: 'first-time', label: 'First time', helper: 'Never had filler before' },
  { id: 'maintenance', label: 'Maintenance', helper: 'Regular filler patient' },
  { id: 'correction', label: 'Previous treatment', helper: 'Adjusting or correcting prior work' },
]

export const ZONE_VOLUME_LIMITS: Record<TreatmentZone, number> = {
  lips: 2.0,
  cheeks: 4.0,
  jaw: 3.0,
}

export const TREATMENT_INFO = {
  onset: 'Immediate, settles over 7 days',
  lasts: '~6–18 months',
  reversible: 'HA fillers can be dissolved with hyaluronidase if needed.',
}
