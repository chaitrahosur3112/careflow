import { useEffect, useState } from 'react'
import { BrainCircuit, Gauge, Users2 } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import RiskGauge from '../components/RiskGauge'
import SkeletonLoader from '../components/SkeletonLoader'
import { useAuth } from '../context/AuthContext'

export default function AIPredictions() {
  const { user } = useAuth()
  const [departments, setDepartments] = useState([])
  const [selected, setSelected] = useState('')
  const [stats, setStats] = useState(null)
  const [waitTime, setWaitTime] = useState(null)
  const [risk, setRisk] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get('/departments/all').then((res) => {
      const list = res.data.results ?? res.data
      setDepartments(list)
      if (list.length) setSelected(list[0].id)
    })
    if (user?.role === 'ADMIN') {
      api.get('/analytics/model-accuracy').then((res) => setMetrics(res.data)).catch(() => {})
    }
  }, [user])

  useEffect(() => {
    if (!selected) return
    api.get(`/departments/${selected}/stats`).then((res) => setStats(res.data))
  }, [selected])

  const runPredictions = async () => {
    if (!stats) return
    setLoading(true)
    const now = new Date()
    try {
      const [waitRes, riskRes] = await Promise.all([
        api.post('/predictions/wait-time', {
          department_id: selected,
          current_queue_length: stats.current_queue_length,
          triage_level: 'P2',
          staff_on_duty: stats.staff_on_duty_count,
          time_of_day: now.getHours(),
          day_of_week: now.getDay(),
        }),
        api.post('/predictions/overcrowding-risk', {
          department_id: selected,
          admission_rate_last_1h: stats.current_queue_length,
          bed_occupancy_pct: stats.bed_occupancy_pct,
          hour_of_day: now.getHours(),
        }),
      ])
      setWaitTime(waitRes.data)
      setRisk(riskRes.data)

      const recRes = await api.post('/predictions/staffing-recommendation', {
        department_id: selected,
        current_load: stats.current_queue_length,
        staff_on_duty: stats.staff_on_duty_count,
        predicted_risk: riskRes.data.risk_score,
      })
      setRecommendation(recRes.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <TopBar title="AI Predictions" />

      <div className="flex items-center gap-3 mb-6">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="glass-card rounded-xl px-4 py-2.5 text-sm outline-none"
        >
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <button
          onClick={runPredictions}
          disabled={!stats || loading}
          className="px-4 py-2.5 rounded-xl text-sm font-semibold text-white disabled:opacity-50"
          style={{ background: 'var(--cf-cyan-strong)' }}
        >
          {loading ? 'Running model…' : 'Run predictions'}
        </button>
      </div>

      {!stats ? (
        <SkeletonLoader rows={3} />
      ) : (
        <div className="grid md:grid-cols-3 gap-5">
          <div className="glass-card rounded-2xl p-5 flex flex-col items-center justify-center">
            <BrainCircuit size={22} style={{ color: 'var(--cf-cyan-strong)' }} className="mb-2" />
            <p className="text-sm mb-1" style={{ color: 'var(--cf-text-soft)' }}>Predicted Wait Time</p>
            <p className="text-3xl font-bold">
              {waitTime ? Math.round(waitTime.predicted_wait_minutes) : '—'}
              <span className="text-base font-medium ml-1" style={{ color: 'var(--cf-text-soft)' }}>min</span>
            </p>
          </div>

          <RiskGauge score={risk?.risk_score ?? 0} label="Overcrowding Risk (next 1–3h)" />

          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-2">
              <Users2 size={18} style={{ color: 'var(--cf-cyan-strong)' }} />
              <p className="text-sm font-semibold">Staffing Recommendation</p>
            </div>
            <p className="text-sm" style={{ color: 'var(--cf-text-soft)' }}>
              {recommendation?.recommendation || 'Run predictions to get a recommendation.'}
            </p>
          </div>
        </div>
      )}

      {user?.role === 'ADMIN' && metrics && (
        <div className="glass-card rounded-2xl p-5 mt-6">
          <div className="flex items-center gap-2 mb-4">
            <Gauge size={18} style={{ color: 'var(--cf-cyan-strong)' }} />
            <p className="font-semibold">Model Accuracy (validation metrics)</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {Object.entries(metrics).map(([key, m]) => (
              <div key={key} className="rounded-xl p-4" style={{ background: 'var(--cf-surface-soft)' }}>
                <p className="text-xs uppercase tracking-wide mb-2" style={{ color: 'var(--cf-text-soft)' }}>
                  {key.replace('_', ' ')}
                </p>
                {m ? (
                  <div className="flex gap-4 text-sm">
                    <span>MAE: <b>{m.mae}</b></span>
                    <span>RMSE: <b>{m.rmse}</b></span>
                    <span>n = {m.sample_size}</span>
                  </div>
                ) : (
                  <p className="text-sm" style={{ color: 'var(--cf-text-soft)' }}>No validated predictions yet.</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
