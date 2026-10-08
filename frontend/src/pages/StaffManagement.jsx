import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'

export default function StaffManagement() {
  const { pushToast } = useToast()
  const [shifts, setShifts] = useState(null)
  const [departments, setDepartments] = useState([])
  const [staffUsers, setStaffUsers] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ staff_member: '', department: '', shift_start: '', shift_end: '' })

  const load = () => api.get('/staff/all').then((res) => setShifts(res.data.results ?? res.data))

  useEffect(() => {
    load()
    api.get('/departments/all').then((res) => setDepartments(res.data.results ?? res.data))
    api.get('/users/all').then((res) => setStaffUsers(res.data.results ?? res.data)).catch(() => {})
  }, [])

  const toggleDuty = async (shift) => {
    await api.patch(`/staff/${shift.id}/duty-status`, { is_on_duty: !shift.is_on_duty })
    load()
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await api.post('/staff/all', form)
      pushToast('Shift scheduled.', 'success')
      setModalOpen(false)
      load()
    } catch {
      pushToast('Could not schedule shift — check the staff member ID and times.', 'warning')
    }
  }

  return (
    <div className="p-6">
      <TopBar title="Staff Management" />
      <button
        onClick={() => setModalOpen(true)}
        className="mb-5 flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold text-sm"
        style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}
      >
        <Plus size={16} /> Schedule Shift
      </button>

      {shifts && (
        <div className="glass-card rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b" style={{ borderColor: 'var(--cf-border)', color: 'var(--cf-text-soft)' }}>
                <th className="px-5 py-3 font-medium">Staff Member</th>
                <th className="px-5 py-3 font-medium">Department</th>
                <th className="px-5 py-3 font-medium">Shift</th>
                <th className="px-5 py-3 font-medium">On Duty</th>
              </tr>
            </thead>
            <tbody>
              {shifts.map((s) => (
                <tr key={s.id} className="border-b last:border-0" style={{ borderColor: 'var(--cf-border)' }}>
                  <td className="px-5 py-3">{staffUsers.find((u) => u.id === s.staff_member)?.first_name
                    ? `${staffUsers.find((u) => u.id === s.staff_member).first_name} ${staffUsers.find((u) => u.id === s.staff_member).last_name}`
                    : s.staff_member}</td>
                  <td className="px-5 py-3">{departments.find((d) => d.id === s.department)?.name || s.department}</td>
                  <td className="px-5 py-3 text-xs">
                    {new Date(s.shift_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} –{' '}
                    {new Date(s.shift_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-5 py-3">
                    <button
                      onClick={() => toggleDuty(s)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={s.is_on_duty
                        ? { background: 'rgba(22,163,74,0.15)', color: 'var(--cf-emerald)' }
                        : { background: 'var(--cf-border)', color: 'var(--cf-text-soft)' }}
                    >
                      {s.is_on_duty ? 'On duty' : 'Off duty'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Schedule Shift">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Staff member</label>
            <select required value={form.staff_member} onChange={(e) => setForm({ ...form, staff_member: e.target.value })}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }}>
              <option value="">Select…</option>
              {staffUsers.filter((u) => u.role === 'DOCTOR' || u.role === 'NURSE').map((u) => (
                <option key={u.id} value={u.id}>{u.first_name} {u.last_name} ({u.role})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Department</label>
            <select required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }}>
              <option value="">Select…</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Shift start</label>
              <input type="datetime-local" required value={form.shift_start} onChange={(e) => setForm({ ...form, shift_start: e.target.value })}
                className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }} />
            </div>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Shift end</label>
              <input type="datetime-local" required value={form.shift_end} onChange={(e) => setForm({ ...form, shift_end: e.target.value })}
                className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }} />
            </div>
          </div>
          <button type="submit" className="w-full rounded-xl py-2.5 font-semibold" style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}>
            Schedule
          </button>
        </form>
      </Modal>
    </div>
  )
}
