import { useCallback, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { GripVertical } from 'lucide-react'

interface BeforeAfterSliderProps {
  beforeSrc: string
  afterSrc: string
  overlay?: ReactNode
}

export function BeforeAfterSlider({ beforeSrc, afterSrc, overlay }: BeforeAfterSliderProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState(50)
  const [dragging, setDragging] = useState(false)

  const updateFromClientX = useCallback((clientX: number) => {
    const el = containerRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const pct = ((clientX - rect.left) / rect.width) * 100
    setPosition(Math.min(100, Math.max(0, pct)))
  }, [])

  return (
    <div
      ref={containerRef}
      className="relative aspect-[4/3] w-full select-none overflow-hidden rounded-xl bg-surface-sunken"
      onMouseMove={(e) => dragging && updateFromClientX(e.clientX)}
      onMouseUp={() => setDragging(false)}
      onMouseLeave={() => setDragging(false)}
      onTouchMove={(e) => updateFromClientX(e.touches[0].clientX)}
    >
      <img src={afterSrc} alt="Simulated result" className="absolute inset-0 h-full w-full object-cover" />
      <div
        className="absolute inset-0"
        style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
      >
        <img src={beforeSrc} alt="Original photo" className="absolute inset-0 h-full w-full object-cover" />
      </div>
      {overlay}

      <div className="absolute inset-y-0 flex items-center" style={{ left: `${position}%` }}>
        <div
          role="slider"
          aria-label="Before/after comparison position"
          aria-valuenow={Math.round(position)}
          aria-valuemin={0}
          aria-valuemax={100}
          tabIndex={0}
          onMouseDown={() => setDragging(true)}
          onTouchStart={() => setDragging(true)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft') setPosition((p) => Math.max(0, p - 5))
            if (e.key === 'ArrowRight') setPosition((p) => Math.min(100, p + 5))
          }}
          className="flex h-9 w-9 -translate-x-1/2 cursor-ew-resize items-center justify-center rounded-full border-2 border-accent bg-base shadow-lg"
        >
          <GripVertical size={16} className="text-accent" />
        </div>
        <div className="absolute h-full w-0.5 -translate-x-1/2 bg-accent" />
      </div>

      <span className="absolute left-3 top-3 rounded-md bg-base/70 px-2 py-1 text-xs font-medium text-ink-muted">
        Before
      </span>
      <span className="absolute right-3 top-3 rounded-md bg-base/70 px-2 py-1 text-xs font-medium text-accent">
        After
      </span>
    </div>
  )
}
