import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Activity, ClipboardPlus, Building2, Users,
  BrainCircuit, BarChart3, BellRing, Settings, ShieldCheck, LogOut,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_BY_ROLE = {
  ADMIN: [
    ['/dashboard', LayoutDashboard, 'Dashboard'],
    ['/queue', Activity, 'Live Queue Board'],
    ['/departments', Building2, 'Departments'],
    ['/staff', Users, 'Staff'],
    ['/predictions', BrainCircuit, 'AI Predictions'],
    ['/analytics', BarChart3, 'Analytics & Reports'],
    ['/alerts', BellRing, 'Alerts Log'],
    ['/admin', ShieldCheck, 'Admin Panel'],
  ],
  DOCTOR: [
    ['/dashboard', LayoutDashboard, 'Dashboard'],
    ['/queue', Activity, 'Live Queue Board'],
    ['/predictions', BrainCircuit, 'AI Predictions'],
    ['/alerts', BellRing, 'Alerts Log'],
  ],
  NURSE: [
    ['/dashboard', LayoutDashboard, 'Dashboard'],
    ['/queue', Activity, 'Live Queue Board'],
    ['/intake', ClipboardPlus, 'Patient Intake'],
    ['/alerts', BellRing, 'Alerts Log'],
  ],
  HOSPITAL_ADMINISTRATOR: [
    ['/dashboard', LayoutDashboard, 'Dashboard'],
    ['/analytics', BarChart3, 'Analytics & Reports'],
    ['/predictions', BrainCircuit, 'AI Predictions'],
  ],
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const items = NAV_BY_ROLE[user?.role] ?? []

  return (
    <aside className="glass-card w-64 shrink-0 h-full rounded-2xl p-4 flex flex-col gap-1 cf-scrollbar overflow-y-auto">
      <div className="px-2 py-3 mb-2">
        <p className="text-lg font-bold tracking-tight" style={{ color: 'var(--cf-cyan-strong)' }}>
          CareFlow
        </p>
        <p className="text-xs" style={{ color: 'var(--cf-text-soft)' }}>{user?.role?.replace('_', ' ')}</p>
      </div>

      {items.map(([to, Icon, label]) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              isActive
                ? 'bg-cyan-500/15 text-cyan-500'
                : 'hover:bg-black/5 dark:hover:bg-white/5'
            }`
          }
          style={({ isActive }) => (isActive ? {} : { color: 'var(--cf-text)' })}
        >
          <Icon size={18} />
          {label}
        </NavLink>
      ))}

      <div className="mt-auto flex flex-col gap-1 pt-2 border-t" style={{ borderColor: 'var(--cf-border)' }}>
        <NavLink
          to="/profile"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium hover:bg-black/5 dark:hover:bg-white/5"
          style={{ color: 'var(--cf-text)' }}
        >
          <Settings size={18} />
          Profile & Settings
        </NavLink>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-500 hover:bg-red-500/10"
        >
          <LogOut size={18} />
          Log out
        </button>
      </div>
    </aside>
  )
}
