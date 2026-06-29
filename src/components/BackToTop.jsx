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
      className="back-to-top">
      <ArrowUp size={20} />
    </button>
  )
}
