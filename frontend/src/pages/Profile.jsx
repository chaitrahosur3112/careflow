import { useState } from 'react'
import { User } from 'lucide-react'
import api from '../lib/api'
import TopBar from '../components/TopBar'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

export default function Profile() {
  const { user, refetch } = useAuth()
  const { pushToast } = useToast()
  const [form, setForm] = useState({ first_name: user?.first_name || '', last_name: user?.last_name || '' })
  const [saving, setSaving] = useState(false)

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.patch('/users/me', form)
      await refetch()
      pushToast('Profile updated.', 'success')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6">
      <TopBar title="Profile & Settings" />

      <div className="glass-card rounded-2xl p-6 max-w-lg">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-full" style={{ background: 'rgba(20,201,201,0.15)' }}>
            <User size={22} style={{ color: 'var(--cf-cyan-strong)' }} />
          </div>
          <div>
            <p className="font-semibold">{user?.username}</p>
            <p className="text-sm" style={{ color: 'var(--cf-text-soft)' }}>{user?.email}</p>
          </div>
        </div>

        <form onSubmit={save} className="flex flex-col gap-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">First name</label>
            <input
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none glass-card"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1.5">Last name</label>
            <input
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              className="w-full rounded-xl px-4 py-2.5 text-sm outline-none glass-card"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1.5">Role</label>
            <input value={user?.role?.replace('_', ' ')} disabled className="w-full rounded-xl px-4 py-2.5 text-sm glass-card opacity-60" />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="mt-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white disabled:opacity-50"
            style={{ background: 'var(--cf-cyan-strong)' }}
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
