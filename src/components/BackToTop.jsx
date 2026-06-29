import { useState, useEffect } from 'react'
import { ArrowUp } from 'lucide-react'

// BackToTop — 悬浮在右下角的返回顶部按钮，滚动超过 400px 时显示
export default function BackToTop() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 400)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  if (!visible) return null

  return (
    <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      aria-label="返回顶部"
      style={{
        position: 'fixed', right: 24, bottom: 24, zIndex: 1000,
        width: 44, height: 44, borderRadius: '50%',
        background: 'var(--color-primary)', color: 'var(--color-on-primary)',
        border: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)', cursor: 'pointer', padding: 0,
        transition: 'opacity 0.2s, transform 0.2s',
      }}
      onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}>
      <ArrowUp size={20} />
    </button>
  )
}
