import { useEffect, useState, useCallback } from 'react'
import { Users, Clock, AlertTriangle, BedDouble, UserCheck, BellRing, Timer } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import StatCard from '../components/StatCard'
import SkeletonLoader from '../components/SkeletonLoader'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [departments, setDepartments] = useState(null)
  const [alertsToday, setAlertsToday] = useState(0)

  const load = useCallback(async () => {
    const [deptRes, alertsRes] = await Promise.all([
      api.get('/departments/all'),
      api.get('/alerts/all'),
    ])
    const list = deptRes.data.results ?? deptRes.data
    const stats = await Promise.all(list.map((d) => api.get(`/departments/${d.id}/stats`).then((r) => r.data)))
    setDepartments(stats)
    const alertList = alertsRes.data.results ?? alertsRes.data
    const today = new Date().toDateString()
    setAlertsToday(alertList.filter((a) => new Date(a.created_at).toDateString() === today).length)
  }, [])

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [load])

  if (!departments) {
    return (
      <div className="p-6">
        <TopBar title="Dashboard" />
        <SkeletonLoader rows={4} />
      </div>
    )
  }

  const totalWaiting = departments.reduce((sum, d) => sum + d.current_queue_length, 0)
  const avgWait = departments.length
    ? Math.round(departments.reduce((sum, d) => sum + d.average_wait_time_minutes, 0) / departments.length)
    : 0
  const highLoad = departments.filter((d) => d.bed_occupancy_pct >= 80).length
  const availableBeds = departments.reduce((sum, d) => sum + (d.total_beds - d.occupied_beds), 0)
  const staffOnDuty = departments.reduce((sum, d) => sum + d.staff_on_duty_count, 0)

  const chartData = departments.map((d) => ({ name: d.name, queue: d.current_queue_length }))

  return (
    <div className="p-6">
      <TopBar title={`Welcome back, ${user?.first_name || user?.username}`} />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Users} label="Patients In System" value={totalWaiting} />
        <StatCard icon={Clock} label="Average Wait Time" value={avgWait} suffix="min" tone={avgWait > 45 ? 'amber' : 'emerald'} />
        <StatCard icon={AlertTriangle} label="Departments at High Load" value={highLoad} tone={highLoad > 0 ? 'red' : 'emerald'} />
        <StatCard icon={BedDouble} label="Available Beds" value={availableBeds} tone="emerald" />
        <StatCard icon={UserCheck} label="Staff On Duty" value={staffOnDuty} />
        <StatCard icon={BellRing} label="Overcrowding Alerts Today" value={alertsToday} tone={alertsToday > 0 ? 'amber' : 'emerald'} />
        {user?.role !== 'HOSPITAL_ADMINISTRATOR' && (
          <StatCard icon={Timer} label="Longest Waiting Patient" value={Math.max(0, ...departments.map((d) => d.average_wait_time_minutes))} suffix="min" tone="amber" />
        )}
      </div>

      <div className="glass-card rounded-2xl p-5">
        <h3 className="font-semibold mb-4">Department Queue Length</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--cf-border)" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--cf-text-soft)' }} />
            <YAxis tick={{ fontSize: 12, fill: 'var(--cf-text-soft)' }} allowDecimals={false} />
            <Tooltip contentStyle={{ background: 'var(--cf-surface)', border: '1px solid var(--cf-border)', borderRadius: 12 }} />
            <Bar dataKey="queue" fill="var(--cf-cyan-strong)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
