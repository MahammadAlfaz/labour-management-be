import { type ChangeEvent, useRef, useState } from 'react'
import { ApiError } from '../lib/apiClient'
import { UsersIcon } from './icons'
import type { ComponentType, SVGProps } from 'react'

export default function PhotoUploader({
  photoUrl,
  onUpload,
  onRemove,
  isUploading,
  isRemoving,
  label = 'Photo',
  PlaceholderIcon = UsersIcon,
}: {
  photoUrl: string | null
  onUpload: (file: File) => Promise<unknown>
  onRemove: () => Promise<unknown>
  isUploading: boolean
  isRemoving: boolean
  label?: string
  PlaceholderIcon?: ComponentType<SVGProps<SVGSVGElement>>
}) {
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setError(null)
    const objectUrl = URL.createObjectURL(file)
    setPreview(objectUrl)
    try {
      await onUpload(file)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not upload photo')
    } finally {
      URL.revokeObjectURL(objectUrl)
      setPreview(null)
    }
  }

  const displayUrl = preview ?? photoUrl
  const busy = isUploading || isRemoving
  const verb = photoUrl ? `Change ${label.toLowerCase()}` : `Add ${label.toLowerCase()}`

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100">
        {displayUrl ? (
          <img src={displayUrl} alt="" className="h-full w-full object-cover" />
        ) : (
          <PlaceholderIcon className="h-8 w-8 text-slate-400" />
        )}
      </div>

      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-slate-700">{isUploading ? 'Uploading…' : verb}</p>
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          <button
            type="button"
            disabled={busy}
            onClick={() => cameraInputRef.current?.click()}
            className="cursor-pointer text-sm font-medium text-brand-600 transition-colors active:text-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Take photo
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => fileInputRef.current?.click()}
            className="cursor-pointer text-sm font-medium text-brand-600 transition-colors active:text-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Choose file
          </button>
          {photoUrl && (
            <button
              type="button"
              disabled={busy}
              onClick={() => onRemove()}
              className="cursor-pointer text-sm font-medium text-rose-600 transition-colors active:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isRemoving ? 'Removing…' : 'Remove'}
            </button>
          )}
        </div>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>

      {/* capture forces the camera directly on mobile; the plain input opens
          the file browser / photo library on both mobile and desktop. */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
      />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  )
}
