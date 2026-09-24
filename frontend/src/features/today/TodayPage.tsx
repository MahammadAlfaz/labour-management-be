import { useState } from 'react'
import { ChatIcon } from '../../components/icons'
import EmptyState from '../../components/EmptyState'
import { todayIso } from '../../lib/date'
import { useSites } from '../sites/useSites'
import QuickAskSheet from './QuickAskSheet'
import SiteCrewBoard from './SiteCrewBoard'
import SiteGrid from './SiteGrid'
import TodaySummary from './TodaySummary'

export default function TodayPage() {
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null)
  const [workDate, setWorkDate] = useState(todayIso())
  const [showQuickAsk, setShowQuickAsk] = useState(false)

  const { data: sites, isLoading: sitesLoading } = useSites({ status: 'active' })
  const selectedSite = sites?.find((s) => s.id === selectedSiteId) ?? null

  return (
    <div className="flex flex-col gap-4 p-4 pb-24">
      <label className="text-sm">
        <span className="mb-1 block font-medium text-slate-700">Date</span>
        <input
          type="date"
          value={workDate}
          onChange={(e) => setWorkDate(e.target.value)}
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-base text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </label>

      {sitesLoading && <p className="text-sm text-slate-500">Loading sites…</p>}

      {!sitesLoading && sites?.length === 0 && (
        <EmptyState message="Add an active site first to start marking attendance." />
      )}

      {sites && sites.length > 0 && !selectedSite && (
        <>
          <TodaySummary sites={sites} workDate={workDate} />
          <SiteGrid sites={sites} workDate={workDate} onSelect={setSelectedSiteId} />
        </>
      )}

      {selectedSite && (
        <SiteCrewBoard site={selectedSite} workDate={workDate} onBack={() => setSelectedSiteId(null)} />
      )}

      <button
        type="button"
        onClick={() => setShowQuickAsk(true)}
        aria-label="Ask the assistant"
        className="fixed right-4 bottom-24 flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-brand-500 text-white shadow-lg transition-colors active:bg-brand-600"
      >
        <ChatIcon className="h-6 w-6" />
      </button>

      {showQuickAsk && <QuickAskSheet onClose={() => setShowQuickAsk(false)} />}
    </div>
  )
}
