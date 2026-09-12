import clsx from 'clsx'
import { ZONES } from '../../mock/staticData'
import type { TreatmentZone } from '../../types/simulation'

interface ZoneTabsProps {
  activeZone: TreatmentZone
  enabledZones: Record<TreatmentZone, boolean>
  onSelectZone: (zone: TreatmentZone) => void
  onToggleZone: (zone: TreatmentZone, enabled: boolean) => void
}

export function ZoneTabs({ activeZone, enabledZones, onSelectZone, onToggleZone }: ZoneTabsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {ZONES.map((zone) => {
        const isEnabled = enabledZones[zone.id]
        const isActive = activeZone === zone.id
        return (
          <div
            key={zone.id}
            className={clsx(
              'flex items-center gap-3 rounded-lg border px-3 py-2 transition-colors',
              isActive ? 'border-accent/60 bg-accent-soft' : 'border-border bg-surface',
            )}
          >
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => onToggleZone(zone.id, e.target.checked)}
                className="h-3.5 w-3.5 rounded border-border-strong bg-surface-raised accent-[#2fd8a8]"
              />
              <button
                type="button"
                onClick={() => onSelectZone(zone.id)}
                disabled={!isEnabled}
                className={clsx(
                  'text-sm font-medium disabled:cursor-not-allowed disabled:text-ink-faint',
                  isActive ? 'text-accent' : 'text-ink',
                )}
              >
                {zone.label}
              </button>
            </label>
          </div>
        )
      })}
    </div>
  )
}