import { motion } from 'framer-motion'

const TONE_COLOR = {
  default: 'var(--cf-cyan-strong)',
  emerald: 'var(--cf-emerald)',
  amber: 'var(--cf-amber)',
  red: 'var(--cf-red)',
}

export default function StatCard({ icon: Icon, label, value, tone = 'default', suffix }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-5 flex items-start justify-between"
    >
      <div>
        <p className="text-sm mb-1" style={{ color: 'var(--cf-text-soft)' }}>{label}</p>
        <p className="text-3xl font-bold tracking-tight">
          {value}
          {suffix && <span className="text-base font-medium ml-1" style={{ color: 'var(--cf-text-soft)' }}>{suffix}</span>}
        </p>
      </div>
      {Icon && (
        <div
          className="rounded-xl p-2.5"
          style={{ backgroundColor: `color-mix(in srgb, ${TONE_COLOR[tone]} 15%, transparent)` }}
        >
          <Icon size={20} style={{ color: TONE_COLOR[tone] }} />
        </div>
      )}
    </motion.div>
  )
}
