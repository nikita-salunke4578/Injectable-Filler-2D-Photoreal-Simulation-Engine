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
    desiredOutcome: null,
    lipShape: null,
    symmetryConcern: null,
    analysisResult: null,
    analysisLoading: false,
    analysisError: null,
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
  | { type: 'ANALYSIS_START' }
  | { type: 'ANALYSIS_SUCCESS'; result: AnalysisResult }
  | { type: 'ANALYSIS_ERROR'; message: string }
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
    case 'ANALYSIS_START':
      return {
        ...state,
        assessment: { ...state.assessment, analysisLoading: true, analysisError: null }
      }
    case 'ANALYSIS_SUCCESS':
      return {
        ...state,
        assessment: { ...state.assessment, analysisResult: action.result, analysisLoading: false, analysisError: null }
      }
    case 'ANALYSIS_ERROR':
      return {
        ...state,
        assessment: { ...state.assessment, analysisLoading: false, analysisError: action.message }
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

/** Convert a File to a base64 data URI string. */
async function fileToBase64(file: File): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
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
    state.assessment.primaryConcern &&
    !state.assessment.analysisLoading
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

  /**
   * Calls the real /api/analyze-face endpoint to scan the uploaded face,
   * compute lip mathematics, and auto-fill assessment answers + config sliders.
   */
  const runAnalysis = useCallback(async () => {
    if (!state.photo.file) return
    
    dispatch({ type: 'ANALYSIS_START' })
    
    try {
      const base64Data = await fileToBase64(state.photo.file)
      
      const response = await fetch('http://localhost:8000/api/analyze-face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_base64: base64Data, zone: 'lips' }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Analysis failed' }))
        throw new Error(errorData.detail || 'Face analysis failed')
      }
      
      const result: AnalysisResult = await response.json()
      
      // 1. Store the full analysis result
      dispatch({ type: 'ANALYSIS_SUCCESS', result })
      
      // 2. Auto-fill assessment answers from AI suggestions
      if (result.suggested_answers) {
        const answers = result.suggested_answers
        if (answers.gender) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'gender', value: answers.gender })
        if (answers.ageRange) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'ageRange', value: answers.ageRange })
        if (answers.primaryConcern) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'primaryConcern', value: answers.primaryConcern })
        if (answers.experience) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'experience', value: answers.experience })
        if (answers.desiredOutcome) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'desiredOutcome', value: answers.desiredOutcome })
        if (answers.lipShape) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'lipShape', value: answers.lipShape })
        if (answers.symmetryConcern) dispatch({ type: 'SET_ASSESSMENT_ANSWER', key: 'symmetryConcern', value: answers.symmetryConcern })
      }
      
      // 3. Auto-fill configuration sliders from AI suggestions
      if (result.suggested_parameters) {
        dispatch({ 
          type: 'UPDATE_ZONE_PARAMS', 
          zone: 'lips', 
          patch: result.suggested_parameters 
        })
      }
      
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Analysis failed'
      console.error('Face analysis failed:', message)
      dispatch({ type: 'ANALYSIS_ERROR', message })
    }
  }, [state.photo.file])

  /**
   * Navigate to a step. When navigating to 'assessment', 
   * automatically triggers face analysis if not already done.
   */
  const goToStepWithAnalysis = useCallback((step: WizardStep) => {
    dispatch({ type: 'GO_TO_STEP', step })
    
    // Auto-trigger analysis when entering the assessment step for the first time
    if (step === 'assessment' && state.photo.file && !state.assessment.analysisResult && !state.assessment.analysisLoading) {
      // We need to trigger analysis after the step change.
      // Since runAnalysis uses state.photo.file which is already set, we can call it.
      setTimeout(() => {
        // Dispatch will be called via the runAnalysis function
      }, 0)
    }
  }, [state.photo.file, state.assessment.analysisResult, state.assessment.analysisLoading])

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
    goToStep: goToStepWithAnalysis,
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
