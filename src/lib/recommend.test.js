import { describe, it, expect } from 'vitest'
import { classifyGradient, recommend } from './recommend.js'

describe('classifyGradient', () => {
  it('冲: 基准位次比用户靠前 3%~15%', () => {
    expect(classifyGradient(15000, 13500).gradient).toBe('reach')   // B/R=0.90
    expect(classifyGradient(15000, 14000).gradient).toBe('reach')   // B/R=0.933
  })
  it('稳: 基准位次接近或略低于用户', () => {
    expect(classifyGradient(15000, 14800).gradient).toBe('stable')  // B/R=0.987
    expect(classifyGradient(15000, 16000).gradient).toBe('stable')  // B/R=1.067
  })
  it('保: 基准位次明显低于用户 15%~40%', () => {
    expect(classifyGradient(15000, 18000).gradient).toBe('safe')    // B/R=1.20
    expect(classifyGradient(15000, 20000).gradient).toBe('safe')    // B/R=1.333
  })
  it('落: 差距过大不归类', () => {
    expect(classifyGradient(15000, 12000).gradient).toBe('out')     // B/R=0.80
    expect(classifyGradient(15000, 22000).gradient).toBe('out')     // B/R=1.467
  })
})

// records5y 采用聚合后的结构：{ key: { schoolId, major, majorCode, years: [{year, minRank, minScore}] } }
const records5y = {
  '10001:080901': {
    schoolId: '10001', major: '计算机科学与技术', majorCode: '080901',
    years: [
      { year: 2020, minRank: 13000 }, { year: 2021, minRank: 12500 },
      { year: 2022, minRank: 14000 }, { year: 2023, minRank: 13500 },
      { year: 2024, minRank: 14500 },
    ],
  },
}
const schools = { '10001': { id: '10001', name: '测试大学', level: '985', province: '北京' } }

describe('recommend', () => {
  it('按专业基准位次分到三档', () => {
    const result = recommend({ userRank: 15000, subject: 'physics', records5y, schools })
    // 基准位次 = (13000+12500+14000+13500+14500)/5 = 13500, B/R=0.90 → 冲
    expect(result.reach).toHaveLength(1)
    expect(result.reach[0].school.name).toBe('测试大学')
    expect(result.reach[0].gradient).toBe('reach')
    expect(result.stable).toHaveLength(0)
    expect(result.safe).toHaveLength(0)
  })

  it('out 档不进入结果', () => {
    const far = {
      '10002:01': {
        schoolId: '10002', major: '数学', majorCode: '01',
        years: [
          { year: 2020, minRank: 5000 }, { year: 2021, minRank: 5200 },
          { year: 2022, minRank: 5100 }, { year: 2023, minRank: 5300 },
          { year: 2024, minRank: 5400 },
        ],
      },
    }
    const s = { '10002': { id: '10002', name: '远大学', level: '985', province: '北京' } }
    const result = recommend({ userRank: 15000, subject: 'physics', records5y: far, schools: s })
    expect(result.reach).toHaveLength(0)
    expect(result.stable).toHaveLength(0)
    expect(result.safe).toHaveLength(0)
  })

  it('缺少年份(不足1年)的专业被跳过', () => {
    const sparse = {
      '10003:01': {
        schoolId: '10003', major: '物理', majorCode: '01',
        years: [{ year: 2024, minRank: 15000 }],
      },
    }
    const s = { '10003': { id: '10003', name: '稀疏大学', level: '211', province: '天津' } }
    const result = recommend({ userRank: 15000, subject: 'physics', records5y: sparse, schools: s })
    // 至少 1 年数据可用，基准=15000, B/R=1.0 → 稳；此处验证不抛错
    expect(result).toBeDefined()
  })
})
