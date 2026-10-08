import { Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from './Sidebar'
import SkeletonLoader from './SkeletonLoader'

export default function Layout() {
  const { user, loading } = useAuth()

  if (loading) return <SkeletonLoader full />
  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="h-screen flex gap-4 p-4" style={{ background: 'var(--cf-surface-soft)' }}>
      <Sidebar />
      <main className="flex-1 overflow-y-auto cf-scrollbar rounded-2xl">
        <Outlet />
      </main>
    </div>
  )
}
