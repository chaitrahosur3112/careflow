import { useState, useEffect } from 'react'
import { UserPlus } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import { useToast } from '../context/ToastContext'

const ROLES = ['ADMIN', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMINISTRATOR']

export default function Register() {
  const { pushToast } = useToast()
  const [departments, setDepartments] = useState([])
  const [form, setForm] = useState({
    username: '', email: '', password: '', first_name: '', last_name: '', role: 'NURSE', department: '',
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api.get('/departments/all').then((res) => setDepartments(res.data.results ?? res.data)).catch(() => {})
  }, [])

  const handleChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post('/auth/register', { ...form, department: form.department || null })
      pushToast(`Staff account created for ${form.first_name || form.username}.`, 'success')
      setForm({ username: '', email: '', password: '', first_name: '', last_name: '', role: 'NURSE', department: '' })
    } catch {
      pushToast('Could not create the account — check the fields and try again.', 'warning')
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass = 'mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none focus:border-cyan-500'

  return (
    <div className="p-6 max-w-2xl">
      <TopBar title="Register Staff" />
      <form onSubmit={handleSubmit} className="glass-card rounded-2xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>First name</label>
            <input required value={form.first_name} onChange={handleChange('first_name')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }} />
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Last name</label>
            <input required value={form.last_name} onChange={handleChange('last_name')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }} />
          </div>
        </div>
        <div>
          <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Username</label>
          <input required value={form.username} onChange={handleChange('username')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }} />
        </div>
        <div>
          <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Email</label>
          <input type="email" required value={form.email} onChange={handleChange('email')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }} />
        </div>
        <div>
          <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Temporary password</label>
          <input type="password" required minLength={8} value={form.password} onChange={handleChange('password')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Role</label>
            <select value={form.role} onChange={handleChange('role')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }}>
              {ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Department</label>
            <select value={form.department} onChange={handleChange('department')} className={inputClass} style={{ borderColor: 'var(--cf-border)' }}>
              <option value="">— none —</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        </div>
        <button
          type="submit" disabled={submitting}
          className="flex items-center gap-2 rounded-xl px-5 py-2.5 font-semibold disabled:opacity-60"
          style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}
        >
          <UserPlus size={16} /> {submitting ? 'Creating…' : 'Create account'}
        </button>
      </form>
    </div>
  )
}
