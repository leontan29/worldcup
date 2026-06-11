import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'
import Leaderboard from '../pages/Leaderboard'

const rows = [
  { id: 1, username: 'alice', total_points: 12, exact_count: 3 },
  { id: 2, username: 'bob',   total_points: 9,  exact_count: 2 },
]

function renderWith(user = null) {
  global.fetch = vi.fn().mockResolvedValue({ json: () => Promise.resolve(rows) })
  render(
    <AuthContext.Provider value={{ user }}>
      <MemoryRouter><Leaderboard /></MemoryRouter>
    </AuthContext.Provider>
  )
}

test('renders leaderboard rows', async () => {
  renderWith()
  await waitFor(() => expect(screen.getByText('alice')).toBeInTheDocument())
  expect(screen.getByText('bob')).toBeInTheDocument()
  expect(screen.getByText('12')).toBeInTheDocument()
})

test('highlights current user', async () => {
  renderWith({ username: 'alice' })
  await waitFor(() => screen.getByText('alice'))
  expect(screen.getByText('(you)')).toBeInTheDocument()
})

test('shows empty state when no rows', async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: () => Promise.resolve([]) })
  render(
    <AuthContext.Provider value={{ user: null }}>
      <MemoryRouter><Leaderboard /></MemoryRouter>
    </AuthContext.Provider>
  )
  await waitFor(() => expect(screen.getByText(/No predictions scored yet/)).toBeInTheDocument())
})
