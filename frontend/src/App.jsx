import { useState, useEffect } from 'react'

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)

  useEffect(() => {
    fetch('/api/me').then(res => res.json()).then(data => {
      if (data.username) setCurrentUser(data.username)
    })
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    const url = isRegistering ? '/api/register' : '/api/login'
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Error'); return }
      if (isRegistering) { setIsRegistering(false); alert('Created! Login now.') }
      else { setCurrentUser(data.username); setUsername(''); setPassword('') }
    } catch (err) { setError('Network error') }
  }

  const handleLogout = async () => {
    await fetch('/api/logout', { method: 'POST' })
    setCurrentUser(null)
  }

  if (currentUser) {
    return (
      <div style={{ fontFamily: 'system-ui', maxWidth: 480, margin: '40px auto', padding: 24 }}>
        <h1>Pi ToDo Pro</h1>
        <p>Welcome, <strong>{currentUser}</strong>!</p>
        <button onClick={handleLogout}>Logout</button>
        <div style={{ marginTop: 40, padding: 20, background: '#f3f4f6', borderRadius: 8 }}>
          <p>🎉 Authenticated! Next: Build ToDo list here.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 380, margin: '60px auto', padding: 24, background: '#fff', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
      <h1>Pi ToDo Pro</h1>
      <p>{isRegistering ? 'Create account' : 'Log in'}</p>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <input style={{ width: '100%', padding: 10, marginBottom: 10, boxSizing: 'border-box' }} placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        <input style={{ width: '100%', padding: 10, marginBottom: 10, boxSizing: 'border-box' }} type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" style={{ width: '100%', padding: 10, background: '#6366f1', color: '#fff', border: 'none' }}>
          {isRegistering ? 'Create' : 'Login'}
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: 20 }}>
        <span onClick={() => setIsRegistering(!isRegistering)} style={{ color: '#6366f1', cursor: 'pointer', fontWeight: 'bold' }}>
          {isRegistering ? 'Login' : 'Register'}
        </span>
      </p>
    </div>
  )
}