import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, Clock, Trash2, ChevronRight, Image } from 'lucide-react'
import StatusBadge from './StatusBadge'

export default function ScanHistoryRow({ scan, onDelete, index }) {
  const navigate = useNavigate()
  const date = new Date(scan.created_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
  const time = new Date(scan.created_at).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit',
  })

  const isClickable = scan.status === 'completed' || scan.analyzed_posts > 0

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: Math.min(index * 0.05, 0.4), duration: 0.3 }}
      onClick={() => isClickable && navigate(`/scans/${scan.id}`)}
      className={`flex items-center gap-4 px-5 py-4 transition-all ${isClickable ? 'cursor-pointer hover:bg-white/[0.03]' : 'cursor-default'
        }`}
      style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
    >
      {/* Username + date */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-white truncate">@{scan.instagram_username}</p>
        <p className="text-xs text-slate-500 mt-0.5">{date} · {time}</p>
      </div>

      {/* Status */}
      <StatusBadge status={scan.status} />

      {/* Stats */}
      <div className="flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1 text-slate-500" title="Images analyzed">
          <Image size={12} />
          {scan.analyzed_posts}/{scan.total_posts}
        </span>
        {(scan.status === 'completed' || scan.suspicious_count > 0) && (
          <>
            <span className="flex items-center gap-1 text-red-400" title="Suspicious">
              <AlertTriangle size={12} />
              {scan.suspicious_count}
            </span>
            <span className="flex items-center gap-1 text-green-400" title="Clean">
              <CheckCircle size={12} />
              {scan.clean_count}
            </span>
          </>
        )}
        {scan.status === 'completed' && scan.avg_scan_duration_ms > 0 && (
          <span className="flex items-center gap-1 text-slate-500 hidden sm:flex" title="Avg duration">
            <Clock size={12} />
            {(scan.avg_scan_duration_ms / 1000).toFixed(2)}s
          </span>
        )}
      </div>

      {/* Arrow / delete */}
      <div className="flex items-center gap-1 shrink-0">
        {isClickable && <ChevronRight size={14} className="text-slate-600" />}
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(scan.id) }}
          className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          title="Delete scan"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </motion.div>
  )
}
