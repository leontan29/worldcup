import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [teams, setTeams] = useState([])
  const [email, setEmail] = useState('')
  const [favoriteTeam, setFavoriteTeam] = useState('')
  const [pw, setPw] = useState({ old_password: '', new_password: '' })
  const [activity, setActivity] = useState([])
  const [msg, setMsg] = useState({})

  useEffect(() => {
    fetch('/api/teams').then(r => r.json()).then(setTeams)
    fetch('/api/user/profile', { credentials: 'include' })
      .then(r => r.json())
      .then(d => { setEmail(d.email || ''); setFavoriteTeam(d.favorite_team_id || '') })
    fetch('/api/user/activity', { credentials: 'include' })
      .then(r => r.json()).then(setActivity)
  }, [])

  async function saveProfile(e) {
    e.preventDefault()
    const res = await fetch('/api/user/profile', {
      method: 'PUT', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    setMsg(m => ({ ...m, profile: res.ok ? 'Saved!' : 'Error' }))
  }

  async function saveFavorite(e) {
    e.preventDefault()
    const res = await fetch('/api/user/favorite-team', {
      method: 'PUT', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: Number(favoriteTeam) }),
    })
    setMsg(m => ({ ...m, fav: res.ok ? 'Saved!' : 'Error' }))
  }

  async function changePassword(e) {
    e.preventDefault()
    const res = await fetch('/api/user/change-password', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pw),
    })
    const data = await res.json()
    setMsg(m => ({ ...m, pw: res.ok ? 'Password changed!' : (data.error || 'Error') }))
    if (res.ok) setPw({ old_password: '', new_password: '' })
  }

  async function deactivate() {
    if (!confirm('Deactivate your account? This cannot be undone.')) return
    await fetch('/api/user/profile', { method: 'DELETE', credentials: 'include' })
    await logout()
    navigate('/login')
  }

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>

      <div className="bg-white rounded-lg shadow p-5 space-y-4">
        <h2 className="font-semibold">Account</h2>
        <p className="text-sm text-gray-500">Username: <span className="font-medium text-gray-800">{user?.username}</span></p>
        <form onSubmit={saveProfile} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full border rounded px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="bg-green-700 text-white px-4 py-2 rounded text-sm hover:bg-green-800">
            Update Email
          </button>
          {msg.profile && <span className="text-sm text-gray-500 ml-2">{msg.profile}</span>}
        </form>
        <form onSubmit={saveFavorite} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Favourite Team</label>
            <select value={favoriteTeam} onChange={e => setFavoriteTeam(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm">
              <option value="">— None —</option>
              {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <button type="submit" className="bg-green-700 text-white px-4 py-2 rounded text-sm hover:bg-green-800">
            Save Favourite
          </button>
          {msg.fav && <span className="text-sm text-gray-500 ml-2">{msg.fav}</span>}
        </form>
      </div>

      <div className="bg-white rounded-lg shadow p-5 space-y-3">
        <h2 className="font-semibold">Change Password</h2>
        <form onSubmit={changePassword} className="space-y-3">
          {['old_password', 'new_password'].map(field => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                {field.replace('_', ' ')}
              </label>
              <input type="password" value={pw[field]} onChange={e => setPw(p => ({ ...p, [field]: e.target.value }))} required
                className="w-full border rounded px-3 py-2 text-sm" />
            </div>
          ))}
          <button type="submit" className="bg-green-700 text-white px-4 py-2 rounded text-sm hover:bg-green-800">
            Change Password
          </button>
          {msg.pw && <span className="text-sm ml-2 text-gray-500">{msg.pw}</span>}
        </form>
      </div>

      {activity.length > 0 && (
        <div className="bg-white rounded-lg shadow p-5">
          <h2 className="font-semibold mb-3">Recent Activity</h2>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {activity.map(a => (
              <div key={a.id} className="flex justify-between text-xs text-gray-500">
                <span className="capitalize">{a.action}</span>
                <span>{new Date(a.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold text-red-600 mb-2">Danger Zone</h2>
        <button onClick={deactivate}
          className="border border-red-400 text-red-600 px-4 py-2 rounded text-sm hover:bg-red-50">
          Deactivate Account
        </button>
      </div>
    </div>
  )
}
