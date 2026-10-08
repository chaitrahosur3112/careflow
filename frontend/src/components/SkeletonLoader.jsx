export default function SkeletonLoader({ full, rows = 3 }) {
  const pulse = (className) => (
    <div className={`animate-pulse rounded-xl bg-black/5 dark:bg-white/5 ${className}`} />
  )

  if (full) {
    return (
      <div className="h-screen w-full flex items-center justify-center" style={{ background: 'var(--cf-surface-soft)' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 rounded-full animate-spin" style={{ borderColor: 'var(--cf-border)', borderTopColor: 'var(--cf-cyan-strong)' }} />
          <p className="text-sm" style={{ color: 'var(--cf-text-soft)' }}>Loading CareFlow…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i}>{pulse('h-16 w-full')}</div>
      ))}
    </div>
  )
}
