import { useState } from 'react'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { ZoneTabs } from './ZoneTabs'
import { ZoneParameterPanel } from './ZoneParameterPanel'
import { MeasurementsPanel } from './MeasurementsPanel'
import { PresetGrid } from './PresetGrid'
import { ZONES } from '../../mock/staticData'
import type { ConfigurationPreset } from '../../mock/presets'
import type { ConfigurationState, TreatmentZone } from '../../types/simulation'

interface ConfigurationProps {
  configuration: ConfigurationState
  onSelectZone: (zone: TreatmentZone) => void
  onToggleZone: (zone: TreatmentZone, enabled: boolean) => void
  onUpdateZoneParams: (zone: TreatmentZone, patch: Record<string, unknown>) => void
  onResetZone: (zone: TreatmentZone) => void
  onResetAll: () => void
}

export function Configuration({
  configuration,
  onSelectZone,
  onToggleZone,
  onUpdateZoneParams,
  onResetZone,
  onResetAll,
}: ConfigurationProps) {
  const [activePresetId, setActivePresetId] = useState<string | null>(null)

  const applyPreset = (preset: ConfigurationPreset) => {
    ZONES.forEach((zone) => onToggleZone(zone.id, preset.enabledZones.includes(zone.id)))
      ; (Object.keys(preset.parameters) as TreatmentZone[]).forEach((zone) => {
        const patch = preset.parameters[zone]
        if (patch) onUpdateZoneParams(zone, patch)
      })
    onSelectZone(preset.enabledZones[0] ?? configuration.activeZone)
    setActivePresetId(preset.id)
  }

  return (
    <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 lg:grid-cols-[1fr_300px]">
      <div className="flex flex-col gap-6">
        <PresetGrid activePresetId={activePresetId} onApply={applyPreset} />

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs font-semibold tracking-wide text-ink-faint">TREATMENT ZONES</p>
          </div>
          <ZoneTabs
            activeZone={configuration.activeZone}
            enabledZones={configuration.enabledZones}
            onSelectZone={onSelectZone}
            onToggleZone={(zone, enabled) => {
              onToggleZone(zone, enabled)
              setActivePresetId(null)
            }}
          />

          <div className="my-5 border-t border-border" />

          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs font-semibold tracking-wide text-ink-faint">PARAMETERS</p>
            <button
              type="button"
              onClick={() => {
                onResetAll()
                setActivePresetId(null)
              }}
              className="text-xs text-ink-muted hover:text-ink"
            >
              Reset
            </button>
          </div>
          <ZoneParameterPanel
            zone={configuration.activeZone}
            configuration={configuration}
            disabled={!configuration.enabledZones[configuration.activeZone]}
            onUpdate={(zone, patch) => {
              onUpdateZoneParams(zone, patch)
              setActivePresetId(null)
            }}
            onReset={onResetZone}
          />
        </Card>
      </div>

      <div className="flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start">
        <MeasurementsPanel configuration={configuration} />
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
    <div className="mx-auto grid max-w-5xl grid-cols-1 gap-3 lg:grid-cols-[1fr_300px]">
      <div />
      <div className="flex flex-col gap-3">
        <Button variant="primary" onClick={onContinue} disabled={disabled} className="w-full">
          Preview results
        </Button>
        <Button variant="secondary" onClick={onBack} className="w-full">
          Back
        </Button>
      </div>
    </div>
  )
}