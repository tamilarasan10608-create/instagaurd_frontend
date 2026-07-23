import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // FIX: only redirect to login on 401 for protected routes
    // NOT for /auth/login or /auth/register — those should show error messages
    const url = err.config?.url || ''
    const isAuthRoute = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/google')

    if (err.response?.status === 401 && !isAuthRoute) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
