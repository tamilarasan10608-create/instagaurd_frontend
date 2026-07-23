import { Loader2 } from 'lucide-react'

const LABELS = {
  pending:   'Pending',
  scraping:  'Scraping',
  analyzing: 'Analyzing',
  completed: 'Completed',
  failed:    'Failed',
}

export default function StatusBadge({ status }) {
  const spinning = status === 'scraping' || status === 'analyzing'
  return (
    <span className={`status-badge ${status}`}>
      {spinning && <Loader2 size={10} className="animate-spin" />}
      {LABELS[status] || status}
    </span>
  )
}
