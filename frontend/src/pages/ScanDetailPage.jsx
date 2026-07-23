import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  ArrowLeft, BarChart2, AlertTriangle, CheckCircle,
  Clock, Download, Grid3X3, List, Loader2, FileText,
  ExternalLink, RefreshCw,
} from 'lucide-react'
import Navbar from '../components/Navbar'
import StatCard from '../components/StatCard'
import PostResultCard from '../components/PostResultCard'
import StatusBadge from '../components/StatusBadge'
import { useScan } from '../hooks/useScans'

const FILTERS = [
  { key: 'All', label: 'All' },
  { key: 'Suspicious', label: 'Suspicious' },
  { key: 'Clean', label: 'Clean' },
]

export default function ScanDetailPage() {
  const { scanId } = useParams()
  const navigate = useNavigate()
  const { data: scan, isLoading, refetch } = useScan(scanId)
  const [filter, setFilter] = useState('All')
  const [viewMode, setViewMode] = useState('grid')
  const [exporting, setExporting] = useState(false)

  const isActive = ['pending', 'scraping', 'analyzing'].includes(scan?.status)

  const results = scan?.results || []
  const filtered = results.filter((r) => {
    if (filter === 'Suspicious') return r.is_suspicious
    if (filter === 'Clean') return !r.is_suspicious
    return true
  })

  const progress = scan?.total_posts > 0
    ? Math.round((scan.analyzed_posts / scan.total_posts) * 100)
    : 0

  const handleExport = async () => {
    if (exporting) return
    setExporting(true)
    try {
      const res = await fetch(`/api/scans/${scanId}/export`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `instaguard_report_${scan.instagram_username}_${new Date().toISOString().slice(0, 10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Report downloaded!')
    } catch {
      toast.error('Failed to export report')
    } finally {
      setExporting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="circuit-bg min-h-screen">
        <Navbar onSearch={() => { }} />
        <div className="flex items-center justify-center h-[60vh] text-slate-500">
          <Loader2 size={24} className="animate-spin mr-3" />
          Loading scan…
        </div>
      </div>
    )
  }

  if (!scan) return null

  return (
    <div className="circuit-bg min-h-screen pb-24">
      <Navbar onSearch={(u) => navigate('/')} />

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start justify-between gap-4 mb-8 flex-wrap"
        >
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-xl font-bold text-white">@{scan.instagram_username}</h1>
                <StatusBadge status={scan.status} />
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Scanned {new Date(scan.created_at).toLocaleString()} · {scan.max_posts} posts requested
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              <RefreshCw size={13} />
              Refresh
            </button>
            {scan.status === 'completed' && (
              <button
                onClick={handleExport}
                disabled={exporting}
                className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm text-white disabled:opacity-60 hover:opacity-90 transition-opacity"
                style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
              >
                {exporting
                  ? <Loader2 size={14} className="animate-spin" />
                  : <Download size={14} />
                }
                Export PDF Report
              </button>
            )}
          </div>
        </motion.div>

        {/* Live progress bar */}
        {isActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card p-5 mb-6"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-9 h-9 rounded-full border-2 border-brand border-t-transparent animate-spin shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-white capitalize">
                  {scan.status === 'scraping'
                    ? `Scraping @${scan.instagram_username} via Apify…`
                    : `Analyzing images (${scan.analyzed_posts}/${scan.total_posts})…`
                  }
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {scan.status === 'scraping'
                    ? 'Fetching post metadata from Instagram…'
                    : `${scan.suspicious_count} suspicious · ${scan.clean_count} clean so far`
                  }
                </p>
              </div>
              {scan.total_posts > 0 && (
                <span className="text-sm font-mono text-brand-light shrink-0">{progress}%</span>
              )}
            </div>
            {scan.total_posts > 0 && (
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: 'linear-gradient(90deg, #3b82f6, #6366f1)' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            )}
          </motion.div>
        )}

        {/* Error state */}
        {scan.status === 'failed' && scan.error_message && (
          <div
            className="glass-card p-5 mb-6 text-sm text-red-300"
            style={{ borderColor: 'rgba(239,68,68,0.3)' }}
          >
            <p className="font-semibold mb-1 text-red-400">Scan failed</p>
            <p className="text-slate-400 font-mono text-xs whitespace-pre-wrap">{scan.error_message}</p>
          </div>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Total Posts Scraped"
            value={scan.total_posts.toLocaleString()}
            subtitle={`${scan.max_posts} requested`}
            icon={<BarChart2 size={16} />}
            index={0}
          />
          <StatCard
            label="Suspicious Content"
            value={scan.suspicious_count}
            subtitle="Stego detected"
            variant="suspicious"
            icon={<AlertTriangle size={16} />}
            index={1}
          />
          <StatCard
            label="Clean Posts"
            value={scan.clean_count}
            subtitle="No payload found"
            variant="clean"
            icon={<CheckCircle size={16} />}
            index={2}
          />
          <StatCard
            label="Avg Scan Duration"
            value={scan.avg_scan_duration_ms > 0 ? `${(scan.avg_scan_duration_ms / 1000).toFixed(2)}s` : '—'}
            subtitle="per image"
            icon={<Clock size={16} />}
            index={3}
          />
        </div>

        {/* Results panel */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card overflow-hidden"
        >
          {/* Toolbar */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 flex-wrap gap-3">
            <div>
              <h2 className="font-semibold text-white">Analysis Results</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Steganography detection for @{scan.instagram_username}
                {scan.status === 'completed' && ` · ${scan.analyzed_posts} images analyzed`}
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Filter tabs */}
              <div className="flex rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                {FILTERS.map((f) => {
                  const count = f.key === 'All' ? results.length
                    : f.key === 'Suspicious' ? results.filter(r => r.is_suspicious).length
                      : results.filter(r => !r.is_suspicious).length
                  return (
                    <button
                      key={f.key}
                      onClick={() => setFilter(f.key)}
                      className={`px-3 py-1.5 text-xs font-medium transition-colors ${filter === f.key ? 'bg-brand text-white' : 'text-slate-400 hover:text-white'
                        }`}
                    >
                      {f.label}{count > 0 ? ` (${count})` : ''}
                    </button>
                  )
                })}
              </div>

              {/* View mode */}
              <div className="flex rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 transition-colors ${viewMode === 'grid' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
                  title="Grid view"
                >
                  <Grid3X3 size={14} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 transition-colors ${viewMode === 'list' ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}
                  title="List view"
                >
                  <List size={14} />
                </button>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {filtered.length === 0 && !isActive ? (
              <div className="flex flex-col items-center justify-center py-16 text-slate-500">
                <FileText size={32} className="mb-3 text-slate-700" />
                <p className="text-sm">
                  {results.length === 0
                    ? scan.status === 'completed' ? 'No images were analyzed' : 'Waiting for results…'
                    : `No ${filter.toLowerCase()} posts`
                  }
                </p>
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {filtered.map((result, i) => (
                  <PostResultCard key={result.id} result={result} index={i} />
                ))}
                {/* Placeholder cards while scanning */}
                {isActive && Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={`placeholder-${i}`}
                    className="rounded-xl flex items-center justify-center bg-white/[0.02]"
                    style={{
                      aspectRatio: '1',
                      border: '2px dashed rgba(255,255,255,0.07)',
                    }}
                  >
                    <Loader2 size={18} className="animate-spin text-slate-700" />
                  </div>
                ))}
              </div>
            ) : (
              <ListView results={filtered} />
            )}
          </div>
        </motion.div>
      </main>

      {/* Floating export button (alternative access) */}
      {scan.status === 'completed' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="fixed bottom-6 right-6 z-40"
        >
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-sm text-white shadow-2xl disabled:opacity-60"
            style={{
              background: 'rgba(17,24,39,0.95)',
              border: '1px solid rgba(59,130,246,0.35)',
              backdropFilter: 'blur(16px)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(59,130,246,0.1)',
            }}
          >
            {exporting ? <Loader2 size={15} className="animate-spin" /> : <FileText size={15} />}
            Export Detailed Report
          </button>
        </motion.div>
      )}
    </div>
  )
}

function ListView({ results }) {
  return (
    <div className="flex flex-col divide-y divide-white/5">
      {results.map((r, i) => (
        <motion.div
          key={r.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: Math.min(i * 0.02, 0.4) }}
          className="flex items-center gap-4 py-3"
        >
          <span className="text-xs text-slate-600 font-mono w-7 text-right shrink-0">
            #{r.post_index}
          </span>

          {/* Thumbnail */}
          {r.thumbnail_b64 ? (
            <img
              src={`data:image/jpeg;base64,${r.thumbnail_b64}`}
              alt={`Post ${r.post_index}`}
              className="w-11 h-11 rounded-lg object-cover shrink-0"
            />
          ) : (
            <div className="w-11 h-11 rounded-lg bg-white/5 shrink-0" />
          )}

          <div className="flex-1 min-w-0">
            <p className="text-xs text-slate-400 truncate font-mono">
              {r.instagram_post_url || r.image_url || '—'}
            </p>
            <p className="text-xs text-slate-600 mt-0.5">{r.scan_duration_ms.toFixed(1)} ms</p>
          </div>

          {/* Confidence */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${Math.round(r.confidence_score * 100)}%`,
                  background: r.is_suspicious ? '#ef4444' : '#22c55e',
                }}
              />
            </div>
            <span className="text-xs font-mono text-slate-300 w-10 text-right">
              {Math.round(r.confidence_score * 100)}%
            </span>
          </div>

          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${r.is_suspicious
              ? 'bg-red-500/15 text-red-400'
              : 'bg-green-500/15 text-green-400'
            }`}>
            {r.is_suspicious ? '⚠ Suspicious' : '✓ Clean'}
          </span>

          {r.instagram_post_url && (
            <a
              href={r.instagram_post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-600 hover:text-brand-light transition-colors shrink-0"
            >
              <ExternalLink size={13} />
            </a>
          )}
        </motion.div>
      ))}
    </div>
  )
}
