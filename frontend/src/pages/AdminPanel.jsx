import { useEffect, useState, useCallback } from 'react'
import { ShieldCheck, UserPlus } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import Modal from '../components/Modal'
import SkeletonLoader from '../components/SkeletonLoader'
import { useToast } from '../context/ToastContext'

const ROLES = ['ADMIN', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMINISTRATOR']
const EMPTY_FORM = { username: '', email: '', password: '', first_name: '', last_name: '', role: 'NURSE', department: '' }

export default function AdminPanel() {
  const { pushToast } = useToast()
  const [users, setUsers] = useState(null)
  const [departments, setDepartments] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    api.get('/users/all').then((res) => setUsers(res.data.results ?? res.data))
  }, [])

  useEffect(() => {
    load()
    api.get('/departments/all').then((res) => setDepartments(res.data.results ?? res.data))
  }, [load])

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/auth/register', { ...form, department: form.department || null })
      pushToast('Staff account created.', 'success')
      setOpen(false)
      setForm(EMPTY_FORM)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create account — check the fields.')
    }
  }

  const deactivate = async (id) => {
    await api.delete(`/users/${id}`)
    pushToast('Staff account deactivated.', 'success')
    load()
  }

  return (
    <div className="p-6">
      <TopBar title="Admin Panel" />

      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <ShieldCheck size={20} style={{ color: 'var(--cf-cyan-strong)' }} />
          <p className="font-semibold">User Management</p>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white"
          style={{ background: 'var(--cf-cyan-strong)' }}
        >
          <UserPlus size={16} /> New staff account
        </button>
      </div>

      {!users ? <SkeletonLoader rows={4} /> : (
        <div className="glass-card rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b" style={{ borderColor: 'var(--cf-border)', color: 'var(--cf-text-soft)' }}>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b last:border-0" style={{ borderColor: 'var(--cf-border)' }}>
                  <td className="px-5 py-3 font-medium">{u.first_name} {u.last_name}</td>
                  <td className="px-5 py-3">{u.email}</td>
                  <td className="px-5 py-3">{u.role?.replace('_', ' ')}</td>
                  <td className="px-5 py-3">
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${u.is_active_staff ? 'bg-emerald-500/15 text-emerald-500' : 'bg-red-500/15 text-red-500'}`}>
                      {u.is_active_staff ? 'Active' : 'Deactivated'}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    {u.is_active_staff && (
                      <button onClick={() => deactivate(u.id)} className="text-xs font-medium text-red-500 hover:underline">
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="New staff account">
        <form onSubmit={submit} className="flex flex-col gap-3">
          {error && <p className="text-sm text-red-500">{error}</p>}
          <input required placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none" />
          <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none" />
          <input required type="password" minLength={8} placeholder="Temporary password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none" />
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="First name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none" />
            <input placeholder="Last name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none" />
          </div>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none">
            {ROLES.map((r) => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
          </select>
          {form.role !== 'ADMIN' && form.role !== 'HOSPITAL_ADMINISTRATOR' && (
            <select value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="rounded-xl px-4 py-2.5 text-sm glass-card outline-none">
              <option value="">Assign department…</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          )}
          <button type="submit" className="mt-1 px-4 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: 'var(--cf-cyan-strong)' }}>
            Create account
          </button>
        </form>
      </Modal>
    </div>
  )
}
