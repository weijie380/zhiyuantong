import { useState, useEffect } from 'react'
import { Moon, Sun, LogOut } from 'lucide-react'
import Sidebar from './components/Sidebar.jsx'
import RecommendPage from './pages/RecommendPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import SchoolDetailPage from './pages/SchoolDetailPage.jsx'
import FavoritesPage from './pages/FavoritesPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import BackToTop from './components/BackToTop.jsx'
import { auth } from './lib/auth.js'
import { userInput } from './lib/storage.js'

export default function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('recommend')
  const [detailId, setDetailId] = useState(null)
  const [theme, setTheme] = useState('light')
  const [recState, setRecState] = useState({ subject: 'physics', rank: '', result: null })

  // 初始化：检查登录态 + 主题 + 已保存的输入
  useEffect(() => {
    setUser(auth.current())
    const saved = localStorage.getItem('zyt_theme')
    if (saved) setTheme(saved)
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) setTheme('dark')
  }, [])

  // 登录成功后加载该用户的输入
  useEffect(() => {
    if (user) {
      const saved = userInput.get()
      if (saved) setRecState(saved)
    }
  }, [user])

  // 切换页面时自动回到顶部
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }) }, [page, detailId])

  // 主题应用
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('zyt_theme', theme)
  }, [theme])

  // 推荐状态变化时自动保存（用函数式更新避免 stale closure）
  const handleRecStateChange = (next) => {
    setRecState(prev => {
      const val = typeof next === 'function' ? next(prev) : next
      if (user) userInput.save(val)
      return val
    })
  }

  const onLogin = (username) => { setUser(username); setPage('recommend') }

  const onLogout = () => { auth.logout(); setUser(null); setRecState({ subject: 'physics', rank: '', result: null, tab: 'reach' }) }

  // 未登录显示登录页
  if (!user) return <LoginPage onLogin={onLogin} />

  const openSchool = (id) => { setDetailId(id); setPage('detail') }

  const isVisible = (p) => {
    if (p === 'detail') return page === 'detail' && !!detailId
    return page === p
  }
  const displayStyle = (p) => isVisible(p) ? undefined : 'none'
  const activeNav = page === 'detail' ? 'recommend' : page

  const renderPage = () => {
    switch (page) {
      case 'detail':
        return detailId ? <SchoolDetailPage schoolId={detailId} onBack={() => setPage('recommend')} /> : null
      case 'search':
        return <SearchPage onOpenSchool={openSchool} />
      case 'favorites':
        return <FavoritesPage onOpenSchool={openSchool} />
      default:
        return <RecommendPage savedState={recState} onStateChange={handleRecStateChange} onOpenSchool={openSchool} />
    }
  }

  return (
    <div className="app-layout">
      <Sidebar active={activeNav} onNavigate={setPage} user={user} onLogout={onLogout} />
      <main className="app-main">
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 'var(--sp-4)' }}>
          <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
            className="theme-toggle"
            title={theme === 'light' ? '切换暗色模式' : '切换亮色模式'}>
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
        {renderPage()}
      </main>
      <BackToTop />
    </div>
  )
}
