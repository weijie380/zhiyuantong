// storage.js — localStorage 封装（收藏/志愿方案）
const KEY_FAV = 'zyt_favorites'
const KEY_PLANS = 'zyt_plans'

export const favorites = {
  getAll() {
    try { return JSON.parse(localStorage.getItem(KEY_FAV) || '[]') } catch { return [] }
  },
  add(item) {
    const list = this.getAll()
    if (list.some(f => f.schoolId === item.schoolId && f.major === item.major)) return list
    list.push({ ...item, savedAt: Date.now() })
    localStorage.setItem(KEY_FAV, JSON.stringify(list))
    return list
  },
  remove(schoolId, major) {
    const list = this.getAll().filter(f => !(f.schoolId === schoolId && f.major === major))
    localStorage.setItem(KEY_FAV, JSON.stringify(list))
    return list
  },
  has(schoolId, major) {
    return this.getAll().some(f => f.schoolId === schoolId && f.major === major)
  },
}

export const plans = {
  getAll() {
    try { return JSON.parse(localStorage.getItem(KEY_PLANS) || '[]') } catch { return [] }
  },
  create(name) {
    const list = this.getAll()
    const plan = { id: Date.now().toString(36), name, items: [], createdAt: Date.now() }
    list.push(plan)
    localStorage.setItem(KEY_PLANS, JSON.stringify(list))
    return plan
  },
  addItem(planId, item) {
    const list = this.getAll()
    const p = list.find(x => x.id === planId)
    if (!p) return list
    p.items.push({ ...item, addedAt: Date.now() })
    localStorage.setItem(KEY_PLANS, JSON.stringify(list))
    return list
  },
  removeItem(planId, schoolId, major) {
    const list = this.getAll()
    const p = list.find(x => x.id === planId)
    if (!p) return list
    p.items = p.items.filter(i => !(i.schoolId === schoolId && i.major === major))
    localStorage.setItem(KEY_PLANS, JSON.stringify(list))
    return list
  },
  remove(planId) {
    const list = this.getAll().filter(p => p.id !== planId)
    localStorage.setItem(KEY_PLANS, JSON.stringify(list))
    return list
  },
}
