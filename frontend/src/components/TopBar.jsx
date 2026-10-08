import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useAuth } from '../context/AuthContext'

export default function TopBar({ title }) {
  const { theme, toggleTheme } = useTheme()
  const { user } = useAuth()

  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        <p className="text-sm" style={{ color: 'var(--cf-text-soft)' }}>
          {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="glass-card p-2.5 rounded-xl hover:scale-105 transition-transform"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div className="glass-card px-3 py-2 rounded-xl text-sm">
          <span className="font-semibold">{user?.first_name || user?.username}</span>
        </div>
      </div>
    </div>
  )
}
