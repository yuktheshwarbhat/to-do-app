import { useState, useEffect } from 'react'

export default function App() {
  // --- AUTH STATE ---
  const [currentUser, setCurrentUser] = useState(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)

  // --- TODO STATE ---
  const [todos, setTodos] = useState([])
  const [newTodoTitle, setNewTodoTitle] = useState('')

  // Check if already logged in
  useEffect(() => {
    fetch('/api/me')
      .then(res => res.json())
      .then(data => { if (data.username) setCurrentUser(data.username) })
  }, [])

  // Fetch todos when logged in
  useEffect(() => {
    if (currentUser) {
      fetch('/todos')
        .then(res => res.json())
        .then(data => setTodos(data))
        .catch(() => {})
    }
  }, [currentUser])

  // --- AUTH ACTIONS ---
  const handleAuth = async (e) => {
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
      if (isRegistering) {
        setIsRegistering(false)
        setError('Account created! Please log in.')
      } else {
        setCurrentUser(data.username)
        setUsername(''); setPassword('')
      }
    } catch { setError('Network error. Is Flask running?') }
  }

  const handleLogout = async () => {
    await fetch('/api/logout', { method: 'POST' })
    setCurrentUser(null)
    setTodos([])
  }

  // --- TODO ACTIONS ---
  const handleAddTodo = async (e) => {
    e.preventDefault()
    if (!newTodoTitle.trim()) return
    try {
      const res = await fetch('/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTodoTitle, priority: 'medium' }),
      })
      if (res.ok) {
        const newTodo = await res.json()
        setTodos([newTodo, ...todos])
        setNewTodoTitle('')
      }
    } catch (err) { console.error(err) }
  }

  const handleToggle = async (todo) => {
    try {
      const res = await fetch(`/todos/${todo.id}/done`, { method: 'PATCH' })
      if (res.ok) {
        const updated = await res.json()
        setTodos(todos.map(t => t.id === todo.id ? updated : t))
      }
    } catch (err) { console.error(err) }
  }

  const handleDelete = async (todo) => {
    try {
      const res = await fetch(`/todos/${todo.id}`, { method: 'DELETE' })
      if (res.ok) setTodos(todos.filter(t => t.id !== todo.id))
    } catch (err) { console.error(err) }
  }

  // --- UI: LOGGED IN (TODO LIST) ---
  if (currentUser) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>Pi ToDo Pro</h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ color: '#6b7280', fontSize: '0.9rem' }}>Hi, {currentUser}</span>
            <button onClick={handleLogout} style={styles.smallBtn}>Logout</button>
          </div>
        </div>

        {/* Add Todo Form */}
        <form onSubmit={handleAddTodo} style={styles.addForm}>
          <input
            style={styles.todoInput}
            placeholder="What needs doing?"
            value={newTodoTitle}
            onChange={(e) => setNewTodoTitle(e.target.value)}
          />
          <button type="submit" style={styles.addBtn}>+ Add</button>
        </form>

        {/* Todo List */}
        <div style={styles.todoList}>
          {todos.length === 0 && (
            <p style={{ textAlign: 'center', color: '#9ca3af', padding: 20 }}>
              No todos yet. Add one above!
            </p>
          )}
          {todos.map(todo => (
            <div key={todo.id} style={{
              ...styles.todoItem,
              opacity: todo.done ? 0.6 : 1,
            }}>
              <button
                onClick={() => handleToggle(todo)}
                style={{
                  ...styles.checkBtn,
                  background: todo.done ? '#10b981' : 'transparent',
                  borderColor: todo.done ? '#10b981' : '#d1d5db',
                  color: '#fff',
                }}
              >
                {todo.done ? '✓' : ''}
              </button>
              <span style={{
                flex: 1,
                textDecoration: todo.done ? 'line-through' : 'none',
                color: todo.done ? '#9ca3af' : '#1f2937',
              }}>
                {todo.title}
              </span>
              <span style={styles.badge}>{todo.priority}</span>
              <button onClick={() => handleDelete(todo)} style={styles.deleteBtn}>×</button>
            </div>
          ))}
        </div>

        <p style={{ textAlign: 'center', color: '#9ca3af', fontSize: '0.8rem', marginTop: 16 }}>
          {todos.filter(t => !t.done).length} active · {todos.filter(t => t.done).length} done
        </p>
      </div>
    )
  }

  // --- UI: LOGIN / REGISTER ---
  return (
    <div style={styles.authCard}>
      <h1 style={styles.title}>Pi ToDo Pro</h1>
      <p style={styles.subtitle}>{isRegistering ? 'Create your account' : 'Log in to your todos'}</p>
      {error && <div style={styles.error}>{error}</div>}
      <form onSubmit={handleAuth}>
        <input style={styles.input} placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        <input style={styles.input} type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" style={styles.submitBtn}>{isRegistering ? 'Create Account' : 'Login'}</button>
      </form>
      <p style={styles.switchText}>
        {isRegistering ? 'Already have an account? ' : 'Need an account? '}
        <span onClick={() => { setIsRegistering(!isRegistering); setError('') }} style={styles.switchLink}>
          {isRegistering ? 'Login' : 'Register'}
        </span>
      </p>
    </div>
  )
}

// --- STYLES ---
const styles = {
  container: { fontFamily: 'system-ui', maxWidth: 560, margin: '40px auto', padding: '0 16px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  title: { fontSize: '1.8rem', fontWeight: 700, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
  addForm: { display: 'flex', gap: 8, marginBottom: 16 },
  todoInput: { flex: 1, padding: 12, fontSize: '1rem', border: '1px solid #e5e7eb', borderRadius: 8, outline: 'none' },
  addBtn: { padding: '12px 20px', background: 'linear-gradient(90deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' },
  todoList: { display: 'flex', flexDirection: 'column', gap: 8 },
  todoItem: { display: 'flex', alignItems: 'center', gap: 12, padding: 14, background: '#fff', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  checkBtn: { width: 24, height: 24, borderRadius: '50%', border: '2px solid #d1d5db', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0 },
  badge: { padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', background: '#fef3c7', color: '#92400e' },
  deleteBtn: { background: 'none', border: 'none', fontSize: 20, color: '#ef4444', cursor: 'pointer', padding: '0 4px' },
  smallBtn: { padding: '6px 12px', border: '1px solid #e5e7eb', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: '0.85rem' },
  authCard: { fontFamily: 'system-ui', maxWidth: 380, margin: '60px auto', padding: 24, background: '#fff', borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' },
  subtitle: { color: '#6b7280', marginBottom: 24 },
  input: { width: '100%', padding: 12, marginBottom: 12, fontSize: '1rem', border: '1px solid #e5e7eb', borderRadius: 8, boxSizing: 'border-box', outline: 'none' },
  submitBtn: { width: '100%', padding: 12, background: 'linear-gradient(90deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none', borderRadius: 8, fontSize: '1rem', fontWeight: 600, cursor: 'pointer', marginTop: 8 },
  error: { background: '#fee2e2', color: '#991b1b', padding: 10, borderRadius: 6, marginBottom: 16 },
  switchText: { textAlign: 'center', marginTop: 20, fontSize: '0.9rem' },
  switchLink: { color: '#6366f1', cursor: 'pointer', fontWeight: 'bold' },
}