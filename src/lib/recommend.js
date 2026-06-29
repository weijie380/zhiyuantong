// recommend.js — 冲稳保推荐算法（纯函数）

// 梯度区间（B/R 比值）
const RANGES = {
  reach:  [0.85, 0.97],   // 冲
  stable: [0.97, 1.15],   // 稳
  safe:   [1.15, 1.40],   // 保
}

// 概率区间，随 B/R 在档内线性插值（越靠近稳上界概率越高）
const PROB = {
  reach:  [0.40, 0.20],   // B/R 从 0.97→0.85，概率 40%→20%
  stable: [0.70, 0.90],   // B/R 从 0.97→1.15，概率 70%→90%
  safe:   [0.95, 0.99],   // B/R 从 1.15→1.40，概率 95%→99%
}

// 判断单条基准位次所属梯度与录取概率
// userRank 用户位次，baseRank 专业基准位次（5 年平均 minRank）
export function classifyGradient(userRank, baseRank) {
  const ratio = baseRank / userRank
  for (const g of ['reach', 'stable', 'safe']) {
    const [lo, hi] = RANGES[g]
    if (ratio >= lo && ratio <= hi) {
      const [pLo, pHi] = PROB[g]
      const t = (ratio - lo) / (hi - lo) // 0→1
      const probability = pLo + (pHi - pLo) * t
      return { gradient: g, ratio, probability: Math.round(probability * 100) / 100 }
    }
  }
  return { gradient: 'out', ratio, probability: 0 }
}

// 将分片记录按 "schoolId:majorCode" 聚合成多年数组
export function aggregateRecords(records) {
  const map = {}
  for (const r of records) {
    const key = `${r.schoolId}:${r.majorCode || r.major}`
    if (!map[key]) map[key] = { schoolId: r.schoolId, major: r.major, majorCode: r.majorCode, years: [] }
    map[key].years.push({ year: r.year, minRank: r.minRank, minScore: r.minScore })
  }
  return map
}

// 计算专业基准位次（5 年平均，至少需 1 年数据）
function baseRankOf(years) {
  if (!years || years.length < 1) return null
  const valid = years.filter(y => y.minRank != null && y.minRank > 0)
  if (valid.length < 1) return null
  return Math.round(valid.reduce((s, y) => s + y.minRank, 0) / valid.length)
}

// 主推荐函数：输入用户位次、科类、多年聚合记录、学校索引，返回冲稳保三档
export function recommend({ userRank, subject, records5y, schools }) {
  const result = { reach: [], stable: [], safe: [] }
  for (const [, agg] of Object.entries(records5y)) {
    const baseRank = baseRankOf(agg.years)
    if (baseRank == null) continue
    const { gradient, ratio, probability } = classifyGradient(userRank, baseRank)
    if (gradient === 'out') continue
    const school = schools[agg.schoolId]
    if (!school) continue
    const item = {
      school,
      major: agg.major,
      majorCode: agg.majorCode,
      gradient,
      baseRank,
      userRank,
      ratio,
      probability,
      years: agg.years.sort((a, b) => a.year - b.year),
    }
    result[gradient].push(item)
  }
  // 每档按概率降序（录取概率高的排前）
  for (const g of ['reach', 'stable', 'safe']) {
    result[g].sort((a, b) => b.probability - a.probability)
  }
  return result
}
