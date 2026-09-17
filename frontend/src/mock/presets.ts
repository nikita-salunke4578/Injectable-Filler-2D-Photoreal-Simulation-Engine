import type { CheekParameters, JawParameters, LipParameters, TreatmentZone } from '../types/simulation'

export interface ConfigurationPreset {
  id: string
  label: string
  description: string
  recommended?: boolean
  enabledZones: TreatmentZone[]
  parameters: {
    lips?: Partial<LipParameters>
    cheeks?: Partial<CheekParameters>
    jaw?: Partial<JawParameters>
  }
}

export const CONFIGURATION_PRESETS: ConfigurationPreset[] = [
  {
    id: 'lip-augmentation',
    label: 'Lip Augmentation Only',
    description: 'Plump lips, natural ratio — a starting point to explore.',
    recommended: true,
    enabledZones: ['lips'],
    parameters: { lips: { philtralShortening: 30, vermilionShow: 40 } },
  },
  {
    id: 'cheek-contour',
    label: 'Cheek Contour',
    description: 'Lifted, bilateral midface volume for a softer contour.',
    enabledZones: ['cheeks'],
    parameters: { cheeks: { volumeMl: 2.5, side: 'bilateral' } },
  },
  {
    id: 'jawline-definition',
    label: 'Jawline Definition',
    description: 'Structured lower-face contour without surgery.',
    enabledZones: ['jaw'],
    parameters: { jaw: { volumeMl: 1.8, definition: 60 } },
  },
  {
    id: 'full-face-balance',
    label: 'Full Face Balance',
    description: 'Moderate volume across lips, cheeks and jaw together.',
    enabledZones: ['lips', 'cheeks', 'jaw'],
    parameters: {
      lips: { philtralShortening: 15, vermilionShow: 15 },
      cheeks: { volumeMl: 2.0 },
      jaw: { volumeMl: 1.2, definition: 40 },
    },
  },
]