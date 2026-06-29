import { useState } from 'react'
import { GraduationCap, LogIn, UserPlus } from 'lucide-react'
import { auth } from '../lib/auth.js'

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('login')  // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = (e) => {
    e.preventDefault()
    setError('')
    const fn = mode === 'login' ? auth.login : auth.register
    const res = fn(username.trim(), password)
    if (res.ok) onLogin(res.username)
    else setError(res.error)
  }

  const switchMode = () => { setMode(m => m === 'login' ? 'register' : 'login'); setError('') }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--color-background)', padding: 'var(--sp-4)' }}>
      <div style={{ width: '100%', maxWidth: 380 }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--sp-8)' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--sp-2)',
            color: 'var(--color-primary)', fontWeight: 700, fontSize: 'var(--fs-24)' }}>
            <GraduationCap size={28} />
            志愿通
          </div>
          <div style={{ color: 'var(--color-muted-foreground)', fontSize: 'var(--fs-14)', marginTop: 'var(--sp-2)' }}>
            河北高考志愿填报参考
          </div>
        </div>

        <form onSubmit={submit} style={{
          background: 'var(--color-card)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)', padding: 'var(--sp-6)',
        }}>
          <div style={{ display: 'flex', gap: 'var(--sp-2)', marginBottom: 'var(--sp-4)' }}>
            <button type="button" onClick={() => { setMode('login'); setError('') }}
              style={{ flex: 1, padding: 'var(--sp-2)', border: 'none', borderRadius: 'var(--radius-sm)',
                background: mode === 'login' ? 'var(--color-primary)' : 'var(--color-muted)',
                color: mode === 'login' ? 'var(--color-on-primary)' : 'var(--color-muted-foreground)',
                fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--sp-1)' }}>
              <LogIn size={16} /> 登录
            </button>
            <button type="button" onClick={() => { setMode('register'); setError('') }}
              style={{ flex: 1, padding: 'var(--sp-2)', border: 'none', borderRadius: 'var(--radius-sm)',
                background: mode === 'register' ? 'var(--color-primary)' : 'var(--color-muted)',
                color: mode === 'register' ? 'var(--color-on-primary)' : 'var(--color-muted-foreground)',
                fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--sp-1)' }}>
              <UserPlus size={16} /> 注册
            </button>
          </div>

          <label style={{ display: 'block', marginBottom: 'var(--sp-3)' }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>用户名</div>
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="2 个字符以上"
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }} />
          </label>

          <label style={{ display: 'block', marginBottom: 'var(--sp-4)' }}>
            <div style={{ fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)', marginBottom: 'var(--sp-1)' }}>密码</div>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="4 个字符以上"
              style={{ width: '100%', padding: 'var(--sp-2) var(--sp-3)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)', background: 'var(--color-card)' }} />
          </label>

          {error && (
            <div style={{ color: 'var(--color-destructive)', fontSize: 'var(--fs-14)', marginBottom: 'var(--sp-3)' }}>
              {error}
            </div>
          )}

          <button type="submit"
            style={{ width: '100%', padding: 'var(--sp-2) var(--sp-4)', border: 'none',
              borderRadius: 'var(--radius-sm)', background: 'var(--color-accent)', color: 'var(--color-on-accent)',
              fontWeight: 600 }}>
            {mode === 'login' ? '登录' : '注册并登录'}
          </button>

          <div style={{ textAlign: 'center', marginTop: 'var(--sp-3)' }}>
            <button type="button" onClick={switchMode}
              style={{ background: 'none', border: 'none', color: 'var(--color-secondary)',
                fontSize: 'var(--fs-14)', padding: 0, minHeight: 'auto' }}>
              {mode === 'login' ? '没有账号？去注册' : '已有账号？去登录'}
            </button>
          </div>
        </form>

        <div style={{ textAlign: 'center', marginTop: 'var(--sp-4)', fontSize: 'var(--fs-12)', color: 'var(--color-muted-foreground)' }}>
          账号数据保存在本地浏览器，换设备需重新注册
        </div>
      </div>
    </div>
  )
}
