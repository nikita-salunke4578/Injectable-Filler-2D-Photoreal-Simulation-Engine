import { Check } from 'lucide-react'
import clsx from 'clsx'
import type { WizardStep } from '../../types/simulation'
import { WIZARD_STEPS } from '../../mock/staticData'

interface StepperProps {
  currentStep: WizardStep
  furthestCompletedIndex: number
  onStepClick?: (step: WizardStep) => void
}

export function Stepper({ currentStep, furthestCompletedIndex, onStepClick }: StepperProps) {
  const currentIndex = WIZARD_STEPS.findIndex((s) => s.id === currentStep)

  return (
    <ol className="flex items-center justify-center gap-2" aria-label="Simulation progress">
      {WIZARD_STEPS.map((step, index) => {
        const isComplete = index < currentIndex || index <= furthestCompletedIndex
        const isCurrent = step.id === currentStep
        const isClickable = onStepClick && (isComplete || isCurrent)

        return (
          <li key={step.id} className="flex items-center gap-2">
            <button
              type="button"
              disabled={!isClickable}
              onClick={() => isClickable && onStepClick?.(step.id)}
              aria-current={isCurrent ? 'step' : undefined}
              className={clsx(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isCurrent && 'border border-accent/40 bg-accent-soft text-accent',
                !isCurrent && isComplete && 'text-accent hover:bg-surface-raised',
                !isCurrent && !isComplete && 'text-ink-faint',
                isClickable && !isCurrent && 'cursor-pointer',
                !isClickable && 'cursor-default',
              )}
            >
              <span
                className={clsx(
                  'flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold',
                  isCurrent && 'bg-accent text-[#04140f]',
                  !isCurrent && isComplete && 'bg-accent/20 text-accent',
                  !isCurrent && !isComplete && 'bg-surface-raised text-ink-faint',
                )}
              >
                {isComplete && !isCurrent ? <Check size={12} /> : step.order}
              </span>
              {step.label}
            </button>
            {index < WIZARD_STEPS.length - 1 && <span className="h-px w-8 bg-border-strong" aria-hidden="true" />}
          </li>
        )
      })}
    </ol>
  )
}
