import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ScanDetailPage from './pages/ScanDetailPage'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen text-slate-400">Loading…</div>
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/scans/:scanId" element={<PrivateRoute><ScanDetailPage /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
