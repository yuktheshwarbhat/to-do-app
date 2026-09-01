import { useState, useEffect } from 'react'

const THEMES = {
  light: { bg: '#f3f4f6', card: '#ffffff', text: '#1f2937', sub: '#6b7280', border: '#e5e7eb', inputBg: '#ffffff', hover: '#f9fafb' },
  dark: { bg: '#0f172a', card: '#1e293b', text: '#e2e8f0', sub: '#94a3b8', border: '#334155', inputBg: '#0f172a', hover: '#334155' },
}

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)
  const [todos, setTodos] = useState([])
  const [newTodoTitle, setNewTodoTitle] = useState('')
  const [priority, setPriority] = useState('medium')
  const [filter, setFilter] = useState('all')
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark')

  const T = THEMES[isDark ? 'dark' : 'light']

  useEffect(() => {
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

  useEffect(() => {
    fetch('/api/me').then(r => r.json()).then(d => { if (d.username) setCurrentUser(d.username) })
  }, [])

  useEffect(() => {
    if (currentUser) fetchTodos()
  }, [currentUser])

  const fetchTodos = () => fetch('/todos').then(r => r.json()).then(setTodos).catch(() => {})

  const handleAuth = async (e) => {
    e.preventDefault(); setError('')
    const url = isRegistering ? '/api/register' : '/api/login'
    try {
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) })
      const data = await res.json()
      if (!res.ok) { setError(data.error || 'Error'); return }
      if (isRegistering) { setIsRegistering(false); setError('Account created! Log in now.') }
      else { setCurrentUser(data.username); setUsername(''); setPassword('') }
    } catch { setError('Network error') }
  }

  const handleLogout = async () => { await fetch('/api/logout', { method: 'POST' }); setCurrentUser(null); setTodos([]) }

  const handleAddTodo = async (e) => {
    e.preventDefault()
    if (!newTodoTitle.trim()) return
    const res = await fetch('/todos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newTodoTitle, priority }) })
    if (res.ok) { fetchTodos(); setNewTodoTitle('') }
  }

  const handleToggle = async (todo) => { await fetch(`/todos/${todo.id}/done`, { method: 'PATCH' }); fetchTodos() }
  const handleDelete = async (todo) => { await fetch(`/todos/${todo.id}`, { method: 'DELETE' }); fetchTodos() }
  const handleClearCompleted = async () => { await fetch('/todos/clear-completed', { method: 'DELETE' }); fetchTodos() }

  const filteredTodos = todos.filter(t => filter === 'active' ? !t.done : filter === 'done' ? t.done : true)
  const activeCount = todos.filter(t => !t.done).length
  const doneCount = todos.filter(t => t.done).length

  const badgeColors = { low: { background: '#dcfce7', color: '#166534' }, medium: { background: '#fef3c7', color: '#92400e' }, high: { background: '#fee2e2', color: '#991b1b' } }
  const priorityActive = { low: { background: '#dcfce7', borderColor: '#86efac', color: '#166534' }, medium: { background: '#fef3c7', borderColor: '#fcd34d', color: '#92400e' }, high: { background: '#fee2e2', borderColor: '#fca5a5', color: '#991b1b' } }

  const baseStyles = {
    container: { fontFamily: 'system-ui', maxWidth: 560, margin: '40px auto', padding: '0 16px', color: T.text },
    card: { background: T.card, borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,.1)', border: `1px solid ${T.border}` },
    gradient: { background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '1.8rem', fontWeight: 700, margin: 0 },
    primaryBtn: { padding: '12px 20px', background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 16 },
    input: { flex: 1, padding: 12, border: `1px solid ${T.border}`, borderRadius: 8, outline: 'none', fontSize: 16, background: T.inputBg, color: T.text },
    smallBtn: { padding: '6px 12px', border: `1px solid ${T.border}`, borderRadius: 6, background: T.card, cursor: 'pointer', fontSize: 14, color: T.text },
  }

  if (currentUser) {
    return (
      <div style={{ ...baseStyles.container, minHeight: '100vh', background: T.bg, paddingTop: 40, paddingBottom: 40 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h1 style={baseStyles.gradient}>Pi ToDo Pro</h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button onClick={() => setIsDark(!isDark)} style={{ ...baseStyles.smallBtn, fontSize: 18 }}>{isDark ? '☀️' : '🌙'}</button>
            <span style={{ color: T.sub, fontSize: 14 }}>Hi, {currentUser}</span>
            <button onClick={handleLogout} style={baseStyles.smallBtn}>Logout</button>
          </div>
        </div>

        <form onSubmit={handleAddTodo} style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input style={baseStyles.input} placeholder="What needs doing?" value={newTodoTitle} onChange={e => setNewTodoTitle(e.target.value)} />
            <button type="submit" style={baseStyles.primaryBtn}>+ Add</button>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {['low', 'medium', 'high'].map(p => (
              <button key={p} type="button" onClick={() => setPriority(p)} style={{ flex: 1, padding: 8, border: `1px solid ${T.border}`, borderRadius: 6, background: T.card, cursor: 'pointer', fontSize: 14, textTransform: 'capitalize', color: T.text, ...(priority === p ? priorityActive[p] : {}) }}>{p}</button>
            ))}
          </div>
        </form>

        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['all', 'active', 'done'].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{ padding: '8px 16px', border: `1px solid ${filter === f ? '#6366f1' : T.border}`, borderRadius: 20, background: filter === f ? '#6366f1' : T.card, cursor: 'pointer', textTransform: 'capitalize', fontSize: 14, color: filter === f ? '#fff' : T.text }}>{f}</button>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filteredTodos.length === 0 && <p style={{ textAlign: 'center', color: T.sub, padding: 20 }}>Nothing here</p>}
          {filteredTodos.map(todo => (
            <div key={todo.id} style={{ ...baseStyles.card, display: 'flex', alignItems: 'center', gap: 12, padding: 14, opacity: todo.done ? 0.5 : 1 }}>
              <button onClick={() => handleToggle(todo)} style={{ width: 24, height: 24, borderRadius: '50%', border: `2px solid ${todo.done ? '#10b981' : T.border}`, background: todo.done ? '#10b981' : 'transparent', color: '#fff', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{todo.done ? '✓' : ''}</button>
              <span style={{ flex: 1, textDecoration: todo.done ? 'line-through' : 'none', color: T.text }}>{todo.title}</span>
              <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', ...badgeColors[todo.priority] }}>{todo.priority}</span>
              <button onClick={() => handleDelete(todo)} style={{ background: 'none', border: 'none', fontSize: 20, color: '#ef4444', cursor: 'pointer' }}>×</button>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ color: T.sub, fontSize: 14 }}>{activeCount} active · {doneCount} done</span>
          {doneCount > 0 && <button onClick={handleClearCompleted} style={{ ...baseStyles.smallBtn, color: '#ef4444' }}>Clear done</button>}
        </div>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 380, margin: '60px auto', padding: 24, background: T.card, borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,.1)', border: `1px solid ${T.border}`, color: T.text }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <button onClick={() => setIsDark(!isDark)} style={{ ...baseStyles.smallBtn, fontSize: 18 }}>{isDark ? '☀️' : '🌙'}</button>
      </div>
      <h1 style={baseStyles.gradient}>Pi ToDo Pro</h1>
      <p style={{ color: T.sub }}>{isRegistering ? 'Create account' : 'Log in'}</p>
      {error && <div style={{ background: '#fee2e2', color: '#991b1b', padding: 10, borderRadius: 6, marginBottom: 12 }}>{error}</div>}
      <form onSubmit={handleAuth}>
        <input style={{ ...baseStyles.input, width: '100%', boxSizing: 'border-box', marginBottom: 12, flex: 'none' }} placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
        <input style={{ ...baseStyles.input, width: '100%', boxSizing: 'border-box', marginBottom: 12, flex: 'none' }} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit" style={{ ...baseStyles.primaryBtn, width: '100%', marginTop: 8 }}>{isRegistering ? 'Create Account' : 'Login'}</button>
      </form>
      <p style={{ textAlign: 'center', marginTop: 20 }}>
        <span onClick={() => { setIsRegistering(!isRegistering); setError('') }} style={{ color: '#6366f1', cursor: 'pointer', fontWeight: 700 }}>{isRegistering ? 'Login' : 'Register'}</span>
      </p>
    </div>
  )
}