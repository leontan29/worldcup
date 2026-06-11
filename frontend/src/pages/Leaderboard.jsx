import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Leaderboard() {
  const { user } = useAuth()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/predictions/leaderboard')
      .then(r => r.json())
      .then(setRows)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Leaderboard</h1>
      {loading ? <p className="text-gray-400">Loading…</p> : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 border-b">
              <tr>
                <th className="text-left px-4 py-3 w-12">Rank</th>
                <th className="text-left px-4 py-3">Username</th>
                <th className="text-center px-4 py-3">Points</th>
                <th className="text-center px-4 py-3">Exact</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const isMe = user && r.username === user.username
                return (
                  <tr key={r.id} className={`border-b last:border-0 ${isMe ? 'bg-green-50 font-semibold' : i < 3 ? 'bg-yellow-50' : ''}`}>
                    <td className="px-4 py-3 font-mono text-gray-400">
                      {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                    </td>
                    <td className="px-4 py-3">{r.username}{isMe && <span className="text-green-600 text-xs ml-1">(you)</span>}</td>
                    <td className="px-4 py-3 text-center font-bold text-green-700">{r.total_points}</td>
                    <td className="px-4 py-3 text-center text-gray-500">{r.exact_count}</td>
                  </tr>
                )
              })}
              {rows.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-400">No predictions scored yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
