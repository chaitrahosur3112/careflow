import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Clock, HeartPulse } from 'lucide-react'
import api from '../lib/api'

const LOAD_COLOR = {
  low: { text: 'text-emerald-400', bg: 'bg-emerald-500/15', label: 'Low load' },
  medium: { text: 'text-amber-400', bg: 'bg-amber-500/15', label: 'Moderate load' },
  high: { text: 'text-red-400', bg: 'bg-red-500/15', label: 'High load' },
}

export default function KioskView() {
  const [waitTimes, setWaitTimes] = useState(null)

  useEffect(() => {
    const load = () => api.get('/kiosk/wait-times').then((res) => setWaitTimes(res.data)).catch(() => {})
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-12" style={{ background: 'var(--cf-navy)', color: '#eef2ff' }}>
      <div className="flex items-center gap-2 mb-2">
        <HeartPulse size={28} style={{ color: 'var(--cf-cyan)' }} />
        <span className="text-2xl font-bold">CareFlow</span>
      </div>
      <p className="text-sm text-slate-400 mb-10">Estimated wait times — updated live</p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 w-full max-w-5xl">
        {!waitTimes ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-2xl p-6 animate-pulse bg-white/5 h-32" />
          ))
        ) : (
          waitTimes.map((dept) => {
            const style = LOAD_COLOR[dept.load_level] ?? LOAD_COLOR.low
            return (
              <motion.div
                key={dept.department_name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl p-6 border border-white/10 bg-white/5 backdrop-blur"
              >
                <p className="text-lg font-semibold mb-3">{dept.department_name}</p>
                <div className="flex items-center gap-2 mb-3">
                  <Clock size={20} style={{ color: 'var(--cf-cyan)' }} />
                  <span className="text-3xl font-bold">{Math.round(dept.estimated_wait_minutes)}</span>
                  <span className="text-slate-400 text-sm">min estimated wait</span>
                </div>
                <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${style.bg} ${style.text}`}>
                  {style.label}
                </span>
              </motion.div>
            )
          })
        )}
      </div>

      <p className="text-xs text-slate-500 mt-10 max-w-md text-center">
        Estimates only, based on current department load. Actual wait time may vary by
        triage priority. Please speak with reception if your condition changes.
      </p>
    </div>
  )
}
