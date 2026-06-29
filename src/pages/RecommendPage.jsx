import { useState, useEffect, useMemo } from 'react'
import { loadSchools, loadMultiYear, loadMajorList } from '../lib/dataLoader.js'
import { recommend, aggregateRecords } from '../lib/recommend.js'
import { favorites } from '../lib/storage.js'
import { categorizeMajor, ALL_CATEGORIES } from '../lib/majorCategories.js'
import SchoolCard from '../components/SchoolCard.jsx'
import Skeleton from '../components/Skeleton.jsx'
import Pagination from '../components/Pagination.jsx'

const YEARS = [2021, 2022, 2023, 2024, 2025]
const TABS = [
  { key: 'reach', label: '冲' },
  { key: 'stable', label: '稳' },
  { key: 'safe', label: '保' },
]
const TAB_COLOR = {
  reach: 'var(--color-reach)', stable: 'var(--color-stable)', safe: 'var(--color-safe)',
}
const TAB_BG = {
  reach: 'var(--color-reach-bg)', stable: 'var(--color-stable-bg)', safe: 'var(--color-safe-bg)',
}

export default function RecommendPage({ savedState, onStateChange, onOpenSchool }) {
  const { subject, rank, result, tab } = savedState
  const setSubject = (v) => onStateChange(prev => ({ ...prev, subject: v }))
  const setRank = (v) => onStateChange(prev => ({ ...prev, rank: v }))
  const setResult = (v) => onStateChange(prev => ({ ...prev, result: v }))
  const setTab = (v) => onStateChange(prev => ({ ...prev, tab: v }))
  // 以下状态不跨页面持久化
  const [fProvince, setFProvince] = useState('')
  const [fLevel, setFLevel] = useState('')
  const [fType, setFType] = useState('')
  const [fCategory, setFCategory] = useState('')
  const [fMajor, setFMajor] = useState('')
  const [majorList, setMajorList] = useState(null)
  const [loading, setLoading] = useState(false)
  const [favVersion, setFavVersion] = useState(0)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 20

  // 加载专业列表（在结果可用时才加载）
  useEffect(() => {
    if (result && !majorList) {
      loadMajorList().then(setMajorList).catch(() => setMajorList({}))
    }
  }, [result])

  const onGenerate = async () => {
    const userRank = Number(rank)
    if (!userRank || userRank <= 0) return
    setLoading(true); setResult(null); setPage(1)
    try {
      const schoolsMap = await loadSchools()
      const flatRecords = await loadMultiYear(subject, YEARS)
      const records5y = aggregateRecords(flatRecords)
      const res = recommend({ userRank, subject, records5y, schools: schoolsMap })
      setResult(res); setTab('reach')
    } catch (e) {
      console.error('生成方案失败:', e)
    } finally { setLoading(false) }
  }

  const toggleFav = (item) => {
    if (favorites.has(item.school.id, item.major)) favorites.remove(item.school.id, item.major)
    else favorites.add({ schoolId: item.school.id, schoolName: item.school.name, major: item.major, gradient: item.gradient, userRank: item.userRank })
    setFavVersion(v => v + 1)
  }

  // 大类联动：选大类后专业下拉列表更新，切大类时清空专业
  const majorOptions = majorList && fCategory ? (majorList[fCategory] || []) : []
  const selectCategory = (v) => { setFCategory(v); setFMajor(''); setPage(1) }

  const items = result ? result[tab] : []

  // 从推荐结果中提取去重的省份列表
  const provinces = useMemo(() => {
    if (!items.length) return []
    const s = new Set()
    items.forEach(it => { if (it.school.province) s.add(it.school.province) })
    return [...s].sort()
  }, [items])

  const filteredItems = items.filter(it => {
    if (fProvince && (it.school.province || '') !== fProvince) return false
    if (fLevel && (it.school.level || '') !== fLevel) return false
    if (fType && (it.school.type || '') !== fType) return false
    if (fCategory && categorizeMajor(it.major) !== fCategory) return false
    if (fMajor && it.major !== fMajor) return false
    return true
  })
  const totalPages = Math.ceil(filteredItems.length / PAGE_SIZE)
  const currentPage = Math.min(page, totalPages || 1)
  const visibleItems = filteredItems.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  // 筛选条件变化时重置到第一页
  useEffect(() => { setPage(1) }, [fProvince, fLevel, fType, fCategory, fMajor, tab])

  return (
    <div>
      {/* 输入区 */}
      <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ fontWeight: 600, marginBottom: 'var(--sp-3)' }}>输入你的高考信息</div>
        <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
          <label style={{ flex: 1, minWidth: 140 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>科类</div>
            <select value={subject} onChange={e => setSubject(e.target.value)}
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
              <option value="physics">物理类</option>
              <option value="history">历史类</option>
            </select>
          </label>
          <label style={{ flex: 1, minWidth: 140 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>高考位次</div>
            <input type="number" value={rank} onChange={e => setRank(e.target.value)} placeholder="如 15000"
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', fontVariantNumeric: 'tabular-nums' }} />
          </label>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={onGenerate} disabled={loading || !rank}
              style={{ background: 'var(--color-accent)', color: 'var(--color-on-accent)',
                border: 'none', borderRadius: 'var(--radius-sm)', padding: 'var(--sp-2) var(--sp-4)',
                fontWeight: 600, opacity: (loading || !rank) ? 0.5 : 1 }}>
              {loading ? '生成中...' : '生成方案'}
            </button>
          </div>
        </div>
      </div>

      {/* 梯度统计 */}
      {result && (
        <div style={{ display: 'flex', gap: 'var(--sp-2)', marginBottom: 'var(--sp-3)' }}>
          {TABS.map(t => (
            <div key={t.key} style={{ flex: 1, background: TAB_BG[t.key], border: `1px solid ${TAB_COLOR[t.key]}`,
              borderRadius: 'var(--radius-sm)', padding: 'var(--sp-2) var(--sp-3)' }}>
              <div style={{ fontSize: 'var(--fs-12)', color: TAB_COLOR[t.key], fontWeight: 600 }}>{t.label} · {result[t.key].length} 所</div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 切换 */}
      {result && (
        <div style={{ borderBottom: '2px solid var(--color-border)', marginBottom: 'var(--sp-3)' }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => switchTab(t.key)}
              style={{
                padding: 'var(--sp-2) var(--sp-4)', border: 'none', background: 'transparent',
                borderBottom: tab === t.key ? `2px solid ${TAB_COLOR[t.key]}` : '2px solid transparent',
                color: tab === t.key ? TAB_COLOR[t.key] : 'var(--color-muted-foreground)',
                fontWeight: tab === t.key ? 600 : 400, marginBottom: -2,
                transition: `border-color var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease)`,
              }}>
              {t.label}
            </button>
          ))}
        </div>
      )}

      {/* 筛选栏 */}
      {result && (
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)', padding: 'var(--sp-3)', marginBottom: 'var(--sp-3)',
          display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <FilterSelect label="省份" value={fProvince} set={setFProvince} opts={provinces} />
          <FilterSelect label="专业大类" value={fCategory} set={selectCategory} opts={ALL_CATEGORIES} />
          <label style={{ flex: 1, minWidth: 140 }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>专业名称</div>
            <select value={fMajor} onChange={e => { setFMajor(e.target.value); setPage(1) }} disabled={!fCategory}
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', opacity: fCategory ? 1 : 0.5 }}>
              <option value="">全部{fCategory ? `（${majorOptions.length}个）` : ''}</option>
              {majorOptions.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          <FilterSelect label="层次" value={fLevel} set={setFLevel} opts={['985/211', '双一流', '211', '普通本科']} />
          <FilterSelect label="类型" value={fType} set={setFType} opts={['综合', '理工', '师范', '医药', '财经', '政法', '农林', '艺术', '语言', '民族']} />
          {(fProvince || fLevel || fType || fCategory || fMajor) && (
            <button onClick={() => { setFProvince(''); setFLevel(''); setFType(''); setFCategory(''); setFMajor(''); setPage(1) }}
              style={{ padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)', background: 'var(--color-card)', fontSize: 'var(--fs-12)',
                color: 'var(--color-muted-foreground)', minHeight: 36 }}>
              清除筛选
            </button>
          )}
          <span style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', minWidth: 60 }}>
            共 {filteredItems.length} 条
          </span>
        </div>
      )}

      {/* 列表 */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
          {[0,1,2].map(i => <Skeleton key={i} height={120} />)}
        </div>
      )}
      {!loading && result && filteredItems.length === 0 && (
        <div style={{ padding: 'var(--sp-8)', textAlign: 'center', color: 'var(--color-muted-foreground)' }}>
          {majorFilter ? `没有匹配「${majorFilter}」的专业` : '该档位暂无匹配学校'}
        </div>
      )}
      {!loading && visibleItems.map((item, i) => (
        <SchoolCard key={`${item.school.id}-${item.major}`} item={item}
          isFav={favorites.has(item.school.id, item.major)}
          onToggleFav={toggleFav} onView={onOpenSchool} />
      ))}
      {!loading && filteredItems.length > 0 && (
        <Pagination total={filteredItems.length} page={currentPage} pageSize={PAGE_SIZE} onChange={setPage} />
      )}
    </div>
  )
}

function FilterSelect({ label, value, set, opts }) {
  return (
    <label style={{ flex: 1, minWidth: 120 }}>
      <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>{label}</div>
      <select value={value} onChange={e => { set(e.target.value); /* setPage handled by parent */ }}
        style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }}>
        <option value="">全部</option>
        {opts.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  )
}
