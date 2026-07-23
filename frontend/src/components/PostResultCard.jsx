import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react'

export default function PostResultCard({ result, index }) {
  const suspicious = result.is_suspicious
  const confidence = Math.round(result.confidence_score * 100)
  const imgSrc = result.thumbnail_b64
    ? `data:image/jpeg;base64,${result.thumbnail_b64}`
    : result.image_url

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: Math.min(index * 0.04, 0.5), duration: 0.3 }}
      className={`result-card group ${suspicious ? 'suspicious' : 'clean'}`}
    >
      {/* Image */}
      <img
        src={imgSrc}
        alt={`Post ${result.post_index}`}
        className="w-full h-full object-cover"
        loading="lazy"
        onError={(e) => {
          e.target.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%231a2235' width='200' height='200'/%3E%3Ctext fill='%23334155' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3ENo Image%3C/text%3E%3C/svg%3E`
        }}
      />

      {/* Status badge top */}
      <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
        <div className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${suspicious
            ? 'bg-red-500/80 text-white'
            : 'bg-green-500/80 text-white'
          }`}>
          {suspicious
            ? <AlertTriangle size={10} />
            : <CheckCircle size={10} />
          }
          {suspicious ? 'Suspicious' : 'Clean'}
        </div>

        {result.instagram_post_url && (
          <a
            href={result.instagram_post_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="p-1 rounded-full bg-black/40 text-white/70 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ExternalLink size={10} />
          </a>
        )}
      </div>

      {/* Confidence score bottom */}
      <div className="absolute bottom-0 left-0 right-0 px-2 py-1.5"
        style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%)' }}
      >
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-white/60">#{result.post_index}</span>
          <span className="text-xs font-semibold text-white">
            Confidence: {confidence}%
          </span>
        </div>
      </div>
    </motion.div>
  )
}
