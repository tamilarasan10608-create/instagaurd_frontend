import { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // FIX: restore session from localStorage on every page load
    // This is what was missing — on fresh load the state was null even though
    // token + user were stored, because the effect was completing before React hydrated
    const restoreSession = () => {
      try {
        const token = localStorage.getItem('token')
        const stored = localStorage.getItem('user')
        if (token && stored) {
          const userData = JSON.parse(stored)
          setUser(userData)
        }
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      } finally {
        setLoading(false)
      }
    }
    restoreSession()
  }, [])

  const login = (token, userData) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const updateUser = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
