import { useEffect, useState } from 'react'

function MatchManager() {
  const [matches, setMatches] = useState([])
  const [edit, setEdit] = useState({})
  const [msg, setMsg] = useState({})

  useEffect(() => {
    fetch('/api/matches').then(r => r.json()).then(setMatches)
  }, [])

  function startEdit(m) {
    setEdit({ id: m.id, home_score: m.home_score ?? '', away_score: m.away_score ?? '', status: m.status })
  }

  async function save(mid) {
    const res = await fetch(`/api/admin/matches/${mid}/score`, {
      method: 'PUT', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ home_score: Number(edit.home_score), away_score: Number(edit.away_score), status: edit.status }),
    })
    if (res.ok) {
      setMsg(m => ({ ...m, [mid]: 'Saved!' }))
      setEdit({})
      fetch('/api/matches').then(r => r.json()).then(setMatches)
    } else setMsg(m => ({ ...m, [mid]: 'Error' }))
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {matches.map(m => (
        <div key={m.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded text-sm">
          <span className="flex-1 font-medium">{m.home_team?.name} vs {m.away_team?.name}</span>
          <span className="text-xs text-gray-400 capitalize">
            {m.stage?.replace(/_/g, ' ')}{m.group_name ? ` · Group ${m.group_name}` : ''}
          </span>
          {edit.id === m.id ? (
            <>
              <input type="number" min="0" value={edit.home_score} onChange={e => setEdit(x => ({ ...x, home_score: e.target.value }))}
                className="w-10 border rounded px-1 text-center" />
              <span>–</span>
              <input type="number" min="0" value={edit.away_score} onChange={e => setEdit(x => ({ ...x, away_score: e.target.value }))}
                className="w-10 border rounded px-1 text-center" />
              <select value={edit.status} onChange={e => setEdit(x => ({ ...x, status: e.target.value }))}
                className="border rounded px-1 py-0.5 text-xs">
                {['scheduled','live','completed'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <button onClick={() => save(m.id)} className="text-xs bg-green-600 text-white px-2 py-1 rounded">Save</button>
              <button onClick={() => setEdit({})} className="text-xs text-gray-500 hover:underline">Cancel</button>
            </>
          ) : (
            <>
              <span className="font-mono text-gray-500">{m.home_score ?? '?'} – {m.away_score ?? '?'}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded ${m.status === 'completed' ? 'bg-green-100 text-green-700' : m.status === 'live' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>{m.status}</span>
              <button onClick={() => startEdit(m)} className="text-xs text-green-700 hover:underline">Edit</button>
            </>
          )}
          {msg[m.id] && <span className="text-xs text-gray-400">{msg[m.id]}</span>}
        </div>
      ))}
    </div>
  )
}

function UserManager() {
  const [users, setUsers] = useState([])
  const [msg, setMsg] = useState({})

  useEffect(() => {
    fetch('/api/admin/users', { credentials: 'include' }).then(r => r.json()).then(setUsers)
  }, [])

  async function lock(id) {
    await fetch(`/api/admin/users/${id}/lock`, { method: 'POST', credentials: 'include' })
    setMsg(m => ({ ...m, [id]: 'Locked' }))
    fetch('/api/admin/users', { credentials: 'include' }).then(r => r.json()).then(setUsers)
  }

  async function unlock(id) {
    await fetch(`/api/admin/users/${id}/unlock`, { method: 'POST', credentials: 'include' })
    setMsg(m => ({ ...m, [id]: 'Unlocked' }))
    fetch('/api/admin/users', { credentials: 'include' }).then(r => r.json()).then(setUsers)
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {users.map(u => (
        <div key={u.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded text-sm">
          <span className="flex-1 font-medium">{u.username}</span>
          <span className="text-xs text-gray-400">{u.email}</span>
          {u.is_admin && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">admin</span>}
          {!u.is_active && <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded">inactive</span>}
          {u.locked_until ? (
            <button onClick={() => unlock(u.id)} className="text-xs text-blue-600 hover:underline">Unlock</button>
          ) : (
            <button onClick={() => lock(u.id)} className="text-xs text-red-600 hover:underline">Lock</button>
          )}
          {msg[u.id] && <span className="text-xs text-gray-400">{msg[u.id]}</span>}
        </div>
      ))}
    </div>
  )
}

function Stats() {
  const [stats, setStats] = useState(null)
  useEffect(() => {
    fetch('/api/admin/stats', { credentials: 'include' }).then(r => r.json()).then(setStats)
  }, [])
  if (!stats) return <p className="text-gray-400">Loading…</p>
  return (
    <div className="grid grid-cols-3 gap-4">
      {[
        ['Active Sessions', stats.active_sessions],
        ['Total Users', stats.total_users],
        ['Predictions (24h)', stats.predictions_24h],
      ].map(([label, val]) => (
        <div key={label} className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-700">{val}</div>
          <div className="text-xs text-gray-500 mt-1">{label}</div>
        </div>
      ))}
    </div>
  )
}

const TABS = [['matches', 'Match Management'], ['users', 'User Management'], ['stats', 'System Stats']]

export default function Admin() {
  const [tab, setTab] = useState('matches')
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Admin</h1>
      <div className="flex gap-2">
        {TABS.map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2 rounded text-sm font-medium ${tab === key ? 'bg-green-700 text-white' : 'bg-white shadow text-gray-600 hover:bg-gray-50'}`}>
            {label}
          </button>
        ))}
      </div>
      <div className="bg-white rounded-lg shadow p-5">
        {tab === 'matches' && <MatchManager />}
        {tab === 'users' && <UserManager />}
        {tab === 'stats' && <Stats />}
      </div>
    </div>
  )
}
