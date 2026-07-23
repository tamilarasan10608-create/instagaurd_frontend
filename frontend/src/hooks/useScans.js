import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../utils/api'
import toast from 'react-hot-toast'

// Poll interval while any scan is active
const ACTIVE_STATUSES = ['pending', 'scraping', 'analyzing']

export function useScans() {
  return useQuery({
    queryKey: ['scans'],
    queryFn: () => api.get('/scans').then((r) => r.data),
    // FIX: poll every 4s when any scan is active, otherwise every 30s (keeps history fresh)
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 10_000
      const hasActive = data.some((s) => ACTIVE_STATUSES.includes(s.status))
      return hasActive ? 4_000 : 30_000
    },
    staleTime: 0, // always re-fetch on focus
  })
}

export function useScan(scanId) {
  return useQuery({
    queryKey: ['scans', scanId],
    queryFn: () => api.get(`/scans/${scanId}`).then((r) => r.data),
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3_000
      return ACTIVE_STATUSES.includes(data.status) ? 3_000 : false
    },
    enabled: !!scanId,
    staleTime: 0,
  })
}

export function useStartScan() {
  const queryClient = useQueryClient()
  return useMutation({
    // FIX: accept object { instagram_username, max_posts } not just a string
    mutationFn: (body) => api.post('/scans', body).then((r) => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      toast.success(`Scan started for @${data.instagram_username}`)
    },
    onError: (err) => {
      const msg = err.response?.data?.detail || 'Failed to start scan'
      toast.error(msg)
    },
  })
}

export function useDeleteScan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (scanId) => api.delete(`/scans/${scanId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      toast.success('Scan deleted')
    },
    onError: () => toast.error('Failed to delete scan'),
  })
}
