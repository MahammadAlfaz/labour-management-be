import { BuildingIcon } from '../../components/icons'
import type { Site } from '../sites/api'

export default function SiteGrid({
  sites,
  onSelect,
}: {
  sites: Site[]
  onSelect: (siteId: string) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {sites.map((site) => (
        <button
          key={site.id}
          type="button"
          onClick={() => onSelect(site.id)}
          className="cursor-pointer overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-colors active:bg-slate-50"
        >
          <div className="flex aspect-square items-center justify-center bg-slate-100">
            {site.photo_url ? (
              <img src={site.photo_url} alt="" className="h-full w-full object-cover" />
            ) : (
              <BuildingIcon className="h-10 w-10 text-slate-300" />
            )}
          </div>
          <div className="p-2.5">
            <p className="truncate font-semibold text-slate-900">{site.name}</p>
            <p className="truncate text-xs text-slate-500">{site.location}</p>
          </div>
        </button>
      ))}
    </div>
  )
}
