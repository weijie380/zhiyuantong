import { useState } from 'react'
import { Star, Download, Trash2 } from 'lucide-react'
import { favorites } from '../lib/storage.js'
import GradientBadge from '../components/GradientBadge.jsx'

export default function FavoritesPage({ onOpenSchool }) {
  const [version, setVersion] = useState(0)
  const refresh = () => setVersion(v => v + 1)
  const list = favorites.getAll()

  const remove = (schoolId, major) => { favorites.remove(schoolId, major); refresh() }

  const exportText = () => {
    const lines = list.map(f =>
      `${f.gradient ? `[${f.gradient}] ` : ''}${f.schoolName} - ${f.major} (位次${f.userRank?.toLocaleString()})`
    )
    const text = `我的志愿收藏\n\n${lines.join('\n')}\n\n生成于 ${new Date().toLocaleString('zh-CN')}`
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = '志愿收藏.txt'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
        <h2 style={{ fontSize: 'var(--fs-18)' }}>我的收藏</h2>
        {list.length > 0 && (
          <button onClick={exportText}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--sp-1)',
              background: 'var(--color-card)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)', padding: 'var(--sp-1) var(--sp-3)' }}>
            <Download size={14} /> 导出
          </button>
        )}
      </div>

      {list.length === 0 ? (
        <div style={{ padding: 'var(--sp-12)', textAlign: 'center', color: 'var(--color-muted-foreground)' }}>
          <Star size={32} style={{ marginBottom: 'var(--sp-3)', opacity: 0.4 }} />
          <div>还没有收藏的学校</div>
          <div style={{ fontSize: 'var(--fs-12)', marginTop: 'var(--sp-2)' }}>在推荐结果或学校详情中点击收藏</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
          {list.map(f => (
            <div key={`${f.schoolId}-${f.major}`}
              style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                    <span style={{ fontWeight: 600 }}>{f.schoolName}</span>
                    {f.gradient && <GradientBadge gradient={f.gradient} />}
                  </div>
                  <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginTop: 'var(--sp-1)' }}>
                    {f.major} · 收藏时位次 {f.userRank?.toLocaleString()}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
                  <button onClick={() => onOpenSchool(f.schoolId)}
                    style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)', padding: 'var(--sp-1) var(--sp-3)' }}>详情</button>
                  <button onClick={() => remove(f.schoolId, f.major)}
                    style={{ display: 'inline-flex', alignItems: 'center', color: 'var(--color-destructive)',
                      background: 'var(--color-card)', border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-sm)', padding: 'var(--sp-1) var(--sp-3)' }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
