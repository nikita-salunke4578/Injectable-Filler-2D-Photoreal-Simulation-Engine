import type { ReactNode } from 'react'
import clsx from 'clsx'

type Tone = 'accent' | 'warning' | 'danger' | 'neutral'

const toneClasses: Record<Tone, string> = {
  accent: 'bg-accent-soft text-accent border-accent/30',
  warning: 'bg-warning-soft text-warning border-warning/30',
  danger: 'bg-danger-soft text-danger border-danger/30',
  neutral: 'bg-surface-raised text-ink-muted border-border-strong',
}

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide',
        toneClasses[tone],
      )}
    >
      {children}
    </span>
  )
}
