import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LogIn } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Invalid email or password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--cf-surface-soft)' }}>
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
        className="glass-card w-full max-w-sm rounded-2xl p-8"
      >
        <Link to="/" className="text-lg font-bold" style={{ color: 'var(--cf-cyan-strong)' }}>CareFlow</Link>
        <h2 className="text-2xl font-bold mt-4 mb-1">Staff sign in</h2>
        <p className="text-sm mb-6" style={{ color: 'var(--cf-text-soft)' }}>Enter your hospital credentials.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none focus:border-cyan-500"
              style={{ borderColor: 'var(--cf-border)' }}
            />
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none focus:border-cyan-500"
              style={{ borderColor: 'var(--cf-border)' }}
            />
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit" disabled={submitting}
            className="w-full flex items-center justify-center gap-2 rounded-xl py-2.5 font-semibold disabled:opacity-60"
            style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}
          >
            <LogIn size={16} />
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t text-center" style={{ borderColor: 'var(--cf-border)' }}>
          <Link to="/kiosk" className="text-sm" style={{ color: 'var(--cf-cyan-strong)' }}>
            View public kiosk instead →
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
