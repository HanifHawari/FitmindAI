import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { errorDetail } from '../api'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  async function handleLogin(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/users/login', { username: username.trim(), password: password.trim() })
      const user = res.data
      localStorage.setItem('fitmind_token', user.token)
      localStorage.setItem('fitmind_user', JSON.stringify({
        username: user.username,
        phone: user.phone,
        id: user.id,
        is_new: user.is_new,
        has_profile: user.has_profile,
      }))
      // Always redirect to dashboard on successful login
      window.location.href = '/dashboard'
    } catch (err) {
      if ([400, 401, 429].includes(err.response?.status)) {
        setError(errorDetail(err, 'Username atau password salah.'))
      } else if (err.response?.status === 422) {
        setError('Format data tidak valid')
      } else {
        setError('Gagal masuk. Pastikan backend sudah berjalan.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0a0a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      padding: '0 20px',
    }}>
      {/* Background gradient blobs */}
      <div style={{
        position: 'absolute', width: 500, height: 500,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(34,197,94,0.08) 0%, transparent 70%)',
        top: '-100px', right: '-100px', pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', width: 400, height: 400,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(239,68,68,0.07) 0%, transparent 70%)',
        bottom: '-80px', left: '-80px', pointerEvents: 'none',
      }} />

      {/* Back Button */}
      <button 
        onClick={() => navigate('/')}
        className="btn-ghost battery-hover"
        style={{
          position: 'absolute',
          top: 32,
          left: 32,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          zIndex: 10,
        }}
      >
        <span style={{ fontSize: 16, lineHeight: 1 }}>←</span> Kembali ke Beranda
      </button>

      <div className="card animate-fadeinup" style={{ width: '100%', maxWidth: 400, padding: 40 }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.03em', marginBottom: 8 }}>
            FitMind<span style={{ color: '#22c55e' }}>AI</span>
          </div>
          <p style={{ color: '#a3a3a3', fontSize: 14 }}>
            Masuk ke akun Anda
          </p>
        </div>

        {/* Divider line */}
        <div style={{ height: 1, background: '#2a2a2a', marginBottom: 28 }} />

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ fontSize: 12, color: '#a3a3a3', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 8 }}>
              Username
            </label>
            <input
              className="input-field"
              type="text"
              placeholder="Masukkan username..."
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus
            />
          </div>

          <div>
            <label style={{ fontSize: 12, color: '#a3a3a3', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 8 }}>
              Password
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                className="input-field"
                type={showPassword ? "text" : "password"}
                placeholder="Masukkan password Anda..."
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ paddingRight: '40px', width: '100%' }}
              />
              <button
                className="no-fill-hover"
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  background: 'none',
                  border: 'none',
                  color: '#a3a3a3',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: 0
                }}
                title={showPassword ? "Sembunyikan sandi" : "Tampilkan sandi"}
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div style={{ fontSize: 13, color: '#ef4444', padding: '8px 12px', background: 'rgba(239,68,68,0.08)', borderRadius: 6, border: '1px solid rgba(239,68,68,0.2)' }}>
              {error}
            </div>
          )}

          <button className="btn-primary" type="submit" disabled={loading} style={{ width: '100%', padding: '12px 20px', marginTop: 4 }}>
            {loading ? 'Memproses...' : 'Masuk'}
          </button>
        </form>

        <p style={{ marginTop: 20, fontSize: 13, color: '#a3a3a3', textAlign: 'center' }}>
          Belum punya akun?{' '}
          <button 
            className="no-fill-hover"
            onClick={() => navigate('/register')}
            style={{ background: 'none', border: 'none', color: '#22c55e', cursor: 'pointer', fontWeight: 600 }}
          >
            Daftar di sini
          </button>
        </p>
      </div>
    </div>
  )
}
