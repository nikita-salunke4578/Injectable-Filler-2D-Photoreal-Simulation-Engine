import clsx from 'clsx'
import { Check } from 'lucide-react'
import { CONFIGURATION_PRESETS, type ConfigurationPreset } from '../../mock/presets'

interface PresetGridProps {
  activePresetId: string | null
  onApply: (preset: ConfigurationPreset) => void
}

export function PresetGrid({ activePresetId, onApply }: PresetGridProps) {
  const activePreset = CONFIGURATION_PRESETS.find((p) => p.id === activePresetId)
  const highlighted = activePreset ?? CONFIGURATION_PRESETS.find((p) => p.recommended)!

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3 rounded-lg border border-accent/30 bg-accent-soft px-4 py-3.5">
        <Check size={16} className="mt-0.5 shrink-0 text-accent" />
        <p className="text-sm text-ink">
          <span className="font-semibold text-accent">
            {activePreset ? 'Preset applied: ' : 'Popular preset: '}
            {highlighted.label}
          </span>
          <span className="text-ink-muted"> — {highlighted.description}</span>
        </p>
      </div>

      <div>
        <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">QUICK PRESETS</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {CONFIGURATION_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => onApply(preset)}
              className={clsx(
                'flex flex-col items-start gap-1 rounded-xl border px-4 py-3.5 text-left transition-colors',
                activePresetId === preset.id
                  ? 'border-accent/60 bg-accent-soft'
                  : 'border-border bg-surface hover:border-border-strong',
              )}
            >
              <div className="flex w-full items-center justify-between gap-2">
                <span className="text-sm font-semibold text-ink">{preset.label}</span>
                {preset.recommended && (
                  <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-bold tracking-wide text-accent">
                    REC
                  </span>
                )}
              </div>
              <span className="text-xs text-ink-muted">{preset.description}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}