import { useState } from 'react'
import { ArrowLeft, Droplet } from 'lucide-react'
import { InfoStrip } from '../../components/layout/InfoStrip'
import { Stepper } from '../../components/Stepper/Stepper'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { PhotoUpload } from '../../components/PhotoUpload/PhotoUpload'
import { Consultation } from '../../components/Assessment/Consultation'
import { Configuration, ConfigurationFooter } from '../../components/Configuration/Configuration'
import { SimulationPreview } from '../../components/SimulationPreview/SimulationPreview'
import { useSimulatorWizard } from '../../hooks/useSimulatorWizard'
import { WIZARD_STEPS } from '../../mock/staticData'
import type { WizardStep } from '../../types/simulation'

interface DermalFillerSimulatorProps {
  onBack?: () => void
}

export function DermalFillerSimulator({ onBack }: DermalFillerSimulatorProps) {
  const wizard = useSimulatorWizard()
  const [showDoseOverlay, setShowDoseOverlay] = useState(true)
  const { state } = wizard

  const stepTitle: Record<WizardStep, string> = {
    photo: 'Dermal Filler Simulator',
    assessment: 'Surgical Consultation',
    configure: 'Configure',
    preview: 'Preview',
  }

  return (
    <>
      {/* Contextual sub-header for the simulator */}
      <div className="flex items-center gap-3 border-b border-border px-6 py-3">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="flex h-7 w-7 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
            aria-label="Back to dashboard"
          >
            <ArrowLeft size={15} />
          </button>
        )}
        <span className="text-xs font-semibold tracking-wide text-ink-faint">SIMULATION WIZARD</span>
      </div>
      <InfoStrip showDoseOverlay={showDoseOverlay} onToggleDoseOverlay={setShowDoseOverlay} />

      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <Stepper currentStep={state.step} furthestCompletedIndex={wizard.currentStepIndex - 1} />

        <div className="mx-auto w-full text-center">
          <div className="flex items-center justify-center gap-3">
            <Droplet size={20} className="text-accent" />
            <h1 className="text-2xl font-semibold text-ink">{stepTitle[state.step]}</h1>
            {state.step === 'photo' && <Badge tone="accent">Non-surgical</Badge>}
          </div>
          <p className="mt-1 text-sm text-accent/80">AI Volume Enhancement Preview</p>
        </div>

        {state.step === 'photo' && (
          <>
            <PhotoUpload
              photo={state.photo}
              onPhotoSelected={(file, previewUrl) => wizard.setPhoto(file, previewUrl, 'upload')}
              onClear={wizard.clearPhoto}
              onConsentChange={wizard.setConsent}
            />
            <div className="mx-auto flex w-full max-w-xl justify-end">
              <Button
                variant="primary"
                disabled={!wizard.canContinueFromPhoto}
                onClick={() => wizard.goToStep('assessment')}
              >
                Continue
              </Button>
            </div>
          </>
        )}

        {state.step === 'assessment' && (
          <>
            <Consultation 
              value={state.assessment} 
              onAnswerQuestion={wizard.setAssessmentAnswer}
            />
            <div className="mx-auto flex w-full max-w-3xl items-center justify-between">
              <Button variant="secondary" onClick={() => wizard.goToStep('photo')}>
                Back
              </Button>
              <Button
                variant="primary"
                disabled={!wizard.canContinueFromAssessment}
                onClick={() => wizard.goToStep('configure')}
              >
                Continue to configuration
              </Button>
            </div>
          </>
        )}

        {state.step === 'configure' && (
          <>
            <Configuration
              configuration={state.configuration}
              onSelectZone={wizard.setActiveZone}
              onToggleZone={wizard.toggleZone}
              onUpdateZoneParams={wizard.updateZoneParams}
              onResetZone={wizard.resetZoneParams}
              onResetAll={wizard.resetAllParams}
              onToggleOutline={wizard.toggleOutline}
            />
            <ConfigurationFooter
              onBack={() => wizard.goToStep('assessment')}
              onContinue={wizard.runSimulation}
              disabled={!wizard.hasEnabledZone || state.simulationStatus === 'loading'}
            />
          </>
        )}

        {state.step === 'preview' && (
          <SimulationPreview
            status={state.simulationStatus}
            result={state.result}
            error={state.simulationError}
            onReconfigure={() => wizard.goToStep('configure')}
            onStartOver={wizard.startOver}
            onRetry={wizard.runSimulation}
          />
        )}

        <p className="pt-4 text-center text-xs text-ink-faint">
          {WIZARD_STEPS.length}-step simulation workflow · configuration only, not medical advice
        </p>
      </main>
    </>
  )
}
