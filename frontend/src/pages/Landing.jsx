import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, BrainCircuit, ShieldCheck, Radar } from 'lucide-react'

const FEATURES = [
  [Activity, 'Real-time queue visibility', 'Live department boards update the moment a patient is admitted, moved, or discharged.'],
  [BrainCircuit, 'AI wait-time prediction', 'Gradient Boosting models forecast wait times per triage level and department.'],
  [Radar, 'Overcrowding forecasting', 'Time-series risk scoring flags amber/red capacity before it becomes a crisis.'],
  [ShieldCheck, 'Role-based, audited, anonymized', 'Every action is logged. Every patient record is anonymized. Every role sees only what it should.'],
]

export default function Landing() {
  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(180deg, var(--cf-navy) 0%, var(--cf-navy-light) 100%)', color: '#eef2ff' }}>
      <header className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <p className="text-xl font-bold tracking-tight" style={{ color: 'var(--cf-cyan)' }}>CareFlow</p>
        <div className="flex items-center gap-3">
          <Link to="/kiosk" className="text-sm px-4 py-2 rounded-xl hover:bg-white/10 transition-colors">Kiosk View</Link>
          <Link to="/login" className="text-sm px-4 py-2 rounded-xl font-semibold" style={{ background: 'var(--cf-cyan)', color: 'var(--cf-navy)' }}>
            Staff Login
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto px-6 pt-20 pb-24 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight"
        >
          Predict. Allocate.<br />
          <span style={{ color: 'var(--cf-cyan)' }}>Save Lives.</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="mt-6 text-lg max-w-2xl mx-auto" style={{ color: '#93a2c6' }}
        >
          AI-powered patient flow and resource allocation for hospital operations —
          real-time queues, predictive wait times, and early overcrowding alerts.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="mt-10 flex items-center justify-center gap-4"
        >
          <Link to="/login" className="px-6 py-3 rounded-xl font-semibold" style={{ background: 'var(--cf-cyan)', color: 'var(--cf-navy)' }}>
            Staff Login
          </Link>
          <Link to="/kiosk" className="px-6 py-3 rounded-xl font-semibold border border-white/20 hover:bg-white/5">
            View Public Wait Times
          </Link>
        </motion.div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-2 gap-5">
        {FEATURES.map(([Icon, title, desc], i) => (
          <motion.div
            key={title}
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
            className="rounded-2xl p-6 border border-white/10 bg-white/[0.03] backdrop-blur"
          >
            <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ background: 'rgba(20,201,201,0.15)' }}>
              <Icon size={20} style={{ color: 'var(--cf-cyan)' }} />
            </div>
            <h3 className="font-semibold mb-1.5">{title}</h3>
            <p className="text-sm" style={{ color: '#93a2c6' }}>{desc}</p>
          </motion.div>
        ))}
      </section>

      <footer className="max-w-6xl mx-auto px-6 pb-10 text-xs text-center" style={{ color: '#5b6b8c' }}>
        Academic portfolio project — not a certified medical device. No real patient data is used or stored.
      </footer>
    </div>
  )
}
