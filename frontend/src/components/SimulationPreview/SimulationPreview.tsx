import { useState } from 'react'
import type { ReactNode } from 'react'
import { AlertTriangle, Columns2, Download, RefreshCcw, Share2 } from 'lucide-react'
import { Card } from '../common/Card'
import { Button } from '../common/Button'
import { Toggle } from '../common/Toggle'
import { BeforeAfterSlider } from './BeforeAfterSlider'
import { DoseOverlay } from '../DoseOverlay/DoseOverlay'
import { formatCurrencyRange, formatMl } from '../../utils/format'
import type { SimulationResult, SimulationStatus } from '../../types/simulation'

interface SimulationPreviewProps {
  status: SimulationStatus
  result: SimulationResult | null
  error: string | null
  onReconfigure: () => void
  onStartOver: () => void
  onRetry: () => void
}

export function SimulationPreview({ status, result, error, onReconfigure, onStartOver, onRetry }: SimulationPreviewProps) {
  const [showDoseOverlay, setShowDoseOverlay] = useState(true)
  const [sideBySide, setSideBySide] = useState(false)

  if (status === 'loading') {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center gap-4 py-16 text-center">
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        <p className="text-sm text-ink-muted">Generating your simulation preview…</p>
      </div>
    )
  }

  if (status === 'error' || !result) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
        <AlertTriangle size={28} className="text-danger" />
        <p className="text-sm text-ink">{error ?? 'No simulation result available yet.'}</p>
        <Button variant="primary" onClick={onRetry}>
          Try again
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Columns2 size={16} className="text-ink-muted" />
          <span className="text-sm text-ink-muted">Side-by-side view</span>
          <Toggle checked={sideBySide} onChange={setSideBySide} label="Toggle side-by-side view" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-ink-muted">Dose / unit overlay</span>
          <Toggle checked={showDoseOverlay} onChange={setShowDoseOverlay} label="Toggle dose overlay" />
        </div>
      </div>

      {sideBySide ? (
        <div className="grid grid-cols-2 gap-3">
          <Labeled label="Before">
            <img src={result.beforeImageUrl} alt="Original photo" className="aspect-[4/3] w-full rounded-xl object-cover" />
          </Labeled>
          <Labeled label="After">
            <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl">
              <img src={result.afterImageUrl} alt="Simulated result" className="h-full w-full object-cover" />
              {showDoseOverlay && <DoseOverlay payload={result.requestPayload} />}
            </div>
          </Labeled>
        </div>
      ) : (
        <BeforeAfterSlider
          beforeSrc={result.beforeImageUrl}
          afterSrc={result.afterImageUrl}
          overlay={showDoseOverlay ? <DoseOverlay payload={result.requestPayload} /> : undefined}
        />
      )}

      <Card>
        <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">SIMULATION SUMMARY</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Total volume" value={formatMl(result.totalVolumeMl)} />
          <Stat label="Est. cost" value={formatCurrencyRange(result.estimatedCostUsd)} />
          <Stat label="Zones treated" value={String(result.requestPayload.length)} />
          <Stat label="Generated" value={new Date(result.generatedAt).toLocaleTimeString()} />
        </div>
      </Card>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <Button variant="secondary" icon={<RefreshCcw size={15} />} onClick={onReconfigure}>
            Reconfigure
          </Button>
          <Button variant="ghost" onClick={onStartOver}>
            Start new simulation
          </Button>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" icon={<Share2 size={15} />}>
            Share
          </Button>
          <Button variant="primary" icon={<Download size={15} />}>
            Download
          </Button>
        </div>
      </div>

      <p className="rounded-lg border border-border bg-surface px-4 py-3 text-xs text-ink-faint">
        {result.disclaimer} This simulation is for educational and planning purposes only — consult a
        qualified medical professional before any treatment decision.
      </p>
    </div>
  )
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium text-ink-muted">{label}</p>
      {children}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-ink-muted">{label}</p>
      <p className="mt-0.5 text-sm font-semibold tabular-nums text-ink">{value}</p>
    </div>
  )
}
