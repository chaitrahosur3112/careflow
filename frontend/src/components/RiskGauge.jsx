export default function RiskGauge({ score = 0, label = 'Overcrowding Risk' }) {
  const clamped = Math.max(0, Math.min(100, score))
  const color = clamped >= 95 ? 'var(--cf-red)' : clamped >= 80 ? 'var(--cf-amber)' : 'var(--cf-emerald)'
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (clamped / 100) * circumference

  return (
    <div className="glass-card rounded-2xl p-5 flex flex-col items-center">
      <p className="text-sm mb-2 self-start" style={{ color: 'var(--cf-text-soft)' }}>{label}</p>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="54" fill="none" stroke="var(--cf-border)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r="54" fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          transform="rotate(-90 70 70)" style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="70" y="66" textAnchor="middle" fontSize="26" fontWeight="700" fill="var(--cf-text)">
          {Math.round(clamped)}
        </text>
        <text x="70" y="86" textAnchor="middle" fontSize="11" fill="var(--cf-text-soft)">/ 100</text>
      </svg>
      <p className="text-xs mt-1 font-semibold uppercase tracking-wide" style={{ color }}>
        {clamped >= 95 ? 'Critical' : clamped >= 80 ? 'Warning' : 'Normal'}
      </p>
    </div>
  )
}
