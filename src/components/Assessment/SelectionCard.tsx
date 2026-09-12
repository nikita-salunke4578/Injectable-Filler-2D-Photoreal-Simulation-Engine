import clsx from 'clsx'

interface SelectionCardProps {
  label: string
  helper: string
  selected: boolean
  onSelect: () => void
}

export function SelectionCard({ label, helper, selected, onSelect }: SelectionCardProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      className={clsx(
        'flex flex-col items-start gap-1 rounded-xl border px-4 py-3.5 text-left transition-colors',
        selected
          ? 'border-accent/60 bg-accent-soft'
          : 'border-border bg-surface hover:border-border-strong',
      )}
    >
      <span className={clsx('text-sm font-semibold', selected ? 'text-accent' : 'text-ink')}>{label}</span>
      <span className="text-xs text-ink-muted">{helper}</span>
    </button>
  )
}
