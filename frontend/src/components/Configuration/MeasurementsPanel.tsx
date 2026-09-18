import { Card } from '../common/Card'
import { ZONES } from '../../mock/staticData'
import { formatCurrencyRange, formatMl } from '../../utils/format'
import { getActiveZones, getEstimatedCostRange, getTotalVolume } from '../../utils/simulationMath'
import type { ConfigurationState } from '../../types/simulation'

export function MeasurementsPanel({ configuration }: { configuration: ConfigurationState }) {
  const activeZones = getActiveZones(configuration)
  const totalVolume = getTotalVolume(configuration)
  const costRange = getEstimatedCostRange(configuration)

  return (
    <Card>
      <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">MEASUREMENTS</p>
      <dl className="flex flex-col gap-2.5 text-sm">
        <Row label="Total volume" value={formatMl(totalVolume)} />
        <Row label="Est. cost" value={formatCurrencyRange(costRange)} />
        <Row label="Active zones" value={`${activeZones.length} / ${ZONES.length}`} />
      </dl>

      {activeZones.length > 0 && (
        <div className="mt-4 border-t border-border pt-3">
          <p className="mb-2 text-xs font-semibold tracking-wide text-ink-faint">PER-ZONE VOLUME</p>
          <dl className="flex flex-col gap-1.5">
            {activeZones.map((zone) => {
              const params = configuration.parameters[zone.id] as any
              const vol = zone.id === 'cheeks'
                ? ((params.lateral_volume_ck1 || 0) + (params.medial_volume_ck2 || 0) + (params.submalar_volume_ck3 || 0))
                : (params.volumeMl || 0)
              return <Row key={zone.id} label={zone.label} value={formatMl(vol)} />
            })}
          </dl>
        </div>
      )}
    </Card>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="font-medium tabular-nums text-ink">{value}</dd>
    </div>
  )
}
