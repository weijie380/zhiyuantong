// storage.js — localStorage 封装（收藏/方案/用户输入），按用户隔离
import { auth } from './auth.js'

// 按用户生成 key，未登录时用 'guest'
function userKey(base) {
  const u = auth.current() || 'guest'
  return `${base}_${u}`
}

const BASE_FAV = 'zyt_favorites'
const BASE_PLANS = 'zyt_plans'
const BASE_INPUT = 'zyt_input'

export const favorites = {
  getAll() {
    try { return JSON.parse(localStorage.getItem(userKey(BASE_FAV)) || '[]') } catch { return [] }
  },
  add(item) {
    const list = this.getAll()
    if (list.some(f => f.schoolId === item.schoolId && f.major === item.major)) return list
    list.push({ ...item, savedAt: Date.now() })
    localStorage.setItem(userKey(BASE_FAV), JSON.stringify(list))
    return list
  },
  remove(schoolId, major) {
    const list = this.getAll().filter(f => !(f.schoolId === schoolId && f.major === major))
    localStorage.setItem(userKey(BASE_FAV), JSON.stringify(list))
    return list
  },
  has(schoolId, major) {
    return this.getAll().some(f => f.schoolId === schoolId && f.major === major)
  },
}

export const plans = {
  getAll() {
    try { return JSON.parse(localStorage.getItem(userKey(BASE_PLANS)) || '[]') } catch { return [] }
  },
  create(name) {
    const list = this.getAll()
    const plan = { id: Date.now().toString(36), name, items: [], createdAt: Date.now() }
    list.push(plan)
    localStorage.setItem(userKey(BASE_PLANS), JSON.stringify(list))
    return plan
  },
  addItem(planId, item) {
    const list = this.getAll()
    const p = list.find(x => x.id === planId)
    if (!p) return list
    p.items.push({ ...item, addedAt: Date.now() })
    localStorage.setItem(userKey(BASE_PLANS), JSON.stringify(list))
    return list
  },
  removeItem(planId, schoolId, major) {
    const list = this.getAll()
    const p = list.find(x => x.id === planId)
    if (!p) return list
    p.items = p.items.filter(i => !(i.schoolId === schoolId && i.major === major))
    localStorage.setItem(userKey(BASE_PLANS), JSON.stringify(list))
    return list
  },
  remove(planId) {
    const list = this.getAll().filter(p => p.id !== planId)
    localStorage.setItem(userKey(BASE_PLANS), JSON.stringify(list))
    return list
  },
}

// 用户输入信息（科类 + 位次 + 推荐结果），按用户保存
export const userInput = {
  get() {
    try { return JSON.parse(localStorage.getItem(userKey(BASE_INPUT)) || 'null') } catch { return null }
  },
  save(data) {
    localStorage.setItem(userKey(BASE_INPUT), JSON.stringify(data))
  },
  clear() {
    localStorage.removeItem(userKey(BASE_INPUT))
  },
}
