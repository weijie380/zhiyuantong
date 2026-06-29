import { Sparkles, Search, Star, GraduationCap } from 'lucide-react'

const NAV = [
  { key: 'recommend', label: '智能推荐', icon: Sparkles },
  { key: 'search', label: '学校查询', icon: Search },
  { key: 'favorites', label: '我的收藏', icon: Star },
]

export default function Sidebar({ active, onNavigate }) {
  return (
    <aside style={{
      width: 200, flexShrink: 0, background: 'var(--color-card)',
      borderRight: '1px solid var(--color-border)', padding: 'var(--sp-4)',
      display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)',
        fontWeight: 700, fontSize: 'var(--fs-18)', marginBottom: 'var(--sp-4)', color: 'var(--color-primary)' }}>
        <GraduationCap size={22} />
        志愿通
      </div>
      {NAV.map(({ key, label, icon: Icon }) => (
        <button key={key} onClick={() => onNavigate(key)}
          style={{
            display: 'flex', alignItems: 'center', gap: 'var(--sp-2)',
            padding: 'var(--sp-2) var(--sp-3)', borderRadius: 'var(--radius-sm)',
            border: 'none', background: active === key ? 'var(--color-primary)' : 'transparent',
            color: active === key ? 'var(--color-on-primary)' : 'var(--color-foreground)',
            fontWeight: active === key ? 600 : 400, textAlign: 'left',
            transition: `background var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease)`,
          }}>
          <Icon size={18} />
          {label}
        </button>
      ))}
    </aside>
  )
}
