import { ArrowLeft } from 'lucide-react'

export function AppHeader() {
  return (
    <header className="flex items-center gap-4 border-b border-border px-6 py-4">
      <button
        type="button"
        aria-label="Back"
        className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
      >
        <ArrowLeft size={18} />
      </button>
      <span className="font-display text-sm font-semibold text-ink">Filler Simulation Engine</span>
    </header>
  )
}
