import clsx from 'clsx'
import { ParameterSlider } from './ParameterSlider'
import { ZONE_VOLUME_LIMITS } from '../../mock/staticData'
import type {
  CheekParameters,
  CheekSide,
  ConfigurationState,
  JawParameters,
  LipEnhancementLevel,
  LipParameters,
  TreatmentZone,
} from '../../types/simulation'

interface ZoneParameterPanelProps {
  zone: TreatmentZone
  configuration: ConfigurationState
  disabled: boolean
  onUpdate: (zone: TreatmentZone, patch: Record<string, unknown>) => void
  onReset: (zone: TreatmentZone) => void
}

const LIP_LEVELS: { id: LipEnhancementLevel; label: string }[] = [
  { id: 'subtle', label: 'Subtle' },
  { id: 'natural', label: 'Natural' },
  { id: 'full', label: 'Full' },
]

const CHEEK_SIDES: { id: CheekSide; label: string }[] = [
  { id: 'left', label: 'Left' },
  { id: 'bilateral', label: 'Bilateral' },
  { id: 'right', label: 'Right' },
]

export function ZoneParameterPanel({ zone, configuration, disabled, onUpdate, onReset }: ZoneParameterPanelProps) {
  const limit = ZONE_VOLUME_LIMITS[zone]

  if (zone === 'lips') {
    const params = configuration.parameters.lips
    return (
      <div className="flex flex-col gap-5">
        <ParameterSlider
          label="Lip volume"
          value={params.volumeMl}
          min={0}
          max={limit}
          disabled={disabled}
          onChange={(v) => onUpdate('lips', { volumeMl: v } satisfies Partial<LipParameters>)}
          onReset={() => onReset('lips')}
        />
        <div>
          <p className="mb-2 text-sm text-ink">Enhancement level</p>
          <SegmentedControl
            options={LIP_LEVELS}
            value={params.enhancementLevel}
            disabled={disabled}
            onChange={(v) => onUpdate('lips', { enhancementLevel: v })}
          />
        </div>
        <ParameterSlider
          label="Upper / lower balance"
          value={params.upperLowerBalance}
          min={-100}
          max={100}
          step={5}
          unit="%"
          disabled={disabled}
          onChange={(v) => onUpdate('lips', { upperLowerBalance: v })}
        />
      </div>
    )
  }

  if (zone === 'cheeks') {
    const params = configuration.parameters.cheeks
    return (
      <div className="flex flex-col gap-5">
        <ParameterSlider
          label="Cheek volume"
          value={params.volumeMl}
          min={0}
          max={limit}
          disabled={disabled}
          onChange={(v) => onUpdate('cheeks', { volumeMl: v } satisfies Partial<CheekParameters>)}
          onReset={() => onReset('cheeks')}
        />
        <div>
          <p className="mb-2 text-sm text-ink">Side</p>
          <SegmentedControl
            options={CHEEK_SIDES}
            value={params.side}
            disabled={disabled}
            onChange={(v) => onUpdate('cheeks', { side: v })}
          />
        </div>
      </div>
    )
  }

  const params = configuration.parameters.jaw
  return (
    <div className="flex flex-col gap-5">
      <ParameterSlider
        label="Jaw volume"
        value={params.volumeMl}
        min={0}
        max={limit}
        disabled={disabled}
        onChange={(v) => onUpdate('jaw', { volumeMl: v } satisfies Partial<JawParameters>)}
        onReset={() => onReset('jaw')}
      />
      <ParameterSlider
        label="Jawline definition"
        value={params.definition}
        min={0}
        max={100}
        step={5}
        unit="%"
        disabled={disabled}
        onChange={(v) => onUpdate('jaw', { definition: v })}
      />
    </div>
  )
}

function SegmentedControl<T extends string>({
  options,
  value,
  disabled,
  onChange,
}: {
  options: { id: T; label: string }[]
  value: T
  disabled?: boolean
  onChange: (value: T) => void
}) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-surface p-1">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          disabled={disabled}
          onClick={() => onChange(option.id)}
          className={clsx(
            'rounded-md px-3 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed',
            value === option.id ? 'bg-accent text-[#04140f]' : 'text-ink-muted hover:text-ink',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
