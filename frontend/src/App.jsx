import { useState, useEffect } from 'react'

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

  const handleLogout = async () => {
    await fetch('/api/logout', { method: 'POST' })
    setCurrentUser(null); setTodos([])
  }

  const handleAddTodo = async (e) => {
    e.preventDefault()
    if (!newTodoTitle.trim()) return
    const res = await fetch('/todos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newTodoTitle, priority }) })
    if (res.ok) { fetchTodos(); setNewTodoTitle('') }
  }

  const handleToggle = async (todo) => {
    await fetch(`/todos/${todo.id}/done`, { method: 'PATCH' })
    fetchTodos()
  }

  const handleDelete = async (todo) => {
    await fetch(`/todos/${todo.id}`, { method: 'DELETE' })
    fetchTodos()
  }

  const handleClearCompleted = async () => {
    await fetch('/todos/clear-completed', { method: 'DELETE' })
    fetchTodos()
  }

  const filteredTodos = todos.filter(t => {
    if (filter === 'active') return !t.done
    if (filter === 'done') return t.done
    return true
  })

  const activeCount = todos.filter(t => !t.done).length
  const doneCount = todos.filter(t => t.done).length

  if (currentUser) {
    return (
      <div style={S.container}>
        <div style={S.header}>
          <h1 style={S.gradient}>Pi ToDo Pro</h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ color: '#6b7280', fontSize: 14 }}>Hi, {currentUser}</span>
            <button onClick={handleLogout} style={S.smallBtn}>Logout</button>
          </div>
        </div>

        <form onSubmit={handleAddTodo} style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input style={S.input} placeholder="What needs doing?" value={newTodoTitle} onChange={e => setNewTodoTitle(e.target.value)} />
            <button type="submit" style={S.primaryBtn}>+ Add</button>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {['low', 'medium', 'high'].map(p => (
              <button key={p} type="button" onClick={() => setPriority(p)} style={{ ...S.priorityBtn, ...(priority === p ? S.priorityActive[p] : {}) }}>{p}</button>
            ))}
          </div>
        </form>

        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {['all', 'active', 'done'].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{ ...S.filterBtn, ...(filter === f ? S.filterActive : {}) }}>{f}</button>
          ))}
        </div>

        <div style={S.todoList}>
          {filteredTodos.length === 0 && <p style={{ textAlign: 'center', color: '#9ca3af', padding: 20 }}>Nothing here</p>}
          {filteredTodos.map(todo => (
            <div key={todo.id} style={{ ...S.todoItem, opacity: todo.done ? 0.5 : 1 }}>
              <button onClick={() => handleToggle(todo)} style={{ ...S.checkBtn, background: todo.done ? '#10b981' : 'transparent', borderColor: todo.done ? '#10b981' : '#d1d5db' }}>{todo.done ? '✓' : ''}</button>
              <span style={{ flex: 1, textDecoration: todo.done ? 'line-through' : 'none' }}>{todo.title}</span>
              <span style={{ ...S.badge, ...S.badgeColors[todo.priority] }}>{todo.priority}</span>
              <button onClick={() => handleDelete(todo)} style={S.deleteBtn}>×</button>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
          <span style={{ color: '#9ca3af', fontSize: 14 }}>{activeCount} active · {doneCount} done</span>
          {doneCount > 0 && <button onClick={handleClearCompleted} style={{ ...S.smallBtn, color: '#ef4444' }}>Clear done</button>}
        </div>
      </div>
    )
  }

  return (
    <div style={S.authCard}>
      <h1 style={S.gradient}>Pi ToDo Pro</h1>
      <p style={{ color: '#6b7280' }}>{isRegistering ? 'Create account' : 'Log in'}</p>
      {error && <div style={S.error}>{error}</div>}
      <form onSubmit={handleAuth}>
        <input style={{ ...S.input, width: '100%', boxSizing: 'border-box' }} placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
        <input style={{ ...S.input, width: '100%', boxSizing: 'border-box' }} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit" style={{ ...S.primaryBtn, width: '100%', marginTop: 8 }}>{isRegistering ? 'Create Account' : 'Login'}</button>
      </form>
      <p style={{ textAlign: 'center', marginTop: 20 }}>
        <span onClick={() => { setIsRegistering(!isRegistering); setError('') }} style={{ color: '#6366f1', cursor: 'pointer', fontWeight: 700 }}>{isRegistering ? 'Login' : 'Register'}</span>
      </p>
    </div>
  )
}

const S = {
  container: { fontFamily: 'system-ui', maxWidth: 560, margin: '40px auto', padding: '0 16px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  gradient: { background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '1.8rem', fontWeight: 700, margin: 0 },
  input: { flex: 1, padding: 12, border: '1px solid #e5e7eb', borderRadius: 8, outline: 'none', fontSize: 16 },
  primaryBtn: { padding: '12px 20px', background: 'linear-gradient(90deg,#6366f1,#8b5cf6)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer', fontSize: 16 },
  smallBtn: { padding: '6px 12px', border: '1px solid #e5e7eb', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 14 },
  priorityBtn: { flex: 1, padding: 8, border: '1px solid #e5e7eb', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 14, textTransform: 'capitalize' },
  priorityActive: { low: { background: '#dcfce7', borderColor: '#86efac', color: '#166534' }, medium: { background: '#fef3c7', borderColor: '#fcd34d', color: '#92400e' }, high: { background: '#fee2e2', borderColor: '#fca5a5', color: '#991b1b' } },
  filterBtn: { padding: '8px 16px', border: '1px solid #e5e7eb', borderRadius: 20, background: '#fff', cursor: 'pointer', textTransform: 'capitalize', fontSize: 14 },
  filterActive: { background: '#6366f1', color: '#fff', borderColor: '#6366f1' },
  todoList: { display: 'flex', flexDirection: 'column', gap: 8 },
  todoItem: { display: 'flex', alignItems: 'center', gap: 12, padding: 14, background: '#fff', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,.1)' },
  checkBtn: { width: 24, height: 24, borderRadius: '50%', border: '2px solid #d1d5db', cursor: 'pointer', color: '#fff', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  badge: { padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, textTransform: 'uppercase' },
  badgeColors: { low: { background: '#dcfce7', color: '#166534' }, medium: { background: '#fef3c7', color: '#92400e' }, high: { background: '#fee2e2', color: '#991b1b' } },
  deleteBtn: { background: 'none', border: 'none', fontSize: 20, color: '#ef4444', cursor: 'pointer' },
  authCard: { fontFamily: 'system-ui', maxWidth: 380, margin: '60px auto', padding: 24, background: '#fff', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,.1)' },
  error: { background: '#fee2e2', color: '#991b1b', padding: 10, borderRadius: 6, marginBottom: 12 },
}