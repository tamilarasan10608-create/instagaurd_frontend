import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart2, AlertTriangle, CheckCircle, Clock, Plus, History, Search, X } from 'lucide-react'
import toast from 'react-hot-toast'
import Navbar from '../components/Navbar'
import StatCard from '../components/StatCard'
import ScanHistoryRow from '../components/ScanHistoryRow'
import { useScans, useStartScan, useDeleteScan } from '../hooks/useScans'

export default function DashboardPage() {
  const { data: scans = [], isLoading } = useScans()
  const startScan = useStartScan()
  const deleteScan = useDeleteScan()
  const [newUsername, setNewUsername] = useState('')
  const [maxPosts, setMaxPosts] = useState(50)
  const [showNewScanInput, setShowNewScanInput] = useState(false)
  const [searchFilter, setSearchFilter] = useState('')

  // Aggregate stats from ALL stored scans
  const completedScans = scans.filter((s) => s.status === 'completed')
  const totalPosts = completedScans.reduce((a, s) => a + s.analyzed_posts, 0)
  const totalSuspicious = completedScans.reduce((a, s) => a + s.suspicious_count, 0)
  const totalClean = completedScans.reduce((a, s) => a + s.clean_count, 0)
  const avgDuration = completedScans.length
    ? completedScans.reduce((a, s) => a + s.avg_scan_duration_ms, 0) / completedScans.length
    : 0

  // Filter scans by search
  const filteredScans = searchFilter
    ? scans.filter((s) => s.instagram_username.toLowerCase().includes(searchFilter.toLowerCase()))
    : scans

  const handleSearch = (username) => {
    setNewUsername(username.replace('@', '').trim())
    setShowNewScanInput(true)
  }

  const handleStartScan = () => {
    const u = newUsername.replace('@', '').trim()
    if (!u) { toast.error('Enter an Instagram username'); return }
    startScan.mutate({ instagram_username: u, max_posts: maxPosts }, {
      onSuccess: () => {
        setNewUsername('')
        setShowNewScanInput(false)
      },
    })
  }

  const handleDelete = (id) => {
    if (window.confirm('Delete this scan and all its results?')) {
      deleteScan.mutate(id)
    }
  }

  const activeScans = scans.filter((s) =>
    ['pending', 'scraping', 'analyzing'].includes(s.status)
  )

  return (
    <div className="circuit-bg min-h-screen">
      <Navbar onSearch={handleSearch} />

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* Hero / Topic */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
            InstaGuard
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-3xl">
            An Integrated Framework for Steganography Detection in Instagram Images using Deep Learning
          </p>
        </div>

        {/* Active scan live ticker */}
        {activeScans.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-4 mb-6 flex items-center gap-4"
            style={{ borderColor: 'rgba(59,130,246,0.3)' }}
          >
            <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">
                {activeScans.length} scan{activeScans.length > 1 ? 's' : ''} running
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {activeScans.map(s => `@${s.instagram_username} (${s.status})`).join(' · ')}
              </p>
            </div>
          </motion.div>
        )}

        {/* New scan panel */}
        <AnimatePresence>
          {showNewScanInput && (
            <motion.div
              initial={{ opacity: 0, y: -12, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -8, height: 0 }}
              className="overflow-hidden mb-6"
            >
              <div className="glass-card p-5" style={{ borderColor: 'rgba(59,130,246,0.25)' }}>
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Search size={14} className="text-brand-light" />
                  New Steganography Scan
                </h3>
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="flex-1 min-w-48 relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-mono text-sm">@</span>
                    <input
                      autoFocus
                      value={newUsername}
                      onChange={(e) => setNewUsername(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleStartScan()}
                      placeholder="instagram_username"
                      className="input-field pl-7"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-400 whitespace-nowrap">Max posts:</label>
                    <input
                      type="number"
                      min={1}
                      max={200}
                      value={maxPosts}
                      onChange={(e) => setMaxPosts(e.target.value)}
                      className="input-field w-24 text-center"
                      style={{ paddingTop: '10px', paddingBottom: '10px' }}
                    />
                  </div>
                  <button
                    onClick={handleStartScan}
                    disabled={startScan.isPending}
                    className="px-6 py-2.5 rounded-xl font-semibold text-sm text-white disabled:opacity-50 hover:opacity-90 transition-opacity"
                    style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
                  >
                    {startScan.isPending ? 'Starting…' : '🔍 Start Scan'}
                  </button>
                  <button
                    onClick={() => { setShowNewScanInput(false); setNewUsername('') }}
                    className="p-2.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <X size={16} />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Aggregate stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Total Posts Analyzed"
            value={totalPosts.toLocaleString()}
            subtitle={`across ${completedScans.length} scan${completedScans.length !== 1 ? 's' : ''}`}
            icon={<BarChart2 size={16} />}
            index={0}
          />
          <StatCard
            label="Suspicious Content"
            value={totalSuspicious.toLocaleString()}
            subtitle="Stego detected"
            variant="suspicious"
            icon={<AlertTriangle size={16} />}
            index={1}
          />
          <StatCard
            label="Clean Posts"
            value={totalClean.toLocaleString()}
            subtitle="Safe content"
            variant="clean"
            icon={<CheckCircle size={16} />}
            index={2}
          />
          <StatCard
            label="Avg Scan Duration"
            value={avgDuration > 0 ? `${(avgDuration / 1000).toFixed(1)}s` : '—'}
            subtitle="per image"
            icon={<Clock size={16} />}
            index={3}
          />
        </div>

        {/* Scan history panel */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card overflow-hidden"
        >
          <div className="flex items-center justify-between px-6 py-5 border-b border-white/5 flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <History size={18} className="text-brand-light" />
              <h2 className="font-semibold text-slate-900 dark:text-white">Scan History</h2>
              <span className="text-xs text-slate-500 font-mono ml-1">({scans.length})</span>
            </div>

            <div className="flex items-center gap-3">
              {/* History search filter */}
              {scans.length > 3 && (
                <div className="relative">
                  <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Filter by username…"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    className="pl-7 pr-3 py-1.5 rounded-lg text-xs"
                    style={{
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#f1f5f9',
                      outline: 'none',
                    }}
                  />
                </div>
              )}
              <button
                onClick={() => setShowNewScanInput(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-brand-light hover:bg-brand/10 transition-colors"
              >
                <Plus size={14} />
                New Scan
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-500">
              <div className="w-6 h-6 border-2 border-brand/30 border-t-brand rounded-full animate-spin mr-3" />
              Loading scan history…
            </div>
          ) : filteredScans.length === 0 && scans.length === 0 ? (
            <EmptyState onNew={() => setShowNewScanInput(true)} />
          ) : filteredScans.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-slate-500 text-sm">
              No scans matching "{searchFilter}"
            </div>
          ) : (
            <div>
              {filteredScans.map((scan, i) => (
                <ScanHistoryRow
                  key={scan.id}
                  scan={scan}
                  onDelete={handleDelete}
                  index={i}
                />
              ))}
            </div>
          )}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="mt-8 py-8 border-t border-white/5 bg-black/20">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-500 max-w-4xl mx-auto leading-relaxed">
            InstaGuard is an advanced forensic tool designed to combat malicious steganography on social media. 
            It leverages state-of-the-art deep learning models to automatically scrape and analyze Instagram images for hidden payloads, 
            providing investigators with actionable intelligence, rapid threat detection, and comprehensive PDF reporting capabilities.
          </p>
          <p className="text-xs text-slate-600 mt-4">
            © {new Date().getFullYear()} InstaGuard Project. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

function EmptyState({ onNew }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center px-8">
      <div className="w-16 h-16 rounded-2xl bg-brand/10 flex items-center justify-center mb-4">
        <BarChart2 size={28} className="text-brand-light" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">No scans yet</h3>
      <p className="text-sm text-slate-500 mb-6 max-w-xs">
        Enter an Instagram username to start your first forensic steganography scan.
      </p>
      <button
        onClick={onNew}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm text-white"
        style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
      >
        <Plus size={15} />
        Start First Scan
      </button>
    </div>
  )
}
