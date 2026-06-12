import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { parseDate } from '../api/dates'

const STAGES = ['group', 'round_of_16', 'quarterfinal', 'semifinal', 'third_place', 'final']

function PredictForm({ match, onSaved }) {
  const [home, setHome] = useState('')
  const [away, setAway] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    setMsg('')
    const res = await fetch(`/api/predictions/${match.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ home_score: Number(home), away_score: Number(away) }),
    })
    const data = await res.json()
    setSaving(false)
    if (res.ok) { setMsg(data.created ? 'Saved!' : 'Updated!'); onSaved?.() }
    else setMsg(data.error || 'Error')
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-2 mt-2">
      <input type="number" min="0" max="20" value={home} onChange={e => setHome(e.target.value)}
        required className="w-12 border rounded px-1 py-0.5 text-sm text-center" placeholder="H" />
      <span className="text-gray-400 text-sm">–</span>
      <input type="number" min="0" max="20" value={away} onChange={e => setAway(e.target.value)}
        required className="w-12 border rounded px-1 py-0.5 text-sm text-center" placeholder="A" />
      <button type="submit" disabled={saving}
        className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700 disabled:opacity-50">
        {saving ? '…' : 'Predict'}
      </button>
      {msg && <span className="text-xs text-gray-500">{msg}</span>}
    </form>
  )
}

export default function Matches() {
  const { user } = useAuth()
  const [matches, setMatches] = useState([])
  const [teams, setTeams] = useState([])
  const [venues, setVenues] = useState([])
  const [filters, setFilters] = useState({ date: '', stage: '', team_id: '', venue_id: '' })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetch('/api/teams').then(r => r.json()), fetch('/api/venues').then(r => r.json())])
      .then(([t, v]) => { setTeams(t); setVenues(v) })
  }, [])

  function loadMatches() {
    setLoading(true)
    const params = new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([, v]) => v)))
    fetch(`/api/matches?${params}`)
      .then(r => r.json())
      .then(setMatches)
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadMatches() }, [filters])

  function setFilter(k) { return e => setFilters(f => ({ ...f, [k]: e.target.value })) }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Matches</h1>

      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-3">
        <input type="date" value={filters.date} onChange={setFilter('date')}
          className="border rounded px-2 py-1 text-sm" />
        <select value={filters.stage} onChange={setFilter('stage')}
          className="border rounded px-2 py-1 text-sm">
          <option value="">All Stages</option>
          {STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <select value={filters.team_id} onChange={setFilter('team_id')}
          className="border rounded px-2 py-1 text-sm">
          <option value="">All Teams</option>
          {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select value={filters.venue_id} onChange={setFilter('venue_id')}
          className="border rounded px-2 py-1 text-sm">
          <option value="">All Venues</option>
          {venues.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
        </select>
        <button onClick={() => setFilters({ date: '', stage: '', team_id: '', venue_id: '' })}
          className="text-sm text-gray-500 hover:text-gray-700">Clear</button>
      </div>

      {loading ? <p className="text-gray-400">Loading…</p> : (
        <div className="space-y-2">
          {matches.length === 0 && <p className="text-gray-400">No matches found.</p>}
          {matches.map(m => (
            <div key={m.id} className="bg-white rounded-lg shadow p-4">
              <div className="text-xs text-gray-400 mb-1">
                {parseDate(m.match_date).toLocaleString()} · {m.venue?.name} · <span className="capitalize">{m.stage?.replace(/_/g, ' ')}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="flex-1 text-right font-medium">{m.home_team?.name}</span>
                <span className="font-bold text-lg w-16 text-center">
                  {m.status === 'completed' ? `${m.home_score} – ${m.away_score}` : 'vs'}
                </span>
                <span className="flex-1 font-medium">{m.away_team?.name}</span>
                <Link to={`/matches/${m.id}`} className="text-xs text-green-700 hover:underline ml-2">Details</Link>
              </div>
              {user && m.status === 'scheduled' && (
                <PredictForm match={m} onSaved={loadMatches} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
