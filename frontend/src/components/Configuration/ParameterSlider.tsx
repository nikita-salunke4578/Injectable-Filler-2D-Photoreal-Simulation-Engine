import { RotateCcw } from 'lucide-react'

interface ParameterSliderProps {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit?: string
  disabled?: boolean
  onChange: (value: number) => void
  onReset?: () => void
}

export function ParameterSlider({
  label,
  value,
  min,
  max,
  step = 0.1,
  unit = 'mL',
  disabled = false,
  onChange,
  onReset,
}: ParameterSliderProps) {
  const percent = Math.round(((value - min) / (max - min)) * 100)

  return (
    <div className={disabled ? 'opacity-50' : undefined}>
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm text-ink">{label}</label>
        <div className="flex items-center gap-2">
          <span className="text-sm tabular-nums text-ink-muted">{percent}%</span>
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              disabled={disabled}
              aria-label={`Reset ${label}`}
              className="text-ink-faint hover:text-ink disabled:cursor-not-allowed"
            >
              <RotateCcw size={13} />
            </button>
          )}
        </div>
      </div>
      <input
        type="range"
        className="zone-slider"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
        aria-valuetext={`${value.toFixed(1)}${unit}`}
      />
      <div className="mt-1 flex justify-between text-xs text-ink-faint">
        <span>
          {min.toFixed(1)}
          {unit}
        </span>
        <span>
          {max.toFixed(1)}
          {unit}
        </span>
      </div>
    </div>
  )
}
