import { useCallback, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { Camera, ImagePlus, ShieldCheck, X } from 'lucide-react'
import clsx from 'clsx'
import { Button } from '../common/Button'
import type { PatientPhotoState } from '../../types/simulation'
import { formatBytes } from '../../utils/format'

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_SIZE_BYTES = 10 * 1024 * 1024

interface PhotoUploadProps {
  photo: PatientPhotoState
  onPhotoSelected: (file: File, previewUrl: string) => void
  onClear: () => void
  onConsentChange: (value: boolean) => void
}

export function PhotoUpload({ photo, onPhotoSelected, onClear, onConsentChange }: PhotoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateAndUse = useCallback(
    (file: File | undefined) => {
      if (!file) return
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError('Unsupported format. Please use JPG, PNG or WebP.')
        return
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError(`Image is too large (${formatBytes(file.size)}). Max size is 10MB.`)
        return
      }
      setError(null)
      const previewUrl = URL.createObjectURL(file)
      onPhotoSelected(file, previewUrl)
    },
    [onPhotoSelected],
  )

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    validateAndUse(event.target.files?.[0])
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    validateAndUse(event.dataTransfer.files?.[0])
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-6">
      <label className="flex w-full cursor-pointer items-start gap-3 rounded-lg border border-border bg-surface px-4 py-3.5">
        <input
          type="checkbox"
          checked={photo.consentGiven}
          onChange={(e) => onConsentChange(e.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 rounded border-border-strong bg-surface-raised accent-[#2fd8a8]"
        />
        <span className="text-sm text-ink-muted">
          I consent to this photo being processed for a simulated treatment preview. Images are processed
          in this browser session and are not uploaded without explicit consent.
        </span>
      </label>

      {!photo.previewUrl ? (
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={clsx(
            'flex w-full flex-col items-center gap-4 rounded-2xl border-2 border-dashed px-8 py-14 text-center transition-colors',
            isDragging ? 'border-accent bg-accent-soft' : 'border-border-strong bg-surface-raised',
          )}
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-surface text-ink-muted">
            <ImagePlus size={22} />
          </div>
          <div>
            <p className="font-medium text-ink">Upload a patient photo</p>
            <p className="mt-1 text-sm text-ink-muted">JPG, PNG, or WebP — max 10MB</p>
            <p className="text-sm text-ink-muted">Min 400×400px, front-facing, even lighting</p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button
              variant="secondary"
              icon={<ImagePlus size={16} />}
              onClick={() => inputRef.current?.click()}
            >
              Upload image
            </Button>

          </div>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            className="hidden"
            onChange={handleInputChange}
          />
          {error && <p className="text-sm text-danger">{error}</p>}
        </div>
      ) : (
        <div className="w-full overflow-hidden rounded-2xl border border-border bg-surface-raised">
          <div className="relative">
            <img src={photo.previewUrl} alt="Uploaded patient reference" className="max-h-96 w-full object-cover" />
            <button
              type="button"
              onClick={onClear}
              aria-label="Remove photo"
              className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-base/80 text-ink hover:bg-base"
            >
              <X size={16} />
            </button>
          </div>
          <div className="flex items-center gap-2 border-t border-border px-4 py-3 text-sm text-ink-muted">
            <ShieldCheck size={16} className="text-accent" />
            Photo captured. Nothing has been uploaded to a server.
          </div>
        </div>
      )}

      <p className="text-center text-xs text-ink-faint">
        Use a front-facing photo in even, natural lighting for the most accurate simulation.
      </p>
    </div>
  )
}
