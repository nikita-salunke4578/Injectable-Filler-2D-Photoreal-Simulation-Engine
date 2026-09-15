import { ArrowLeft, Droplet, User, FolderOpen, ArrowRight } from 'lucide-react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { Button } from '../common/Button'
import { REGION_INFO } from '../../mock/dashboardData'
import type { TreatmentZone } from '../../types/simulation'

interface RegionDetailSectionProps {
  zone: TreatmentZone
  onBack: () => void
  onStartSimulation: () => void
}

export function RegionDetailSection({ zone, onBack, onStartSimulation }: RegionDetailSectionProps) {
  const region = REGION_INFO[zone]

  const statusTone =
    region.status === 'Ready' ? 'accent' as const
    : region.status === 'In Development' ? 'warning' as const
    : 'neutral' as const

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-10">
      {/* Back + heading */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
          aria-label="Back to overview"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <Droplet size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink">
                {region.label}
              </h1>
              <Badge tone={statusTone}>{region.status}</Badge>
            </div>
            <p className="text-sm text-ink-muted">{region.tagline}</p>
          </div>
        </div>
      </div>

      {/* Description card */}
      <Card>
        <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">ABOUT THIS REGION</p>
        <p className="text-sm leading-relaxed text-ink-muted">{region.description}</p>
        <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-ink-faint">
          <span className="inline-flex items-center gap-1.5">
            <User size={12} />
            Owner: {region.owner}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <FolderOpen size={12} />
            {region.backendPath}
          </span>
        </div>
      </Card>

      {/* Two-column: features + pipeline */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Features */}
        <Card>
          <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">PARAMETERS & FEATURES</p>
          <ul className="flex flex-col gap-2">
            {region.features.map((f) => (
              <li
                key={f}
                className="flex items-start gap-2 text-sm text-ink-muted"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent/60" />
                {f}
              </li>
            ))}
          </ul>
        </Card>

        {/* Pipeline */}
        <Card>
          <p className="mb-3 text-xs font-semibold tracking-wide text-ink-faint">SIMULATION PIPELINE</p>
          <ol className="flex flex-col gap-2">
            {region.pipelineSteps.map((step, i) => (
              <li
                key={step}
                className="flex items-center gap-2.5 text-sm text-ink-muted"
              >
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-surface-sunken text-[10px] font-semibold text-ink-faint">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </Card>
      </div>

      {/* Action */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          icon={<ArrowRight size={15} />}
          iconPosition="right"
          onClick={onStartSimulation}
        >
          Start {region.label} Simulation
        </Button>
      </div>
    </div>
  )
}
