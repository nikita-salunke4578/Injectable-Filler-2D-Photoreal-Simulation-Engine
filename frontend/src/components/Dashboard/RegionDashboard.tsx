import { Droplet, User, FolderOpen, ChevronRight } from 'lucide-react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import type { RegionInfo } from '../../mock/dashboardData'
import type { TreatmentZone } from '../../types/simulation'

interface RegionDashboardProps {
  region: RegionInfo
  onNavigate: (zone: TreatmentZone) => void
}

export function RegionDashboard({ region, onNavigate }: RegionDashboardProps) {
  const statusTone =
    region.status === 'Ready' ? 'accent' as const
    : region.status === 'In Development' ? 'warning' as const
    : 'neutral' as const

  return (
    <Card className="group flex flex-col gap-4 transition-all duration-200 hover:border-border-strong">
      {/* Header row */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <Droplet size={18} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-ink">{region.label}</h3>
            <p className="text-sm text-ink-muted">{region.tagline}</p>
          </div>
        </div>
        <Badge tone={statusTone}>{region.status}</Badge>
      </div>

      {/* Description */}
      <p className="text-sm leading-relaxed text-ink-muted">{region.description}</p>

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-ink-faint">
        <span className="inline-flex items-center gap-1.5">
          <User size={12} />
          {region.owner}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <FolderOpen size={12} />
          {region.backendPath}
        </span>
      </div>

      {/* Features */}
      <div>
        <p className="mb-2 text-xs font-semibold tracking-wide text-ink-faint">PARAMETERS & FEATURES</p>
        <ul className="flex flex-wrap gap-2">
          {region.features.map((f) => (
            <li
              key={f}
              className="rounded-md border border-border bg-surface-sunken px-2 py-1 text-xs text-ink-muted"
            >
              {f}
            </li>
          ))}
        </ul>
      </div>

      {/* Navigate button */}
      <button
        type="button"
        onClick={() => onNavigate(region.id)}
        className="mt-auto inline-flex items-center gap-1.5 self-end rounded-lg px-3 py-2 text-sm font-medium text-accent transition-colors hover:bg-accent-soft"
      >
        View details
        <ChevronRight size={14} />
      </button>
    </Card>
  )
}
