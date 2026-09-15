import { useState, useRef, useCallback } from 'react'
import ReactCrop, { type Crop, type PixelCrop, centerCrop, makeAspectCrop } from 'react-image-crop'
import 'react-image-crop/dist/ReactCrop.css'
import { Check, X } from 'lucide-react'
import { Button } from '../common/Button'

interface ImageCropperProps {
  imageSrc: string
  onCropComplete: (croppedFile: File, previewUrl: string) => void
  onCancel: () => void
}

function centerAspectCrop(mediaWidth: number, mediaHeight: number, aspect: number) {
  return centerCrop(
    makeAspectCrop(
      {
        unit: '%',
        width: 90,
      },
      aspect,
      mediaWidth,
      mediaHeight,
    ),
    mediaWidth,
    mediaHeight,
  )
}

export function ImageCropper({ imageSrc, onCropComplete, onCancel }: ImageCropperProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const [crop, setCrop] = useState<Crop>()
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>()

  const onImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget
    setCrop(centerAspectCrop(width, height, 4 / 5)) // Default aspect ratio close to portrait
  }, [])

  const handleConfirm = async () => {
    if (!completedCrop || !imgRef.current) return

    const image = imgRef.current
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const scaleX = image.naturalWidth / image.width
    const scaleY = image.naturalHeight / image.height
    const pixelRatio = window.devicePixelRatio

    canvas.width = completedCrop.width * scaleX * pixelRatio
    canvas.height = completedCrop.height * scaleY * pixelRatio

    ctx.scale(pixelRatio, pixelRatio)
    ctx.imageSmoothingQuality = 'high'

    const cropX = completedCrop.x * scaleX
    const cropY = completedCrop.y * scaleY
    const cropWidth = completedCrop.width * scaleX
    const cropHeight = completedCrop.height * scaleY

    ctx.drawImage(
      image,
      cropX,
      cropY,
      cropWidth,
      cropHeight,
      0,
      0,
      cropWidth,
      cropHeight,
    )

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          console.error('Canvas is empty')
          return
        }
        const previewUrl = URL.createObjectURL(blob)
        const file = new File([blob], 'cropped_image.jpg', { type: 'image/jpeg', lastModified: Date.now() })
        onCropComplete(file, previewUrl)
      },
      'image/jpeg',
      0.95,
    )
  }

  // Calculate actual pixel dimensions of the current crop based on natural image size
  const actualWidth = completedCrop && imgRef.current
    ? Math.round(completedCrop.width * (imgRef.current.naturalWidth / imgRef.current.width))
    : 0
  const actualHeight = completedCrop && imgRef.current
    ? Math.round(completedCrop.height * (imgRef.current.naturalHeight / imgRef.current.height))
    : 0

  return (
    <div className="flex w-full flex-col items-center gap-6 rounded-2xl border border-border bg-surface-raised p-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-ink">Crop your photo</h3>
        <p className="mt-1 text-sm text-ink-muted">
          Adjust the frame to focus on the facial region.
        </p>
      </div>

      <div className="relative max-h-[60vh] w-full overflow-auto rounded-lg bg-surface-sunken p-4">
        <ReactCrop
          crop={crop}
          onChange={(_, percentCrop) => setCrop(percentCrop)}
          onComplete={(c) => setCompletedCrop(c)}
          className="mx-auto flex justify-center"
        >
          <img
            ref={imgRef}
            alt="Crop me"
            src={imageSrc}
            onLoad={onImageLoad}
            className="max-h-[50vh] object-contain"
            style={{ maxWidth: '100%' }}
          />
        </ReactCrop>
      </div>

      {completedCrop && (
        <div className="text-sm font-medium text-ink-muted">
          Final dimensions: <span className="text-accent">{actualWidth} &times; {actualHeight} px</span>
        </div>
      )}

      <div className="flex gap-4">
        <Button variant="secondary" onClick={onCancel} icon={<X size={16} />}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleConfirm}
          disabled={!completedCrop?.width || !completedCrop?.height}
          icon={<Check size={16} />}
        >
          Confirm Crop
        </Button>
      </div>
    </div>
  )
}
