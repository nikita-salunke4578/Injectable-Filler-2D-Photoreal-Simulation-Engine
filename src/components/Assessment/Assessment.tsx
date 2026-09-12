import { SelectionCard } from './SelectionCard'
import { AGE_RANGES, EXPERIENCE_LEVELS, ZONES } from '../../mock/staticData'
import type { AssessmentState } from '../../types/simulation'

interface AssessmentProps {
  value: AssessmentState
  onChange: (patch: Partial<AssessmentState>) => void
}

export function Assessment({ value, onChange }: AssessmentProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <fieldset>
        <legend className="mb-3 text-sm font-semibold text-ink">Age range</legend>
        <div role="radiogroup" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {AGE_RANGES.map((option) => (
            <SelectionCard
              key={option.id}
              label={option.label}
              helper={option.helper}
              selected={value.ageRange === option.id}
              onSelect={() => onChange({ ageRange: option.id })}
            />
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="mb-3 text-sm font-semibold text-ink">Primary treatment zone</legend>
        <div role="radiogroup" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {ZONES.map((zone) => (
            <SelectionCard
              key={zone.id}
              label={zone.label}
              helper={zone.description}
              selected={value.primaryZone === zone.id}
              onSelect={() => onChange({ primaryZone: zone.id })}
            />
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="mb-3 text-sm font-semibold text-ink">Filler experience</legend>
        <div role="radiogroup" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {EXPERIENCE_LEVELS.map((option) => (
            <SelectionCard
              key={option.id}
              label={option.label}
              helper={option.helper}
              selected={value.experience === option.id}
              onSelect={() => onChange({ experience: option.id })}
            />
          ))}
        </div>
      </fieldset>

      <p className="text-xs text-ink-faint">
        These selections configure the simulation only. They are not a medical diagnosis or treatment
        recommendation.
      </p>
    </div>
  )
}
