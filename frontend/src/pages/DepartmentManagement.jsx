import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'

export default function DepartmentManagement() {
  const { pushToast } = useToast()
  const [departments, setDepartments] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState({ name: '', total_beds: 10, occupied_beds: 0 })

  const load = () => api.get('/departments/all').then((res) => setDepartments(res.data.results ?? res.data))

  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await api.post('/departments/all', form)
      pushToast(`${form.name} department added.`, 'success')
      setModalOpen(false)
      setForm({ name: '', total_beds: 10, occupied_beds: 0 })
      load()
    } catch {
      pushToast('Could not create department.', 'warning')
    }
  }

  const updateBeds = async (dept, field, value) => {
    await api.patch(`/departments/${dept.id}`, { [field]: value })
    load()
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <TopBar title="Department Management" />
      </div>
      <button
        onClick={() => setModalOpen(true)}
        className="mb-5 flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold text-sm"
        style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}
      >
        <Plus size={16} /> New Department
      </button>

      {!departments ? null : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((d) => {
            const pct = d.bed_occupancy_pct
            const color = pct >= 95 ? 'var(--cf-red)' : pct >= 80 ? 'var(--cf-amber)' : 'var(--cf-emerald)'
            return (
              <div key={d.id} className="glass-card rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">{d.name}</h3>
                  <span className="text-xs font-semibold px-2 py-1 rounded-full" style={{ background: `color-mix(in srgb, ${color} 15%, transparent)`, color }}>
                    {pct}%
                  </span>
                </div>
                <div className="h-2 rounded-full mb-4 overflow-hidden" style={{ background: 'var(--cf-border)' }}>
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <label className="flex flex-col gap-1">
                    <span style={{ color: 'var(--cf-text-soft)' }}>Total beds</span>
                    <input
                      type="number" min={0} defaultValue={d.total_beds}
                      onBlur={(e) => updateBeds(d, 'total_beds', Number(e.target.value))}
                      className="rounded-lg px-2 py-1.5 border bg-transparent" style={{ borderColor: 'var(--cf-border)' }}
                    />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span style={{ color: 'var(--cf-text-soft)' }}>Occupied</span>
                    <input
                      type="number" min={0} defaultValue={d.occupied_beds}
                      onBlur={(e) => updateBeds(d, 'occupied_beds', Number(e.target.value))}
                      className="rounded-lg px-2 py-1.5 border bg-transparent" style={{ borderColor: 'var(--cf-border)' }}
                    />
                  </label>
                </div>
                <div className="flex justify-between mt-4 text-xs" style={{ color: 'var(--cf-text-soft)' }}>
                  <span>Queue: {d.current_queue_length}</span>
                  <span>Staff on duty: {d.staff_on_duty_count}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New Department">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Name</label>
            <input
              required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }}
            />
          </div>
          <div>
            <label className="text-xs font-medium" style={{ color: 'var(--cf-text-soft)' }}>Total beds</label>
            <input
              type="number" min={0} value={form.total_beds} onChange={(e) => setForm({ ...form, total_beds: Number(e.target.value) })}
              className="mt-1 w-full rounded-xl px-3 py-2.5 bg-transparent border outline-none" style={{ borderColor: 'var(--cf-border)' }}
            />
          </div>
          <button type="submit" className="w-full rounded-xl py-2.5 font-semibold" style={{ background: 'var(--cf-cyan-strong)', color: '#fff' }}>
            Create
          </button>
        </form>
      </Modal>
    </div>
  )
}
