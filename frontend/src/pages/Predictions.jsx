import { useEffect, useState } from 'react'

function PredictRow({ pred, onUpdate }) {
  const [home, setHome] = useState(String(pred.predicted_home))
  const [away, setAway] = useState(String(pred.predicted_away))
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  const canEdit = pred.status === 'scheduled'

  async function save(e) {
    e.preventDefault()
    setSaving(true)
    const res = await fetch(`/api/predictions/${pred.match_id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ home_score: Number(home), away_score: Number(away) }),
    })
    setSaving(false)
    if (res.ok) { setMsg('Saved'); onUpdate?.() }
    else setMsg('Error')
  }

  return (
    <tr className="border-b last:border-0">
      <td className="px-4 py-3 text-sm">
        <div className="font-medium">{pred.home_team} vs {pred.away_team}</div>
        <div className="text-xs text-gray-400">{new Date(pred.match_date).toLocaleDateString()} · <span className="capitalize">{pred.stage}</span></div>
      </td>
      <td className="px-4 py-3 text-center text-sm">
        {canEdit ? (
          <form onSubmit={save} className="flex items-center gap-1 justify-center">
            <input type="number" min="0" max="20" value={home} onChange={e => setHome(e.target.value)}
              className="w-10 border rounded px-1 py-0.5 text-center text-sm" />
            <span>–</span>
            <input type="number" min="0" max="20" value={away} onChange={e => setAway(e.target.value)}
              className="w-10 border rounded px-1 py-0.5 text-center text-sm" />
            <button type="submit" disabled={saving}
              className="text-xs bg-green-600 text-white px-2 py-1 rounded ml-1 disabled:opacity-50">
              {saving ? '…' : 'Save'}
            </button>
            {msg && <span className="text-xs text-gray-400">{msg}</span>}
          </form>
        ) : (
          <span className="font-mono">{pred.predicted_home} – {pred.predicted_away}</span>
        )}
      </td>
      <td className="px-4 py-3 text-center text-sm font-mono text-gray-500">
        {pred.status === 'completed' ? `${pred.actual_home} – ${pred.actual_away}` : '—'}
      </td>
      <td className="px-4 py-3 text-center">
        {pred.points_earned != null ? (
          <span className={`font-bold ${pred.points_earned === 3 ? 'text-green-600' : pred.points_earned === 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            {pred.points_earned} pts
          </span>
        ) : <span className="text-gray-300 text-sm">—</span>}
      </td>
    </tr>
  )
}

export default function Predictions() {
  const [preds, setPreds] = useState([])
  const [loading, setLoading] = useState(true)

  function load() {
    fetch('/api/user/predictions', { credentials: 'include' })
      .then(r => r.json())
      .then(setPreds)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const total = preds.reduce((s, p) => s + (p.points_earned || 0), 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Predictions</h1>
        {preds.length > 0 && (
          <div className="text-sm text-gray-500">
            Total: <span className="font-bold text-green-700">{total} pts</span>
          </div>
        )}
      </div>
      {loading ? <p className="text-gray-400">Loading…</p> : preds.length === 0 ? (
        <p className="text-gray-400">No predictions yet. Head to <a href="/matches" className="text-green-700 hover:underline">Matches</a> to predict!</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 border-b text-xs">
              <tr>
                <th className="text-left px-4 py-3">Match</th>
                <th className="text-center px-4 py-3">Predicted</th>
                <th className="text-center px-4 py-3">Actual</th>
                <th className="text-center px-4 py-3">Points</th>
              </tr>
            </thead>
            <tbody>
              {preds.map(p => <PredictRow key={p.id} pred={p} onUpdate={load} />)}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
