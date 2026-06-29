import { useState, useEffect, useMemo } from 'react'
import { Search } from 'lucide-react'
import { loadSchoolsArray, loadScoreFile, loadMajorList } from '../lib/dataLoader.js'
import { categorizeMajor, ALL_CATEGORIES } from '../lib/majorCategories.js'
import SchoolTable from '../components/SchoolTable.jsx'
import Skeleton from '../components/Skeleton.jsx'
import Pagination from '../components/Pagination.jsx'

const LEVELS = ['985/211', '双一流', '211', '普通本科']
const TYPES = ['综合', '理工', '师范', '医药', '财经', '政法', '农林', '艺术', '语言', '民族']
const YEAR_OPTS = [2021, 2022, 2023, 2024, 2025]
const PAGE_SIZE = 30

export default function SearchPage({ onOpenSchool }) {
  const [schoolsArr, setSchoolsArr] = useState(null)
  const [schoolsMap, setSchoolsMap] = useState(null)
  const [kw, setKw] = useState('')
  const [fProvince, setFProvince] = useState('')
  const [fLevel, setFLevel] = useState('')
  const [fType, setFType] = useState('')
  const [fCategory, setFCategory] = useState('')
  const [fMajor, setFMajor] = useState('')
  const [subject, setSubject] = useState('physics')
  const [year, setYear] = useState(2024)
  const [scoreRecords, setScoreRecords] = useState(null)
  const [majorList, setMajorList] = useState(null)
  const [page, setPage] = useState(1)

  useEffect(() => {
    loadSchoolsArray().then(arr => {
      setSchoolsArr(arr)
      const m = {}
      for (const s of arr) m[s.id] = s
      setSchoolsMap(m)
    }).catch(() => { setSchoolsArr([]); setSchoolsMap({}) })
    loadMajorList().then(setMajorList).catch(() => setMajorList({}))
  }, [])

  useEffect(() => {
    if (!schoolsArr) return
    let cancelled = false
    setScoreRecords(null)
    loadScoreFile(subject, year).then(file => {
      if (cancelled) return
      setScoreRecords(file.records.filter(r => r.minRank != null && !r.minRankEstimated))
    }).catch(() => { if (!cancelled) setScoreRecords([]) })
    return () => { cancelled = true }
  }, [schoolsArr, subject, year])

  const provinces = useMemo(() => {
    if (!schoolsArr) return []
    return [...new Set(schoolsArr.map(s => s.province))].filter(Boolean).sort()
  }, [schoolsArr])

  // 当前大类下的专业列表（联动）
  const majorOptions = useMemo(() => {
    if (!majorList) return []
    if (!fCategory) return []  // 未选大类时不显示专业下拉
    return majorList[fCategory] || []
  }, [majorList, fCategory])

  const selectCategory = (v) => { setFCategory(v); setFMajor('') }  // 切换大类时清空专业

  // 筛选条件变化时重置到第一页
  useEffect(() => { setPage(1) }, [kw, fProvince, fLevel, fType, fCategory, fMajor, subject, year])

  // 是否进入专业维度筛选模式
  const majorMode = !!(fCategory || fMajor)

  // 学校维度行
  const schoolRows = useMemo(() => {
    if (!schoolsArr || !scoreRecords) return []
    const bySchool = {}
    for (const r of scoreRecords) {
      if (!bySchool[r.schoolId] || r.minRank < bySchool[r.schoolId].minRank)
        bySchool[r.schoolId] = { minRank: r.minRank, minScore: r.minScore }
    }
    return schoolsArr
      .map(s => ({ ...s, ...(bySchool[s.id] || {}) }))
      .filter(s => {
        if (kw && !s.name.includes(kw)) return false
        if (fProvince && s.province !== fProvince) return false
        if (fLevel && s.level !== fLevel) return false
        if (fType && s.type !== fType) return false
        return true
      })
  }, [schoolsArr, scoreRecords, kw, fProvince, fLevel, fType])

  // 专业维度行
  const majorRows = useMemo(() => {
    if (!schoolsMap || !scoreRecords) return []
    return scoreRecords
      .map(r => {
        const s = schoolsMap[r.schoolId]
        if (!s) return null
        return { ...s, major: r.major, minScore: r.minScore, minRank: r.minRank, planNum: r.planNum }
      })
      .filter(r => {
        if (!r) return false
        if (kw && !r.name.includes(kw)) return false
        if (fProvince && r.province !== fProvince) return false
        if (fLevel && r.level !== fLevel) return false
        if (fType && r.type !== fType) return false
        if (fCategory && categorizeMajor(r.major) !== fCategory) return false
        if (fMajor && r.major !== fMajor) return false
        return true
      })
  }, [schoolsMap, scoreRecords, kw, fProvince, fLevel, fType, fCategory, fMajor])

  const columns = majorMode
    ? [
        { key: 'name', label: '学校', sortable: true, render: r => <span style={{ fontWeight: 600 }}>{r.name}</span> },
        { key: 'major', label: '专业', sortable: true, render: r => <span style={{ fontWeight: 500 }}>{r.major}</span> },
        { key: 'province', label: '地区', sortable: true, render: r => r.province || '—' },
        { key: 'level', label: '层次', sortable: true, render: r => r.level || '—' },
        { key: 'minScore', label: `${year}最低分`, sortable: true, numeric: true, render: r => r.minScore ?? '—' },
        { key: 'minRank', label: `${year}最低位次`, sortable: true, numeric: true, render: r => r.minRank?.toLocaleString() ?? '—' },
      ]
    : [
        { key: 'name', label: '学校', sortable: true, render: r => <span style={{ fontWeight: 600 }}>{r.name}</span> },
        { key: 'province', label: '地区', sortable: true, render: r => r.province || '—' },
        { key: 'level', label: '层次', sortable: true, render: r => r.level || '—' },
        { key: 'type', label: '类型', sortable: true, render: r => r.type || '—' },
        { key: 'minScore', label: `${year}最低分`, sortable: true, numeric: true, render: r => r.minScore ?? '—' },
        { key: 'minRank', label: `${year}最低位次`, sortable: true, numeric: true, render: r => r.minRank?.toLocaleString() ?? '—' },
      ]

  const rows = majorMode ? majorRows : schoolRows
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const currentPage = Math.min(page, totalPages || 1)
  const displayRows = rows.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  return (
    <div>
      <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ flex: 2, minWidth: 200 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>学校名称</div>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: 'var(--sp-2)', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-muted-foreground)' }} />
              <input value={kw} onChange={e => setKw(e.target.value)} placeholder="输入学校名称"
                style={{ width: '100%', padding: 'var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-6)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }} />
            </div>
          </label>
          <FilterSelect label="专业大类" value={fCategory} set={selectCategory} opts={ALL_CATEGORIES} />
          <label style={{ flex: 2, minWidth: 200 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>专业名称</div>
            <select value={fMajor} onChange={e => setFMajor(e.target.value)} disabled={!fCategory}
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', opacity: fCategory ? 1 : 0.5 }}>
              <option value="">全部{fCategory ? `（${majorOptions.length}个）` : ''}</option>
              {majorOptions.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          <FilterSelect label="省份" value={fProvince} set={setFProvince} opts={provinces} />
          <FilterSelect label="层次" value={fLevel} set={setFLevel} opts={LEVELS} />
          <FilterSelect label="类型" value={fType} set={setFType} opts={TYPES} />
          <FilterSelectCvt label="科类" value={subject} set={setSubject}
            opts={[{v:'physics',l:'物理类'},{v:'history',l:'历史类'}]} />
          <FilterSelectCvt label="年份" value={year} set={setYear}
            opts={YEAR_OPTS.map(y => ({v:y,l:y}))} />
        </div>
        {majorMode && (
          <div style={{ marginTop: 'var(--sp-3)', fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>
            已进入专业筛选模式，共匹配 {rows.length} 条
          </div>
        )}
      </div>

      {scoreRecords == null ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {[0,1,2,3,4].map(i => <Skeleton key={i} height={36} />)}
        </div>
      ) : (
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          <SchoolTable rows={displayRows} columns={columns} onRowClick={r => onOpenSchool(r.id)} emptyText="没有符合条件的记录" />
        </div>
        {rows.length > 0 && (
          <Pagination total={rows.length} page={currentPage} pageSize={PAGE_SIZE} onChange={setPage} />
        )}
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
