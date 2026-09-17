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
  AnalysisResult,
} from '../types/simulation'
import { WIZARD_STEPS } from '../mock/staticData'
import { runSimulationApi } from '../mock/mockSimulationResult'

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
  lips: { philtralShortening: 0, vermilionShow: 0, cupidsBow: 0, philtralColumn: 0, dentalShow: 0 },
  cheeks: { volumeMl: 0, side: 'bilateral' },
  jaw: { volumeMl: 0, definition: 0 },
}

const initialState: WizardState = {
  step: 'photo',
  photo: { file: null, previewUrl: null, consentGiven: false, captureMethod: null },
  assessment: { 
    gender: null,
    ageRange: null, 
    primaryConcern: null, 
    experience: null, 
    analysisResult: null
  },
  configuration: {
    activeZone: 'lips',
    enabledZones: { lips: true, cheeks: false, jaw: false },
    parameters: DEFAULT_PARAMETERS,
    showOutline: false,
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
  | { type: 'TOGGLE_OUTLINE'; show: boolean }
  | { type: 'SIMULATION_START' }
  | { type: 'SIMULATION_SUCCESS'; result: SimulationResult }
  | { type: 'SIMULATION_ERROR'; message: string }
  | { type: 'START_OVER' }
  | { type: 'ANALYSIS_SUCCESS'; result: AnalysisResult }
  | { type: 'SET_ASSESSMENT_ANSWER'; key: string; value: string }

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
      return {
        ...state,
        assessment: next,
      }
    }
    case 'ANALYSIS_SUCCESS':
      return {
        ...state,
        assessment: { ...state.assessment, analysisResult: action.result }
      }
    case 'SET_ASSESSMENT_ANSWER':
      return {
        ...state,
        assessment: { 
          ...state.assessment, 
          [action.key]: action.value 
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
    case 'TOGGLE_OUTLINE':
      return { ...state, configuration: { ...state.configuration, showOutline: action.show } }
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
    state.assessment.gender && 
    state.assessment.ageRange && 
    state.assessment.primaryConcern
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

  const setAssessmentAnswer = useCallback(
    (key: string, value: string) => dispatch({ type: 'SET_ASSESSMENT_ANSWER', key, value }),
    []
  )

  const runAnalysis = useCallback(async () => {
    if (!state.photo.file) return
    try {
      // Simulate network request to AI backend
      await new Promise((resolve) => setTimeout(resolve, 1500))
      
      const mockedResult = {
        gender: 'female',
        ageRange: '20-30',
        primaryConcern: 'long-upper-lip',
        recommendation: {
          philtralShortening: 45,
          vermilionShow: 35,
          cupidsBow: 20,
          philtralColumn: 15,
          dentalShow: 30
        }
      }

      dispatch({ type: 'ANALYSIS_SUCCESS', result: mockedResult as any })
      
      // Auto-fill the assessment answers
      dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'gender', value: mockedResult.gender })
      dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'ageRange', value: mockedResult.ageRange })
      dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'primaryConcern', value: mockedResult.primaryConcern })
      
      // Auto-fill the sliders based on the face scan
      dispatch({ 
        type: 'UPDATE_ZONE_PARAMS', 
        zone: state.configuration.activeZone, 
        patch: mockedResult.recommendation
      })
      
    } catch (e) {
      console.error("Analysis failed", e)
    }
  }, [state.photo.file, state.configuration.activeZone])

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
  const toggleOutline = useCallback((show: boolean) => dispatch({ type: 'TOGGLE_OUTLINE', show }), [])

  const runSimulation = useCallback(async () => {
    if (!state.photo.file) return
    dispatch({ type: 'SIMULATION_START' })
    try {
      const result = await runSimulationApi(state.photo.file, state.configuration)
      dispatch({ type: 'SIMULATION_SUCCESS', result })
      dispatch({ type: 'GO_TO_STEP', step: 'preview' })
    } catch {
      dispatch({ type: 'SIMULATION_ERROR', message: 'Simulation failed. Please try again.' })
    }
  }, [state.photo.file, state.configuration])

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
    setAssessmentAnswer,
    runAnalysis,
    setActiveZone,
    toggleZone,
    updateZoneParams,
    resetZoneParams,
    resetAllParams,
    toggleOutline,
    runSimulation,
    startOver,
  }
}

export type SimulatorWizard = ReturnType<typeof useSimulatorWizard>
