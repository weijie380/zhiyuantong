// MiniTrend — 5 年位次走势 SVG 折线，含用户位次参考线
export default function MiniTrend({ years, userRank }) {
  const ranks = years.map(y => y.minRank).filter(r => r != null && r > 0)
  if (ranks.length < 2) return <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>数据不足</div>

  const W = 200, H = 40, PAD = 8
  const minR = Math.min(...ranks, userRank ?? Infinity)
  const maxR = Math.max(...ranks, userRank ?? -Infinity)
  const span = Math.max(1, maxR - minR)
  const x = i => PAD + (i * (W - 2 * PAD)) / (years.length - 1)
  // 位次越小=排名越靠前=上方
  const y = r => H - PAD - ((r - minR) / span) * (H - 2 * PAD)

  const pts = years.map((yy, i) => `${x(i)},${y(yy.minRank)}`).join(' ')
  const userY = userRank != null ? y(userRank) : null

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: H }}>
      {userY != null && (
        <line x1={PAD} y1={userY} x2={W - PAD} y2={userY}
          stroke="var(--color-secondary)" strokeWidth="1" strokeDasharray="3,2" />
      )}
      <polyline points={pts} fill="none" stroke="var(--color-primary)" strokeWidth="1.5" />
      {years.map((yy, i) => (
        <circle key={i} cx={x(i)} cy={y(yy.minRank)} r="2" fill="var(--color-primary)" />
      ))}
    </svg>
  )
}
