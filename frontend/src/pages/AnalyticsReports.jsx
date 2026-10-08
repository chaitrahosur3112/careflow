import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import SkeletonLoader from '../components/SkeletonLoader'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export default function AnalyticsReports() {
  const [trends, setTrends] = useState(null)
  const [peakHours, setPeakHours] = useState(null)
  const [bottlenecks, setBottlenecks] = useState(null)

  useEffect(() => {
    api.get('/analytics/admission-trends').then((res) => setTrends(res.data))
    api.get('/analytics/peak-hours').then((res) => setPeakHours(res.data))
    api.get('/analytics/department-bottlenecks').then((res) => setBottlenecks(res.data))
  }, [])

  const trendData = trends?.map((t) => ({ day: new Date(t.day).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), admissions: t.admissions }))

  const heatmapMax = peakHours?.length ? Math.max(...peakHours.map((p) => p.admissions)) : 1
  const heatmapLookup = {}
  peakHours?.forEach((p) => { heatmapLookup[`${p.weekday}-${p.hour}`] = p.admissions })

  return (
    <div className="p-6">
      <TopBar title="Analytics & Reports" />

      <div className="glass-card rounded-2xl p-5 mb-6">
        <h3 className="font-semibold mb-4">Admission Trends</h3>
        {!trends ? <SkeletonLoader rows={2} /> : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--cf-border)" />
              <XAxis dataKey="day" tick={{ fontSize: 12, fill: 'var(--cf-text-soft)' }} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--cf-text-soft)' }} allowDecimals={false} />
              <Tooltip contentStyle={{ background: 'var(--cf-surface)', border: '1px solid var(--cf-border)', borderRadius: 12 }} />
              <Line type="monotone" dataKey="admissions" stroke="var(--cf-cyan-strong)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="glass-card rounded-2xl p-5 mb-6">
        <h3 className="font-semibold mb-4">Peak Hour Heatmap</h3>
        {!peakHours ? <SkeletonLoader rows={3} /> : (
          <div className="overflow-x-auto cf-scrollbar">
            <div className="grid grid-cols-[auto_repeat(24,1fr)] gap-1 min-w-[900px]">
              <div />
              {Array.from({ length: 24 }).map((_, h) => (
                <div key={h} className="text-[10px] text-center" style={{ color: 'var(--cf-text-soft)' }}>{h}</div>
              ))}
              {WEEKDAYS.map((label, weekday) => (
                <div key={weekday} className="contents">
                  <div className="text-xs pr-2 flex items-center" style={{ color: 'var(--cf-text-soft)' }}>{label}</div>
                  {Array.from({ length: 24 }).map((_, hour) => {
                    const count = heatmapLookup[`${weekday}-${hour}`] || 0
                    const intensity = heatmapMax ? count / heatmapMax : 0
                    return (
                      <div
                        key={hour}
                        title={`${count} admissions`}
                        className="aspect-square rounded"
                        style={{ background: `color-mix(in srgb, var(--cf-cyan-strong) ${Math.round(intensity * 90) + (count ? 10 : 0)}%, transparent)` }}
                      />
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="glass-card rounded-2xl p-5">
        <h3 className="font-semibold mb-4">Department Bottleneck Analysis</h3>
        {!bottlenecks ? <SkeletonLoader rows={3} /> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b" style={{ borderColor: 'var(--cf-border)', color: 'var(--cf-text-soft)' }}>
                <th className="py-2 font-medium">Department</th>
                <th className="py-2 font-medium">Avg wait</th>
                <th className="py-2 font-medium">Queue length</th>
                <th className="py-2 font-medium">Bed occupancy</th>
              </tr>
            </thead>
            <tbody>
              {bottlenecks.map((b) => (
                <tr key={b.department_id} className="border-b last:border-0" style={{ borderColor: 'var(--cf-border)' }}>
                  <td className="py-2.5 font-medium">{b.department_name}</td>
                  <td className="py-2.5">{b.average_wait_time_minutes} min</td>
                  <td className="py-2.5">{b.current_queue_length}</td>
                  <td className="py-2.5">{b.bed_occupancy_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
