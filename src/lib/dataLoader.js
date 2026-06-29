// dataLoader.js — JSON 数据按需加载 + 内存缓存
const cache = new Map()
let schoolsMap = null
let schoolsArr = null
let majorList = null

export async function loadMajorList() {
  if (majorList) return majorList
  const res = await fetch('./data/major-list.json')
  if (!res.ok) throw new Error(`加载专业列表失败: ${res.status}`)
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json') && !ct.includes('text/plain')) {
    throw new Error('专业列表文件不存在')
  }
  majorList = await res.json()
  return majorList
}

export async function loadSchools() {
  if (schoolsMap) return schoolsMap
  const res = await fetch('./data/schools.json')
  if (!res.ok) throw new Error(`加载学校索引失败: ${res.status}`)
  const data = await res.json()
  schoolsArr = data.schools
  schoolsMap = {}
  for (const s of schoolsArr) schoolsMap[s.id] = s
  return schoolsMap
}

export async function loadSchoolsArray() {
  await loadSchools()
  return schoolsArr
}

export async function loadScoreFile(subject, year) {
  const key = `${subject}-${year}`
  if (cache.has(key)) return cache.get(key)
  const res = await fetch(`./data/${key}.json`)
  if (!res.ok) throw new Error(`加载分数线失败: ${key} (${res.status})`)
  // 防止 SPA fallback 返回 HTML 而非 JSON（缺失年份会被重定向到 index.html）
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json') && !ct.includes('text/plain')) {
    throw new Error(`分数线文件不存在: ${key}`)
  }
  const data = await res.json()
  cache.set(key, data)
  return data
}

// 加载某科类多年数据，合并成扁平 records 数组供聚合使用
export async function loadMultiYear(subject, years) {
  const all = []
  for (const year of years) {
    try {
      const file = await loadScoreFile(subject, year)
      all.push(...file.records.map(r => ({ ...r, year: file.year })))
    } catch (e) {
      // 某年缺失则跳过
      console.warn(e.message)
    }
  }
  return all
}

export function clearCache() {
  cache.clear()
  schoolsMap = null
  schoolsArr = null
  majorList = null
}
