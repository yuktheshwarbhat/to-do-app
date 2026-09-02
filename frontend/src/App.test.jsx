import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

// Mock fetch globally (so tests never hit the real Flask server)
const mockFetch = vi.fn()
global.fetch = mockFetch

// Helper: build a fake fetch response
const mockResponse = (data, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(data),
})

beforeEach(() => {
  mockFetch.mockReset()
  localStorage.clear()
})

describe('Login Page', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValueOnce(mockResponse({ username: null }))
  })

  it('shows login form when not logged in', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
    })
  })

  it('shows register link', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('Register')).toBeInTheDocument())
  })

  it('switches to register mode', async () => {
    render(<App />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('Register'))
    await user.click(screen.getByText('Register'))
    await waitFor(() => expect(screen.getByText('Create Account')).toBeInTheDocument())
  })

  it('shows error on failed login', async () => {
    render(<App />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByPlaceholderText('Username'))
    mockFetch.mockResolvedValueOnce(mockResponse({ error: 'Invalid username or password' }, 401))
    await user.type(screen.getByPlaceholderText('Username'), 'baduser')
    await user.type(screen.getByPlaceholderText('Password'), 'badpass')
    await user.click(screen.getByText('Login'))
    await waitFor(() => expect(screen.getByText('Invalid username or password')).toBeInTheDocument())
  })

  it('logs in and shows todo list', async () => {
    render(<App />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByPlaceholderText('Username'))
    mockFetch.mockResolvedValueOnce(mockResponse({ username: 'testuser' }))
    mockFetch.mockResolvedValueOnce(mockResponse([]))
    await user.type(screen.getByPlaceholderText('Username'), 'testuser')
    await user.type(screen.getByPlaceholderText('Password'), 'secret123')
    await user.click(screen.getByText('Login'))
    await waitFor(() => expect(screen.getByText(/Hi, testuser/)).toBeInTheDocument())
  })
})

describe('Todo List', () => {
  beforeEach(() => {
    mockFetch.mockResolvedValueOnce(mockResponse({ username: 'testuser' }))
    mockFetch.mockResolvedValueOnce(mockResponse([
      { id: 1, title: 'Buy milk', done: 0, priority: 'high' },
      { id: 2, title: 'Walk the dog', done: 1, priority: 'low' },
      { id: 3, title: 'Study React', done: 0, priority: 'medium' },
    ]))
  })

  it('shows todo items', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Buy milk')).toBeInTheDocument()
      expect(screen.getByText('Walk the dog')).toBeInTheDocument()
      expect(screen.getByText('Study React')).toBeInTheDocument()
    })
  })

  it('shows priority badges', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('high')).toBeInTheDocument()
      expect(screen.getByText('low')).toBeInTheDocument()
      expect(screen.getByText('medium')).toBeInTheDocument()
    })
  })

  it('shows active and done counts', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText(/2 active/)).toBeInTheDocument()
      expect(screen.getByText(/1 done/)).toBeInTheDocument()
    })
  })

  it('shows filter buttons', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('all')).toBeInTheDocument()
      expect(screen.getByText('active')).toBeInTheDocument()
      expect(screen.getByText('done')).toBeInTheDocument()
    })
  })

  it('shows clear done button', async () => {
    render(<App />)
    await waitFor(() => expect(screen.getByText('Clear done')).toBeInTheDocument())
  })
})

describe('Dark Mode', () => {
  it('toggles dark mode', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ username: null }))
    render(<App />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('🌙'))
    await user.click(screen.getByText('🌙'))
    await waitFor(() => expect(screen.getByText('☀️')).toBeInTheDocument())
    expect(localStorage.getItem('theme')).toBe('dark')
  })
})