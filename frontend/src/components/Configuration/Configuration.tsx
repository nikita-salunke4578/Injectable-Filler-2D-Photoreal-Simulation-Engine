import { ZoneTabs } from './ZoneTabs'
import { ZoneParameterPanel } from './ZoneParameterPanel'
import { MeasurementsPanel } from './MeasurementsPanel'
import { Button } from '../common/Button'
import type { ConfigurationState, TreatmentZone } from '../../types/simulation'

interface ConfigurationProps {
  configuration: ConfigurationState
  onSelectZone: (zone: TreatmentZone) => void
  onToggleZone: (zone: TreatmentZone, enabled: boolean) => void
  onUpdateZoneParams: (zone: TreatmentZone, patch: Record<string, unknown>) => void
  onResetZone: (zone: TreatmentZone) => void
  onResetAll: () => void
  onToggleOutline: (show: boolean) => void
}

export function Configuration({
  configuration,
  onSelectZone,
  onToggleZone,
  onUpdateZoneParams,
  onResetZone,
  onToggleOutline,
}: ConfigurationProps) {

  return (
    <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-8 lg:grid-cols-[1fr_350px]">
      <div className="flex flex-col gap-6">
        <ZoneTabs
          activeZone={configuration.activeZone}
          enabledZones={configuration.enabledZones}
          onSelectZone={onSelectZone}
          onToggleZone={onToggleZone}
        />

        <ZoneParameterPanel
          zone={configuration.activeZone}
          configuration={configuration}
          disabled={!configuration.enabledZones[configuration.activeZone]}
          onUpdate={(zone, patch) => {
            onUpdateZoneParams(zone, patch)
          }}
          onReset={onResetZone}
        />
      </div>

      <div className="flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start">
        <MeasurementsPanel configuration={configuration} />
        
        <div className="mt-4 flex items-center justify-between rounded-xl border border-border bg-surface p-4">
          <div>
            <p className="text-sm font-medium text-ink">Show Before Outline</p>
            <p className="text-xs text-ink-muted">
              {configuration.activeZone === 'cheeks'
                ? 'Display original cheek contours and apex points'
                : configuration.activeZone === 'jaw'
                ? 'Display original jawline and chin contour'
                : 'Display a dotted line of original lips'}
            </p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input 
              type="checkbox" 
              className="peer sr-only" 
              checked={configuration.showOutline}
              onChange={(e) => onToggleOutline(e.target.checked)} 
            />
            <div className="peer h-6 w-11 rounded-full bg-border after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-accent peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none" />
          </label>
        </div>
        
        <p className="text-xs text-ink-faint">
          These are simulation parameters, not medically authoritative dosage guidance.
        </p>
      </div>
    </div>
  )
}

export function ConfigurationFooter({
  onBack,
  onContinue,
  disabled,
}: {
  onBack: () => void
  onContinue: () => void
  disabled: boolean
}) {
  return (
    <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-8 lg:grid-cols-[1fr_350px]">
      <div />
      <div className="flex flex-col gap-3">
        <Button variant="primary" onClick={onContinue} disabled={disabled} className="w-full">
          Preview Results →
        </Button>
        <button onClick={onBack} className="w-full text-sm text-ink-muted hover:text-ink">
          ← Back to Assessment
        </button>
      </div>
    </div>
  )
}