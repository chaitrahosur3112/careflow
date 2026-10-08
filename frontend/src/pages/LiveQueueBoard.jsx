import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import TriageBadge from '../components/TriageBadge'
import SkeletonLoader from '../components/SkeletonLoader'
import useQueueSocket from '../lib/useQueueSocket'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const STATUS_LABEL = { waiting: 'Waiting', in_treatment: 'In Treatment', discharged: 'Discharged' }

export default function LiveQueueBoard() {
  const { user } = useAuth()
  const { pushToast } = useToast()
  const [departments, setDepartments] = useState([])
  const [selectedDept, setSelectedDept] = useState(user?.department || '')
  const [patients, setPatients] = useState(null)

  useEffect(() => {
    api.get('/departments/all').then((res) => {
      const list = res.data.results ?? res.data
      setDepartments(list)
      if (!selectedDept && list.length) setSelectedDept(list[0].id)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadQueue = useCallback(async () => {
    if (!selectedDept) return
    const res = await api.get(`/departments/${selectedDept}/queue`)
    setPatients(res.data.results ?? res.data)
  }, [selectedDept])

  useEffect(() => {
    setPatients(null)
    loadQueue()
  }, [loadQueue])

  useQueueSocket(selectedDept, useCallback(() => {
    loadQueue()
    pushToast('Queue updated — a patient moved.', 'info')
  }, [loadQueue, pushToast]))

  const updateStatus = async (patientId, status) => {
    await api.patch(`/patients/${patientId}/status`, { status })
    loadQueue()
  }

  const discharge = async (patientId) => {
    await api.post(`/patients/${patientId}/discharge`)
    pushToast('Patient discharged.', 'success')
    loadQueue()
  }

  return (
    <div className="p-6">
      <TopBar title="Live Queue Board" />

      <div className="flex gap-2 mb-5 flex-wrap">
        {departments.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelectedDept(d.id)}
            className="px-4 py-2 rounded-xl text-sm font-medium transition-colors"
            style={
              selectedDept === d.id
                ? { background: 'var(--cf-cyan-strong)', color: '#fff' }
                : { background: 'var(--cf-surface)', border: '1px solid var(--cf-border)', color: 'var(--cf-text)' }
            }
          >
            {d.name}
          </button>
        ))}
      </div>

      {!patients ? (
        <SkeletonLoader rows={5} />
      ) : patients.length === 0 ? (
        <div className="glass-card rounded-2xl p-10 text-center" style={{ color: 'var(--cf-text-soft)' }}>
          No patients currently waiting in this department.
        </div>
      ) : (
        <div className="glass-card rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b" style={{ borderColor: 'var(--cf-border)', color: 'var(--cf-text-soft)' }}>
                <th className="px-5 py-3 font-medium">Patient ID</th>
                <th className="px-5 py-3 font-medium">Triage</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Time waiting</th>
                <th className="px-5 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <motion.tr
                  key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="border-b last:border-0" style={{ borderColor: 'var(--cf-border)' }}
                >
                  <td className="px-5 py-3 font-mono text-xs">{p.id.slice(0, 8)}</td>
                  <td className="px-5 py-3"><TriageBadge level={p.triage_level} /></td>
                  <td className="px-5 py-3">{STATUS_LABEL[p.status]}</td>
                  <td className="px-5 py-3">{Math.round(p.time_in_system_minutes)} min</td>
                  <td className="px-5 py-3 flex gap-2">
                    {p.status === 'waiting' && (
                      <button
                        onClick={() => updateStatus(p.id, 'in_treatment')}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium"
                        style={{ background: 'rgba(20,201,201,0.15)', color: 'var(--cf-cyan-strong)' }}
                      >
                        Start treatment
                      </button>
                    )}
                    {p.status !== 'discharged' && (
                      <button
                        onClick={() => discharge(p.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium"
                        style={{ background: 'rgba(22,163,74,0.15)', color: 'var(--cf-emerald)' }}
                      >
                        Discharge
                      </button>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
