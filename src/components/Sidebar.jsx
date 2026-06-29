import { Sparkles, Search, Star, GraduationCap, LogOut } from 'lucide-react'

const NAV = [
  { key: 'recommend', label: '智能推荐', icon: Sparkles },
  { key: 'search', label: '学校查询', icon: Search },
  { key: 'favorites', label: '我的收藏', icon: Star },
]

export default function Sidebar({ active, onNavigate, user, onLogout }) {
  return (
    <aside style={{
      width: 200, flexShrink: 0, background: 'var(--color-card)',
      borderRight: '1px solid var(--color-border)', padding: 'var(--sp-4)',
      display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)',
      position: 'sticky', top: 0, alignSelf: 'flex-start',
      maxHeight: '100dvh', overflowY: 'auto',
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

      {/* 用户信息 + 登出，底部固定 */}
      <div style={{ marginTop: 'auto', paddingTop: 'var(--sp-4)', borderTop: '1px solid var(--color-border)' }}>
        <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-2)' }}>
          当前用户
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--sp-2)' }}>
          <span style={{ fontSize: 'var(--fs-14)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {user}
          </span>
          <button onClick={onLogout} title="登出"
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              background: 'none', border: 'none', color: 'var(--color-muted-foreground)',
              width: 32, height: 32, padding: 0, minHeight: 32, flexShrink: 0 }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--color-destructive)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--color-muted-foreground)'}>
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
