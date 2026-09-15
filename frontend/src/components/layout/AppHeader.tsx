import { ArrowLeft, Droplet } from 'lucide-react'
import clsx from 'clsx'
import type { DashboardSection } from '../../mock/dashboardData'

interface AppHeaderProps {
  activeSection: DashboardSection
  onSectionChange: (section: DashboardSection) => void
}

const NAV_ITEMS: { id: DashboardSection; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'lips', label: 'Lips' },
  { id: 'cheeks', label: 'Cheeks' },
  { id: 'jaw', label: 'Jaw' },
]

export function AppHeader({ activeSection, onSectionChange }: AppHeaderProps) {
  return (
    <header className="border-b border-border">
      <div className="flex items-center gap-4 px-6 py-4">
        <button
          type="button"
          aria-label="Back"
          onClick={() => onSectionChange('overview')}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="flex items-center gap-2">
          <Droplet size={16} className="text-accent" />
          <span className="font-display text-sm font-semibold text-ink">
            Filler Simulation Engine
          </span>
        </div>
      </div>

      {/* Navigation tabs */}
      <nav className="flex gap-1 overflow-x-auto px-6" aria-label="Treatment region navigation">
        {NAV_ITEMS.map((item) => {
          const isActive = activeSection === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSectionChange(item.id)}
              className={clsx(
                'relative whitespace-nowrap px-4 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'text-accent'
                  : 'text-ink-muted hover:text-ink',
              )}
            >
              {item.label}
              {/* Active indicator bar */}
              {isActive && (
                <span className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-accent" />
              )}
            </button>
          )
        })}
      </nav>
    </header>
  )
}
