const META = {
  reach:  { label: '冲', color: 'var(--color-reach)', bg: 'var(--color-reach-bg)' },
  stable: { label: '稳', color: 'var(--color-stable)', bg: 'var(--color-stable-bg)' },
  safe:   { label: '保', color: 'var(--color-safe)', bg: 'var(--color-safe-bg)' },
}

export default function GradientBadge({ gradient }) {
  const m = META[gradient]
  if (!m) return null
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 'var(--sp-1)',
      padding: '2px var(--sp-2)', borderRadius: 'var(--radius-sm)',
      color: m.color, backgroundColor: m.bg, fontSize: 'var(--fs-12)', fontWeight: 600,
    }}>
      {m.label}
    </span>
  )
}
