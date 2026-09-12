import { Toggle } from '../common/Toggle'
import { TREATMENT_INFO } from '../../mock/staticData'

interface InfoStripProps {
  showDoseOverlay: boolean
  onToggleDoseOverlay: (value: boolean) => void
}

export function InfoStrip({ showDoseOverlay, onToggleDoseOverlay }: InfoStripProps) {
  return (
    <div className="border-b border-border">
      <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <InfoCell label="Onset" value={TREATMENT_INFO.onset} />
        <InfoCell label="Lasts" value={TREATMENT_INFO.lasts} />
        <InfoCell label="Reversible" value={TREATMENT_INFO.reversible} />
      </div>
      <div className="flex items-center justify-between border-t border-border px-6 py-3">
        <span className="text-sm text-ink-muted">Show dose / unit overlay</span>
        <Toggle checked={showDoseOverlay} onChange={onToggleDoseOverlay} label="Show dose and unit overlay" />
      </div>
      <p className="border-t border-dashed border-border px-6 py-2 text-xs text-ink-faint">
        Note: injectable effects are temporary. Ask your surgeon about maintenance over time.
      </p>
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-6 py-3">
      <div className="text-sm font-semibold text-ink">{label}</div>
      <div className="mt-0.5 text-sm text-ink-muted">{value}</div>
    </div>
  )
}
