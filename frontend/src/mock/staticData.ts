import type {
  AgeRange,
  FillerExperience,
  StepDefinition,
  TreatmentZone,
  ZoneMeta,
  Gender,
  PrimaryConcern,
  DesiredOutcome,
  LipShapePreference,
  SymmetryConcern
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

export const GENDERS: { id: Gender; label: string; helper: string }[] = [
  { id: 'female', label: 'Female', helper: 'Philtrum: 12-15mm' },
  { id: 'male', label: 'Male', helper: 'Philtrum: 16.5-18mm' },
]

export const AGE_RANGES: { id: AgeRange; label: string; helper: string }[] = [
  { id: '18-30', label: '18–30', helper: 'Cosmetic enhancement' },
  { id: '30-45', label: '30–45', helper: 'Early aging changes' },
  { id: '45-60', label: '45–60', helper: 'Moderate lengthening' },
  { id: '60+', label: '60+', helper: 'Significant philtral elongation' },
]

export const PRIMARY_CONCERNS: { id: PrimaryConcern; label: string; helper: string }[] = [
  { id: 'long-upper-lip', label: 'Long Upper Lip', helper: 'Elongated philtrum' },
  { id: 'thin-vermilion', label: 'Thin Vermilion', helper: 'Minimal lip show' },
  { id: 'downturned-corners', label: 'Downturned Corners', helper: 'Sad mouth appearance' },
  { id: 'aging-rejuvenation', label: 'Aging Rejuvenation', helper: 'Philtral lengthening with age' },
]

export const EXPERIENCE_LEVELS: { id: FillerExperience; label: string; helper: string }[] = [
  { id: 'first-time', label: 'First time', helper: 'Never had filler before' },
  { id: 'maintenance', label: 'Maintenance', helper: 'Regular filler patient' },
  { id: 'correction', label: 'Previous treatment', helper: 'Adjusting or correcting prior work' },
]

export const DESIRED_OUTCOMES: { id: DesiredOutcome; label: string; helper: string }[] = [
  { id: 'natural', label: 'Natural', helper: 'Subtle enhancement, barely noticeable' },
  { id: 'glamorous', label: 'Glamorous', helper: 'Noticeably fuller, photo-ready' },
  { id: 'dramatic', label: 'Dramatic', helper: 'Bold transformation, maximum impact' },
]

export const CHEEK_PRIMARY_CONCERNS = [
  { id: 'flat-malar', label: 'Flat Cheekbones', helper: 'Lack of forward projection at malar apex' },
  { id: 'submalar-hollow', label: 'Gaunt Midface Hollows', helper: 'Depression beneath zygomatic bone' },
  { id: 'midface-sagging', label: 'Midface Laxity & Volume Loss', helper: 'Loss of lateral lift and youthful apex' },
  { id: 'cheek-asymmetry', label: 'Cheek Asymmetry', helper: 'Uneven volume between left and right' },
]

export const CHEEK_DESIRED_OUTCOMES = [
  { id: 'contour', label: 'High Cheekbone Contour', helper: 'Sculpted lateral lift & defined apex' },
  { id: 'natural', label: 'Natural Midface Volume', helper: 'Balanced, youthful softness' },
  { id: 'dramatic', label: 'Model Zygomatic Lift', helper: 'Bold lateral sweep towards hairline' },
]

export const CHEEK_ELASTICITY_OPTIONS = [
  { id: 'tight', label: 'Firm / Young (0.9x)', helper: 'High skin elasticity, localized lift' },
  { id: 'normal', label: 'Standard (1.0x)', helper: 'Balanced elasticity and dispersion' },
  { id: 'lax', label: 'Mature / Lax (1.15x)', helper: 'Soft tissue with wider volume spread' },
]

export const LIP_SHAPES: { id: LipShapePreference; label: string; helper: string }[] = [
  { id: 'heart', label: 'Heart', helper: 'Defined cupid\'s bow, tapered corners' },
  { id: 'round', label: 'Round', helper: 'Soft, evenly full shape' },
  { id: 'wide', label: 'Wide', helper: 'Horizontally broad with volume' },
  { id: 'current', label: 'Keep Current', helper: 'Enhance without shape change' },
]

export const SYMMETRY_CONCERNS: { id: SymmetryConcern; label: string; helper: string }[] = [
  { id: 'none', label: 'No Concern', helper: 'Lips appear symmetrical' },
  { id: 'mild', label: 'Mild Asymmetry', helper: 'Slight unevenness' },
  { id: 'significant', label: 'Significant Asymmetry', helper: 'Noticeable left-right difference' },
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
