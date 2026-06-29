import { Sparkles, Search, Star, GraduationCap, LogOut } from 'lucide-react'

const NAV = [
  { key: 'recommend', label: '智能推荐', icon: Sparkles },
  { key: 'search', label: '学校查询', icon: Search },
  { key: 'favorites', label: '我的收藏', icon: Star },
]

export default function Sidebar({ active, onNavigate, user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <GraduationCap size={22} />
        志愿通
      </div>
      <div className="sidebar-nav">
        {NAV.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => onNavigate(key)}
            className={active === key ? 'sidebar-btn active' : 'sidebar-btn'}>
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </div>
      <div className="sidebar-footer">
        <div className="sidebar-user-label">当前用户</div>
        <div className="sidebar-user-row">
          <span className="sidebar-username">{user}</span>
          <button onClick={onLogout} title="登出" className="sidebar-logout">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
