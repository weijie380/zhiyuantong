// auth.js — 本地账号系统（无后端，数据存 localStorage）
// 注册/登录/登出/获取当前用户。密码做简单哈希，不存明文。

const KEY_USERS = 'zyt_users'
const KEY_SESSION = 'zyt_session'

// 简单哈希（非加密安全，仅避免明文存储；本地账号场景够用）
function hashPassword(pwd) {
  let h = 0
  for (let i = 0; i < pwd.length; i++) {
    h = ((h << 5) - h) + pwd.charCodeAt(i)
    h |= 0
  }
  return 'h' + h
}

function getUsers() {
  try { return JSON.parse(localStorage.getItem(KEY_USERS) || '{}') } catch { return {} }
}

function saveUsers(users) {
  localStorage.setItem(KEY_USERS, JSON.stringify(users))
}

export const auth = {
  // 注册：用户名+密码，用户名不可重复
  register(username, password) {
    if (!username || !password) return { ok: false, error: '用户名和密码不能为空' }
    if (username.length < 2) return { ok: false, error: '用户名至少 2 个字符' }
    if (password.length < 4) return { ok: false, error: '密码至少 4 个字符' }
    const users = getUsers()
    if (users[username]) return { ok: false, error: '该用户名已存在' }
    users[username] = { password: hashPassword(password), createdAt: Date.now() }
    saveUsers(users)
    // 注册后自动登录
    localStorage.setItem(KEY_SESSION, username)
    return { ok: true, username }
  },

  // 登录
  login(username, password) {
    const users = getUsers()
    const user = users[username]
    if (!user) return { ok: false, error: '用户名不存在' }
    if (user.password !== hashPassword(password)) return { ok: false, error: '密码错误' }
    localStorage.setItem(KEY_SESSION, username)
    return { ok: true, username }
  },

  // 登出
  logout() {
    localStorage.removeItem(KEY_SESSION)
  },

  // 当前登录用户名，未登录返回 null
  current() {
    return localStorage.getItem(KEY_SESSION) || null
  },
}
