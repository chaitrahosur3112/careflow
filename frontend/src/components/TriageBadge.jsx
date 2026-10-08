const CONFIG = {
  P1: { label: 'P1 Critical', bg: 'bg-red-500/15', text: 'text-red-500', ring: 'ring-red-500/30' },
  P2: { label: 'P2 Urgent', bg: 'bg-amber-500/15', text: 'text-amber-500', ring: 'ring-amber-500/30' },
  P3: { label: 'P3 Standard', bg: 'bg-emerald-500/15', text: 'text-emerald-500', ring: 'ring-emerald-500/30' },
}

export default function TriageBadge({ level }) {
  const c = CONFIG[level] ?? CONFIG.P3
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${c.bg} ${c.text} ${c.ring}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {c.label}
    </span>
  )
}
