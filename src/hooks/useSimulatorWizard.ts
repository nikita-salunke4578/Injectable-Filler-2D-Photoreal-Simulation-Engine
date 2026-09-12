import { useCallback, useMemo, useReducer } from 'react'
import type {
  AssessmentState,
  ConfigurationState,
  PatientPhotoState,
  SimulationResult,
  SimulationStatus,
  TreatmentZone,
  WizardStep,
  ZoneParameterMap,
} from '../types/simulation'
import { WIZARD_STEPS } from '../mock/staticData'
import { mockSimulationResult } from '../mock/mockSimulationResult'

interface WizardState {
  step: WizardStep
  photo: PatientPhotoState
  assessment: AssessmentState
  configuration: ConfigurationState
  simulationStatus: SimulationStatus
  simulationError: string | null
  result: SimulationResult | null
}

const DEFAULT_PARAMETERS: ZoneParameterMap = {
  lips: { volumeMl: 0, enhancementLevel: 'natural', upperLowerBalance: 0 },
  cheeks: { volumeMl: 0, side: 'bilateral' },
  jaw: { volumeMl: 0, definition: 0 },
}

const initialState: WizardState = {
  step: 'photo',
  photo: { file: null, previewUrl: null, consentGiven: false, captureMethod: null },
  assessment: { ageRange: null, primaryZone: null, experience: null },
  configuration: {
    activeZone: 'lips',
    enabledZones: { lips: true, cheeks: false, jaw: false },
    parameters: DEFAULT_PARAMETERS,
  },
  simulationStatus: 'idle',
  simulationError: null,
  result: null,
}

type Action =
  | { type: 'GO_TO_STEP'; step: WizardStep }
  | { type: 'SET_PHOTO'; file: File; previewUrl: string; method: 'upload' | 'camera' }
  | { type: 'CLEAR_PHOTO' }
  | { type: 'SET_CONSENT'; value: boolean }
  | { type: 'SET_ASSESSMENT'; patch: Partial<AssessmentState> }
  | { type: 'SET_ACTIVE_ZONE'; zone: TreatmentZone }
  | { type: 'TOGGLE_ZONE'; zone: TreatmentZone; enabled: boolean }
  | { type: 'UPDATE_ZONE_PARAMS'; zone: TreatmentZone; patch: Record<string, unknown> }
  | { type: 'RESET_ZONE_PARAMS'; zone: TreatmentZone }
  | { type: 'RESET_ALL_PARAMS' }
  | { type: 'SIMULATION_START' }
  | { type: 'SIMULATION_SUCCESS'; result: SimulationResult }
  | { type: 'SIMULATION_ERROR'; message: string }
  | { type: 'START_OVER' }

function reducer(state: WizardState, action: Action): WizardState {
  switch (action.type) {
    case 'GO_TO_STEP':
      return { ...state, step: action.step }
    case 'SET_PHOTO':
      return {
        ...state,
        photo: {
          ...state.photo,
          file: action.file,
          previewUrl: action.previewUrl,
          captureMethod: action.method,
        },
      }
    case 'CLEAR_PHOTO':
      return { ...state, photo: { ...initialState.photo } }
    case 'SET_CONSENT':
      return { ...state, photo: { ...state.photo, consentGiven: action.value } }
    case 'SET_ASSESSMENT': {
      const next = { ...state.assessment, ...action.patch }
      // Keep configuration's active zone in sync with the chosen primary zone.
      const activeZone = next.primaryZone ?? state.configuration.activeZone
      return {
        ...state,
        assessment: next,
        configuration: {
          ...state.configuration,
          activeZone,
          enabledZones: { ...state.configuration.enabledZones, [activeZone]: true },
        },
      }
    }
    case 'SET_ACTIVE_ZONE':
      return { ...state, configuration: { ...state.configuration, activeZone: action.zone } }
    case 'TOGGLE_ZONE':
      return {
        ...state,
        configuration: {
          ...state.configuration,
          enabledZones: { ...state.configuration.enabledZones, [action.zone]: action.enabled },
        },
      }
    case 'UPDATE_ZONE_PARAMS':
      return {
        ...state,
        configuration: {
          ...state.configuration,
          parameters: {
            ...state.configuration.parameters,
            [action.zone]: { ...state.configuration.parameters[action.zone], ...action.patch },
          },
        },
      }
    case 'RESET_ZONE_PARAMS':
      return {
        ...state,
        configuration: {
          ...state.configuration,
          parameters: { ...state.configuration.parameters, [action.zone]: DEFAULT_PARAMETERS[action.zone] },
        },
      }
    case 'RESET_ALL_PARAMS':
      return { ...state, configuration: { ...state.configuration, parameters: DEFAULT_PARAMETERS } }
    case 'SIMULATION_START':
      return { ...state, simulationStatus: 'loading', simulationError: null }
    case 'SIMULATION_SUCCESS':
      return { ...state, simulationStatus: 'success', result: action.result }
    case 'SIMULATION_ERROR':
      return { ...state, simulationStatus: 'error', simulationError: action.message }
    case 'START_OVER':
      return { ...initialState }
    default:
      return state
  }
}

export function useSimulatorWizard() {
  const [state, dispatch] = useReducer(reducer, initialState)

  const currentStepIndex = useMemo(
    () => WIZARD_STEPS.findIndex((s) => s.id === state.step),
    [state.step],
  )

  const canContinueFromPhoto = Boolean(state.photo.previewUrl && state.photo.consentGiven)
  const canContinueFromAssessment = Boolean(
    state.assessment.ageRange && state.assessment.primaryZone && state.assessment.experience,
  )
  const hasEnabledZone = Object.values(state.configuration.enabledZones).some(Boolean)

  const goToStep = useCallback((step: WizardStep) => dispatch({ type: 'GO_TO_STEP', step }), [])

  const setPhoto = useCallback(
    (file: File, previewUrl: string, method: 'upload' | 'camera') =>
      dispatch({ type: 'SET_PHOTO', file, previewUrl, method }),
    [],
  )
  const clearPhoto = useCallback(() => dispatch({ type: 'CLEAR_PHOTO' }), [])
  const setConsent = useCallback((value: boolean) => dispatch({ type: 'SET_CONSENT', value }), [])

  const setAssessment = useCallback(
    (patch: Partial<AssessmentState>) => dispatch({ type: 'SET_ASSESSMENT', patch }),
    [],
  )

  const setActiveZone = useCallback((zone: TreatmentZone) => dispatch({ type: 'SET_ACTIVE_ZONE', zone }), [])
  const toggleZone = useCallback(
    (zone: TreatmentZone, enabled: boolean) => dispatch({ type: 'TOGGLE_ZONE', zone, enabled }),
    [],
  )
  const updateZoneParams = useCallback(
    (zone: TreatmentZone, patch: Record<string, unknown>) =>
      dispatch({ type: 'UPDATE_ZONE_PARAMS', zone, patch }),
    [],
  )
  const resetZoneParams = useCallback((zone: TreatmentZone) => dispatch({ type: 'RESET_ZONE_PARAMS', zone }), [])
  const resetAllParams = useCallback(() => dispatch({ type: 'RESET_ALL_PARAMS' }), [])

  const runSimulation = useCallback(async () => {
    if (!state.photo.previewUrl) return
    dispatch({ type: 'SIMULATION_START' })
    try {
      const result = await mockSimulationResult(state.photo.previewUrl, state.configuration)
      dispatch({ type: 'SIMULATION_SUCCESS', result })
      dispatch({ type: 'GO_TO_STEP', step: 'preview' })
    } catch {
      dispatch({ type: 'SIMULATION_ERROR', message: 'Simulation failed. Please try again.' })
    }
  }, [state.photo.previewUrl, state.configuration])

  const startOver = useCallback(() => dispatch({ type: 'START_OVER' }), [])

  return {
    state,
    currentStepIndex,
    canContinueFromPhoto,
    canContinueFromAssessment,
    hasEnabledZone,
    goToStep,
    setPhoto,
    clearPhoto,
    setConsent,
    setAssessment,
    setActiveZone,
    toggleZone,
    updateZoneParams,
    resetZoneParams,
    resetAllParams,
    runSimulation,
    startOver,
  }
}

export type SimulatorWizard = ReturnType<typeof useSimulatorWizard>
