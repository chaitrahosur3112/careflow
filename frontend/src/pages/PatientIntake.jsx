import { useEffect, useState } from 'react'
import { ClipboardPlus } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import TriageBadge from '../components/TriageBadge'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const TRIAGE_OPTIONS = ['P1', 'P2', 'P3']

export default function PatientIntake() {
  const { user } = useAuth()
  const { pushToast } = useToast()
  const [departments, setDepartments] = useState([])
  const [triage, setTriage] = useState('P3')
  const [department, setDepartment] = useState(user?.department || '')
  const [submitting, setSubmitting] = useState(false)
  const [recent, setRecent] = useState([])

  useEffect(() => {
    api.get('/departments/all').then((res) => {
      const list = res.data.results ?? res.data
      setDepartments(list)
      if (!department && list.length) setDepartment(list[0].id)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await api.post('/patients/intake', {
        triage_level: triage,
        department,
        assigned_nurse: user?.id,
      })
      pushToast(`Patient admitted to queue — triage ${triage}.`, 'success')
      setRecent((r) => [res.data, ...r].slice(0, 8))
    } catch {
      pushToast('Could not add patient to queue. Please retry.', 'warning')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="p-6 max-w-3xl">
      <TopBar title="Patient Intake" />

      <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Department</label>
            <select
              value={department} onChange={(e) => setDepartment(e.target.value)}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none focus:border-cyan-500"
              style={{ borderColor: 'var(--cf-border)' }}
            >
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Triage Level</label>
            <div className="flex gap-2 mt-1">
              {TRIAGE_OPTIONS.map((t) => (
                <button
                  type="button" key={t} onClick={() => setTriage(t)}
                  className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors"
                  style={triage === t
                    ? { background: 'var(--cf-cyan-strong)', color: '#fff' }
                    : { border: '1px solid var(--cf-border)', color: 'var(--cf-text)' }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-xs mb-4" style={{ color: 'var(--cf-text-soft)' }}>
          A new anonymized patient ID is generated automatically — no names or personal identifiers are collected.
        </p>

        <button
          type="submit" disabled={submitting}
          className="flex items-center gap-2 rounded-xl px-5 py-2.5 font-semibold disabled:opacity-60"
          style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}
        >
          <ClipboardPlus size={16} /> {submitting ? 'Adding…' : 'Add to queue'}
        </button>
      </form>

      {recent.length > 0 && (
        <div className="glass-card rounded-2xl p-5">
          <h3 className="font-semibold mb-3">Recently admitted this session</h3>
          <div className="space-y-2">
            {recent.map((p) => (
              <div key={p.id} className="flex items-center justify-between text-sm">
                <span className="font-mono text-xs" style={{ color: 'var(--cf-text-soft)' }}>{p.id.slice(0, 8)}</span>
                <TriageBadge level={p.triage_level} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
