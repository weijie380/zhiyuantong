import { Star } from 'lucide-react'
import GradientBadge from './GradientBadge.jsx'
import MiniTrend from './MiniTrend.jsx'

export default function SchoolCard({ item, isFav, onToggleFav, onView }) {
  const { school, major, baseRank, userRank, probability, years, gradient } = item
  const probColor = gradient === 'reach' ? 'var(--color-reach)'
    : gradient === 'stable' ? 'var(--color-stable)' : 'var(--color-safe)'

  return (
    <div style={{
      background: 'var(--color-card)', border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-3)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--sp-3)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 'var(--fs-15)', fontWeight: 600 }}>{school.name}</span>
            {school.level && (
              <span style={{ fontSize: 'var(--fs-12)', color: 'var(--color-primary)',
                border: '1px solid var(--color-primary)', borderRadius: 'var(--radius-sm)', padding: '0 var(--sp-1)' }}>
                {school.level}
              </span>
            )}
            <GradientBadge gradient={gradient} />
          </div>
          <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginTop: 'var(--sp-1)' }}>
            {major}{school.province ? ` · ${school.province}` : ''}{school.nature ? ` · ${school.nature}` : ''}
          </div>
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ color: probColor, fontWeight: 600 }}>录取概率 {Math.round(probability * 100)}%</div>
          <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', fontVariantNumeric: 'tabular-nums' }}>
            你 {userRank.toLocaleString()} / 该专业 {baseRank.toLocaleString()}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 'var(--sp-3)' }}>
        <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>5年位次走势</div>
        <MiniTrend years={years} userRank={userRank} />
      </div>

      <div style={{ marginTop: 'var(--sp-3)', display: 'flex', gap: 'var(--sp-2)' }}>
        <button onClick={() => onView(school.id)}
          style={{ background: 'var(--color-card)', color: 'var(--color-foreground)',
            border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
            padding: 'var(--sp-1) var(--sp-3)' }}>
          查看详情
        </button>
        <button onClick={() => onToggleFav(item)}
          style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)', padding: 'var(--sp-1) var(--sp-3)',
            color: isFav ? 'var(--color-accent)' : 'var(--color-foreground)',
            display: 'inline-flex', alignItems: 'center', gap: 'var(--sp-1)' }}>
          <Star size={14} fill={isFav ? 'currentColor' : 'none'} />
          {isFav ? '已收藏' : '收藏'}
        </button>
      </div>
    </div>
  )
}
