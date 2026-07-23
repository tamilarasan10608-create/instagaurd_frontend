import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'
import api from '../utils/api'
import { useAuth } from '../context/AuthContext'
import ShieldLogo from '../components/ShieldLogo'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  // FIX: inline error state so user sees field-level errors
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setError('')
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.email.trim()) { setError('Email is required'); return }
    if (!form.password) { setError('Password is required'); return }

    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', form)
      login(data.access_token, data.user)
      toast.success(`Welcome back, ${data.user.full_name}!`)
      navigate('/')
    } catch (err) {
      // FIX: extract the actual error message from FastAPI response
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        (typeof err.response?.data === 'string' ? err.response.data : null) ||
        'Login failed. Check your email and password.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="circuit-bg min-h-screen flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="glass-card w-full max-w-md p-10"
        style={{ boxShadow: '0 0 60px rgba(59,130,246,0.12), 0 25px 50px rgba(0,0,0,0.5)' }}
      >
        <div className="flex flex-col items-center mb-8 gap-2">
          <ShieldLogo size={52} />
          <div className="flex items-center gap-1 mt-1">
            <span className="text-2xl font-bold text-white">Insta</span>
            <span className="text-2xl font-bold text-brand-light">Guard</span>
          </div>
          <h1 className="text-3xl font-bold text-white mt-1">Welcome Back</h1>
          <p className="text-sm text-slate-400">Sign in to your investigator account</p>
        </div>

        {/* Inline error banner */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 px-4 py-3 rounded-xl mb-4 text-sm text-red-300"
            style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}
          >
            <AlertCircle size={15} className="shrink-0" />
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Email</label>
            <input
              name="email"
              type="email"
              className="input-field"
              placeholder="agent@instaguard.io"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Password</label>
            <div className="relative">
              <input
                name="password"
                type={showPassword ? 'text' : 'password'}
                className="input-field pr-10"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <button type="submit" className="btn-primary mt-1" disabled={loading}>
            {loading
              ? <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Signing in…
              </span>
              : 'Sign In'
            }
          </button>
        </form>



        <p className="text-center text-sm text-slate-400 mt-5">
          <span className="text-brand-light cursor-pointer hover:underline">Forgot password?</span>
        </p>
        <p className="text-center text-sm text-slate-400 mt-2">
          Don't have an account?{' '}
          <Link to="/register" className="text-brand-light hover:underline font-medium">
            Create an account
          </Link>
        </p>
      </motion.div>
    </div>
  )
}


