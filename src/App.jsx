import { useEffect, useState } from 'react'
import { loadSchoolsArray, loadScoreFile } from './lib/dataLoader.js'

export default function App() {
  const [msg, setMsg] = useState('加载中...')
  useEffect(() => {
    (async () => {
      const schools = await loadSchoolsArray()
      const f = await loadScoreFile('physics', 2024)
      setMsg(`学校${schools.length}所，2024物理记录${f.records.length}条`)
    })().catch(e => setMsg('错误:' + e.message))
  }, [])
  return <div style={{ padding: 24 }}>{msg}</div>
}
