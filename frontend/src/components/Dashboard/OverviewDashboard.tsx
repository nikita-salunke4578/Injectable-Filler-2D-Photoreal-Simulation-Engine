import { Droplet, Shield } from 'lucide-react'
import { RegionDashboard } from './RegionDashboard'
import { REGION_INFO, REGION_ORDER } from '../../mock/dashboardData'
import type { TreatmentZone } from '../../types/simulation'

interface OverviewDashboardProps {
  onNavigateToRegion: (zone: TreatmentZone) => void
}

export function OverviewDashboard({ onNavigateToRegion }: OverviewDashboardProps) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
      {/* Hero / summary */}
      <div className="text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-accent-soft text-accent">
          <Droplet size={22} />
        </div>
        <h1 className="font-display text-2xl font-semibold text-ink">
          Filler Simulation Engine
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-ink-muted">
          2D image-based facial simulation supporting three treatment regions.
          Select a region below to inspect its status, parameters, and pipeline,
          or use the navigation above to jump directly.
        </p>
      </div>

      {/* Region cards grid */}
      <div>
        <p className="mb-4 text-xs font-semibold tracking-wide text-ink-faint">
          TREATMENT REGIONS
        </p>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {REGION_ORDER.map((id) => (
            <RegionDashboard
              key={id}
              region={REGION_INFO[id]}
              onNavigate={onNavigateToRegion}
            />
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 rounded-lg border border-border bg-surface px-4 py-3.5">
        <Shield size={16} className="mt-0.5 shrink-0 text-ink-faint" />
        <p className="text-xs leading-relaxed text-ink-faint">
          This application is a visualization and simulation tool.
          It does not provide medical diagnosis, treatment recommendations, or dosage guidance.
          Simulation values are application parameters, not injection instructions.
          Results do not guarantee real-world outcomes. Consult a qualified medical professional.
        </p>
      </div>
    </div>
  )
}
