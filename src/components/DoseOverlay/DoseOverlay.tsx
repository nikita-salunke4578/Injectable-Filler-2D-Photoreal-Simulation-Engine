import type { SimulationRequestPayload, TreatmentZone } from '../../types/simulation'
import { formatMl } from '../../utils/format'

// Approximate anchor positions for each zone's label, expressed as
// percentages of the image bounding box. These are illustrative only —
// the real engine will position these from detected facial landmarks.
const ZONE_ANCHORS: Record<TreatmentZone, { top: string; left: string }> = {
  lips: { top: '68%', left: '50%' },
  cheeks: { top: '48%', left: '76%' },
  jaw: { top: '82%', left: '28%' },
}

export function DoseOverlay({ payload }: { payload: SimulationRequestPayload[] }) {
  return (
    <div className="pointer-events-none absolute inset-0">
      {payload
        .filter((p) => p.volume > 0)
        .map((p) => (
          <span
            key={p.zone}
            style={{ top: ZONE_ANCHORS[p.zone].top, left: ZONE_ANCHORS[p.zone].left }}
            className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-accent/50 bg-base/80 px-2 py-1 text-xs font-medium tabular-nums text-accent shadow-lg"
          >
            {formatMl(p.volume)}
          </span>
        ))}
    </div>
  )
}
