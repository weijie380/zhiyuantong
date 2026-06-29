import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'
import Sidebar from './components/Sidebar.jsx'
import RecommendPage from './pages/RecommendPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import SchoolDetailPage from './pages/SchoolDetailPage.jsx'
import FavoritesPage from './pages/FavoritesPage.jsx'

export default function App() {
  const [page, setPage] = useState('recommend')
  const [detailId, setDetailId] = useState(null)
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    const saved = localStorage.getItem('zyt_theme')
    if (saved) setTheme(saved)
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) setTheme('dark')
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('zyt_theme', theme)
  }, [theme])

  const openSchool = (id) => { setDetailId(id); setPage('detail') }

  const renderPage = () => {
    if (page === 'detail' && detailId)
      return <SchoolDetailPage schoolId={detailId} onBack={() => setPage('recommend')} />
    if (page === 'search') return <SearchPage onOpenSchool={openSchool} />
    if (page === 'favorites') return <FavoritesPage onOpenSchool={openSchool} />
    return <RecommendPage onOpenSchool={openSchool} />
  }

  return (
    <div style={{ display: 'flex', minHeight: '100dvh', background: 'var(--color-background)' }}>
      <Sidebar active={page === 'detail' ? 'recommend' : page} onNavigate={setPage} />
      <main style={{ flex: 1, maxWidth: 1100, margin: '0 auto', padding: 'var(--sp-6)', minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 'var(--sp-4)' }}>
          <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--color-card)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)', width: 36, height: 36, padding: 0, minHeight: 36 }}
            title={theme === 'light' ? '切换暗色模式' : '切换亮色模式'}>
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
        {renderPage()}
      </main>
    </div>
  )
}
