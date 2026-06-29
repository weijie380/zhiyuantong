import { useState, useEffect } from 'react'
import { ArrowLeft } from 'lucide-react'
import { loadSchools, loadScoreFile } from '../lib/dataLoader.js'
import { classifyGradient } from '../lib/recommend.js'
import SchoolTable from '../components/SchoolTable.jsx'
import GradientBadge from '../components/GradientBadge.jsx'
import Skeleton from '../components/Skeleton.jsx'

export default function SchoolDetailPage({ schoolId, onBack }) {
  const [school, setSchool] = useState(null)
  const [subject, setSubject] = useState('physics')
  const [year, setYear] = useState(2024)
  const [records, setRecords] = useState(null)
  const [compareRank, setCompareRank] = useState('')
  const [showCompare, setShowCompare] = useState(false)

  useEffect(() => {
    loadSchools().then(m => setSchool(m[schoolId])).catch(() => setSchool(null))
  }, [schoolId])

  useEffect(() => {
    setRecords(null)
    loadScoreFile(subject, year).then(f => {
      setRecords(f.records.filter(r => r.schoolId === schoolId))
    }).catch(() => setRecords([]))
  }, [schoolId, subject, year])

  const rankNum = showCompare && compareRank ? Number(compareRank) : null

  const columns = [
    { key: 'major', label: '专业', sortable: true, render: r => <span style={{ fontWeight: 500 }}>{r.major}</span> },
    { key: 'minScore', label: '最低分', sortable: true, numeric: true },
    { key: 'maxScore', label: '最高分', sortable: true, numeric: true },
    { key: 'avgScore', label: '平均分', sortable: true, numeric: true },
    { key: 'minRank', label: '最低位次', sortable: true, numeric: true, render: r => r.minRank?.toLocaleString() ?? '—' },
    { key: 'planNum', label: '计划数', numeric: true, render: r => r.planNum ?? '—' },
  ]
  if (rankNum) {
    columns.push({
      key: '_grad', label: '梯度', render: r => {
        if (r.minRank == null) return '—'
        const g = classifyGradient(rankNum, r.minRank)
        return g.gradient === 'out'
          ? <span style={{ color: 'var(--color-muted-foreground)' }}>—</span>
          : <GradientBadge gradient={g.gradient} />
      },
    })
  }

  return (
    <div>
      <button onClick={onBack}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--sp-1)', background: 'none',
          border: 'none', color: 'var(--color-secondary)', marginBottom: 'var(--sp-4)' }}>
        <ArrowLeft size={16} /> 返回
      </button>

      {!school ? <Skeleton height={80} /> : (
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', flexWrap: 'wrap' }}>
            <span style={{ fontSize: 'var(--fs-24)', fontWeight: 700 }}>{school.name}</span>
            {school.level && <span style={{ fontSize: 'var(--fs-12)', color: 'var(--color-primary)', border: '1px solid var(--color-primary)', borderRadius: 'var(--radius-sm)', padding: '0 var(--sp-1)' }}>{school.level}</span>}
          </div>
          <div style={{ color: 'var(--color-muted-foreground)', marginTop: 'var(--sp-2)' }}>
            {school.province} · {school.type} · {school.nature} · {school.batch}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: 'var(--sp-3)' }}>
        <label style={{ minWidth: 120 }}>
          <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>科类</div>
          <select value={subject} onChange={e => setSubject(e.target.value)}
            style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
            <option value="physics">物理类</option><option value="history">历史类</option>
          </select>
        </label>
        <label style={{ minWidth: 120 }}>
          <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>年份</div>
          <select value={year} onChange={e => setYear(Number(e.target.value))}
            style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
            {[2021,2022,2023,2024,2025].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', minWidth: 200 }}>
          <input type="checkbox" checked={showCompare} onChange={e => setShowCompare(e.target.checked)} />
          <span style={{ fontSize: 'var(--fs-14)' }}>我的位次对比</span>
        </label>
        {showCompare && (
          <input type="number" value={compareRank} onChange={e => setCompareRank(e.target.value)} placeholder="输入位次"
            style={{ padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', width: 140 }} />
        )}
      </div>

      {records == null ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {[0,1,2].map(i => <Skeleton key={i} height={36} />)}
        </div>
      ) : (
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          <SchoolTable rows={records} columns={columns} emptyText="该年无专业分数线数据" />
        </div>
      )}
    </div>
  )
}
