import { useEffect, useState, useCallback } from 'react'
import { AlertTriangle, Check } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import SkeletonLoader from '../components/SkeletonLoader'
import { useToast } from '../context/ToastContext'

const SEVERITY_STYLE = {
  amber: { bg: 'bg-amber-500/10', text: 'text-amber-500' },
  red: { bg: 'bg-red-500/10', text: 'text-red-500' },
}

export default function AlertsLog() {
  const { pushToast } = useToast()
  const [alerts, setAlerts] = useState(null)

  const load = useCallback(() => {
    api.get('/alerts/all').then((res) => setAlerts(res.data.results ?? res.data))
  }, [])

  useEffect(() => { load() }, [load])

  const acknowledge = async (id) => {
    await api.post(`/alerts/${id}/acknowledge`)
    pushToast('Alert acknowledged.', 'success')
    load()
  }

  return (
    <div className="p-6">
      <TopBar title="Alerts Log" />

      {!alerts ? <SkeletonLoader rows={5} /> : alerts.length === 0 ? (
        <div className="glass-card rounded-2xl p-10 text-center" style={{ color: 'var(--cf-text-soft)' }}>
          No alerts — all departments within normal thresholds.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {alerts.map((a) => {
            const style = SEVERITY_STYLE[a.severity] ?? SEVERITY_STYLE.amber
            return (
              <div key={a.id} className={`glass-card rounded-2xl p-4 flex items-center gap-4 ${a.acknowledged_at ? 'opacity-60' : ''}`}>
                <div className={`p-2.5 rounded-xl ${style.bg}`}>
                  <AlertTriangle size={18} className={style.text} />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">{a.message}</p>
                  <p className="text-xs" style={{ color: 'var(--cf-text-soft)' }}>
                    {a.department_name} · {a.alert_type.replace('_', ' ')} · {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
                {!a.acknowledged_at && (
                  <button
                    onClick={() => acknowledge(a.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"
                    style={{ background: 'rgba(20,201,201,0.15)', color: 'var(--cf-cyan-strong)' }}
                  >
                    <Check size={14} /> Acknowledge
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
