import { useState, useEffect, useMemo } from 'react'
import { Search } from 'lucide-react'
import { loadSchoolsArray, loadScoreFile } from '../lib/dataLoader.js'
import SchoolTable from '../components/SchoolTable.jsx'
import Skeleton from '../components/Skeleton.jsx'

const LEVELS = ['985/211', '双一流', '普通本科']
const TYPES = ['综合', '理工', '师范', '医药', '财经', '政法']
const YEAR_OPTS = [2020, 2021, 2022, 2023, 2024]

export default function SearchPage({ onOpenSchool }) {
  const [schools, setSchools] = useState(null)
  const [kw, setKw] = useState('')
  const [fProvince, setFProvince] = useState('')
  const [fLevel, setFLevel] = useState('')
  const [fType, setFType] = useState('')
  const [subject, setSubject] = useState('physics')
  const [year, setYear] = useState(2024)

  useEffect(() => {
    loadSchoolsArray().then(setSchools).catch(() => setSchools([]))
  }, [])

  const [enriched, setEnriched] = useState(null)
  useEffect(() => {
    if (!schools) return
    let cancelled = false
    setEnriched(null)
    loadScoreFile(subject, year).then(file => {
      if (cancelled) return
      const bySchool = {}
      for (const r of file.records) {
        if (r.minRank == null) continue
        if (!bySchool[r.schoolId] || r.minRank < bySchool[r.schoolId].minRank)
          bySchool[r.schoolId] = { minRank: r.minRank, minScore: r.minScore }
      }
      setEnriched(schools.map(s => ({ ...s, ...(bySchool[s.id] || {}) })))
    }).catch(() => { if (!cancelled) setEnriched(schools) })
    return () => { cancelled = true }
  }, [schools, subject, year])

  const provinces = useMemo(() => {
    if (!schools) return []
    return [...new Set(schools.map(s => s.province))].sort()
  }, [schools])

  const rows = useMemo(() => {
    if (!enriched) return []
    return enriched.filter(s => {
      if (kw && !s.name.includes(kw)) return false
      if (fProvince && s.province !== fProvince) return false
      if (fLevel && s.level !== fLevel) return false
      if (fType && s.type !== fType) return false
      return true
    })
  }, [enriched, kw, fProvince, fLevel, fType])

  const columns = [
    { key: 'name', label: '学校', sortable: true, render: r => <span style={{ fontWeight: 600 }}>{r.name}</span> },
    { key: 'province', label: '地区', sortable: true },
    { key: 'level', label: '层次', sortable: true },
    { key: 'type', label: '类型', sortable: true },
    { key: 'minScore', label: `${year}最低分`, sortable: true, numeric: true, render: r => r.minScore ?? '—' },
    { key: 'minRank', label: `${year}最低位次`, sortable: true, numeric: true, render: r => r.minRank != null ? r.minRank.toLocaleString() : '—' },
  ]

  return (
    <div>
      <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ flex: 2, minWidth: 200 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>搜索学校/专业</div>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: 'var(--sp-2)', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted-foreground)' }} />
              <input value={kw} onChange={e => setKw(e.target.value)} placeholder="输入学校名称"
                style={{ width: '100%', padding: 'var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-6)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }} />
            </div>
          </label>
          <FilterSelect label="省份" value={fProvince} set={setFProvince} opts={provinces} />
          <FilterSelect label="层次" value={fLevel} set={setFLevel} opts={LEVELS} />
          <FilterSelect label="类型" value={fType} set={setFType} opts={TYPES} />
          <FilterSelectCvt label="科类" value={subject} set={setSubject}
            opts={[{v:'physics',l:'物理类'},{v:'history',l:'历史类'}]} />
          <FilterSelectCvt label="年份" value={year} set={setYear}
            opts={YEAR_OPTS.map(y => ({v:y,l:y}))} />
        </div>
      </div>

      {enriched == null ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {[0,1,2,3,4].map(i => <Skeleton key={i} height={36} />)}
        </div>
      ) : (
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          <SchoolTable rows={rows} columns={columns} onRowClick={r => onOpenSchool(r.id)} emptyText="没有符合条件的学校" />
        </div>
      )}
    </div>
  )
}

function FilterSelect({ label, value, set, opts }) {
  return (
    <label style={{ flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>{label}</div>
      <select value={value} onChange={e => set(e.target.value)}
        style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
        <option value="">全部</option>
        {opts.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  )
}

function FilterSelectCvt({ label, value, set, opts }) {
  return (
    <label style={{ flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>{label}</div>
      <select value={value} onChange={e => set(typeof opts[0].v === 'number' ? Number(e.target.value) : e.target.value)}
        style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
        {opts.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
      </select>
    </label>
  )
}
