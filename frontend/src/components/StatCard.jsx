import { motion } from 'framer-motion'

export default function StatCard({ label, value, subtitle, variant = 'default', icon, index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className={`stat-card ${variant}`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-sm text-slate-400 font-medium">{label}</span>
        <span className={`p-1.5 rounded-lg ${variant === 'suspicious' ? 'bg-red-500/10 text-red-400' :
            variant === 'clean' ? 'bg-green-500/10 text-green-400' :
              'bg-white/5 text-slate-400'
          }`}>
          {icon}
        </span>
      </div>
      <div className={`text-4xl font-bold tracking-tight ${variant === 'suspicious' ? 'text-red-400' :
          variant === 'clean' ? 'text-green-400' :
            'text-white'
        }`}>
        {value}
      </div>
      {subtitle && (
        <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
      )}
    </motion.div>
  )
}
