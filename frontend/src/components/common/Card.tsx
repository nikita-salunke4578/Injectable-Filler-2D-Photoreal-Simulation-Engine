import type { HTMLAttributes } from 'react'
import clsx from 'clsx'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean
  raised?: boolean
}

export function Card({ padded = true, raised = false, className, children, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl border border-border',
        raised ? 'bg-surface-raised' : 'bg-surface',
        padded && 'p-5',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  )
}
