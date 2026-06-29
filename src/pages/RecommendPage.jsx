import { useState } from 'react'
import { loadSchools, loadMultiYear } from '../lib/dataLoader.js'
import { recommend, aggregateRecords } from '../lib/recommend.js'
import { favorites } from '../lib/storage.js'
import SchoolCard from '../components/SchoolCard.jsx'
import Skeleton from '../components/Skeleton.jsx'

const YEARS = [2021, 2022, 2023, 2024, 2025]
const TABS = [
  { key: 'reach', label: '冲' },
  { key: 'stable', label: '稳' },
  { key: 'safe', label: '保' },
]
const TAB_COLOR = {
  reach: 'var(--color-reach)', stable: 'var(--color-stable)', safe: 'var(--color-safe)',
}
const TAB_BG = {
  reach: 'var(--color-reach-bg)', stable: 'var(--color-stable-bg)', safe: 'var(--color-safe-bg)',
}

export default function RecommendPage({ onOpenSchool }) {
  const [subject, setSubject] = useState('physics')
  const [rank, setRank] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [tab, setTab] = useState('reach')
  const [favVersion, setFavVersion] = useState(0)

  const onGenerate = async () => {
    const userRank = Number(rank)
    if (!userRank || userRank <= 0) return
    setLoading(true); setResult(null)
    try {
      const schoolsMap = await loadSchools()
      const flatRecords = await loadMultiYear(subject, YEARS)
      const records5y = aggregateRecords(flatRecords)
      const res = recommend({ userRank, subject, records5y, schools: schoolsMap })
      setResult(res); setTab('reach')
    } finally { setLoading(false) }
  }

  const toggleFav = (item) => {
    if (favorites.has(item.school.id, item.major)) favorites.remove(item.school.id, item.major)
    else favorites.add({ schoolId: item.school.id, schoolName: item.school.name, major: item.major, gradient: item.gradient, userRank: item.userRank })
    setFavVersion(v => v + 1)
  }

  const items = result ? result[tab] : []

  return (
    <div>
      {/* 输入区 */}
      <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ fontWeight: 600, marginBottom: 'var(--sp-3)' }}>输入你的高考信息</div>
        <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
          <label style={{ flex: 1, minWidth: 140 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>科类</div>
            <select value={subject} onChange={e => setSubject(e.target.value)}
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
              <option value="physics">物理类</option>
              <option value="history">历史类</option>
            </select>
          </label>
          <label style={{ flex: 1, minWidth: 140 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>高考位次</div>
            <input type="number" value={rank} onChange={e => setRank(e.target.value)} placeholder="如 15000"
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', fontVariantNumeric: 'tabular-nums' }} />
          </label>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={onGenerate} disabled={loading || !rank}
              style={{ background: 'var(--color-accent)', color: 'var(--color-on-accent)',
                border: 'none', borderRadius: 'var(--radius-sm)', padding: 'var(--sp-2) var(--sp-4)',
                fontWeight: 600, opacity: (loading || !rank) ? 0.5 : 1 }}>
              {loading ? '生成中...' : '生成方案'}
            </button>
          </div>
        </div>
      </div>

      {/* 梯度统计 */}
      {result && (
        <div style={{ display: 'flex', gap: 'var(--sp-2)', marginBottom: 'var(--sp-3)' }}>
          {TABS.map(t => (
            <div key={t.key} style={{ flex: 1, background: TAB_BG[t.key], border: `1px solid ${TAB_COLOR[t.key]}`,
              borderRadius: 'var(--radius-sm)', padding: 'var(--sp-2) var(--sp-3)' }}>
              <div style={{ fontSize: 'var(--fs-12)', color: TAB_COLOR[t.key], fontWeight: 600 }}>{t.label} · {result[t.key].length} 所</div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 切换 */}
      {result && (
        <div style={{ borderBottom: '2px solid var(--color-border)', marginBottom: 'var(--sp-3)' }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              style={{
                padding: 'var(--sp-2) var(--sp-4)', border: 'none', background: 'transparent',
                borderBottom: tab === t.key ? `2px solid ${TAB_COLOR[t.key]}` : '2px solid transparent',
                color: tab === t.key ? TAB_COLOR[t.key] : 'var(--color-muted-foreground)',
                fontWeight: tab === t.key ? 600 : 400, marginBottom: -2,
                transition: `border-color var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease)`,
              }}>
              {t.label}
            </button>
          ))}
        </div>
      )}

      {/* 列表 */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
          {[0,1,2].map(i => <Skeleton key={i} height={120} />)}
        </div>
      )}
      {!loading && result && items.length === 0 && (
        <div style={{ padding: 'var(--sp-8)', textAlign: 'center', color: 'var(--color-muted-foreground)' }}>
          该档位暂无匹配学校
        </div>
      )}
      {!loading && items.map((item, i) => (
        <SchoolCard key={`${item.school.id}-${item.major}`} item={item}
          isFav={favorites.has(item.school.id, item.major)}
          onToggleFav={toggleFav} onView={onOpenSchool} />
      ))}
    </div>
  )
}
