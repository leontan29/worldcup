import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'

const POS_ORDER = { GK: 0, DEF: 1, MID: 2, FWD: 3 }

export default function TeamDetail() {
  const { id } = useParams()
  const [team, setTeam] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/teams/${id}`).then(r => r.json()).then(setTeam).finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="text-gray-400">Loading…</p>
  if (!team) return <p className="text-red-500">Team not found.</p>

  const sorted = [...(team.players || [])].sort((a, b) =>
    POS_ORDER[a.position] - POS_ORDER[b.position] || a.jersey_number - b.jersey_number
  )

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/teams" className="text-green-700 hover:underline text-sm">← Back to Teams</Link>
      <div className="bg-white rounded-xl shadow p-6">
        <h1 className="text-2xl font-bold">{team.name}</h1>
        <div className="text-gray-500 text-sm mt-1">
          Group {team.group_name} · FIFA #{team.fifa_ranking} · Coach: {team.coach}
        </div>
      </div>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 border-b">
            <tr>
              <th className="text-left px-4 py-3">#</th>
              <th className="text-left px-4 py-3">Name</th>
              <th className="text-left px-4 py-3">Pos</th>
              <th className="text-center px-4 py-3">G</th>
              <th className="text-center px-4 py-3">A</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(p => (
              <tr key={p.id} className="border-b last:border-0 hover:bg-gray-50">
                <td className="px-4 py-2 text-gray-400">{p.jersey_number}</td>
                <td className="px-4 py-2 font-medium">{p.name}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium
                    ${p.position === 'GK' ? 'bg-yellow-100 text-yellow-700' :
                      p.position === 'DEF' ? 'bg-blue-100 text-blue-700' :
                      p.position === 'MID' ? 'bg-green-100 text-green-700' :
                      'bg-red-100 text-red-700'}`}>
                    {p.position}
                  </span>
                </td>
                <td className="px-4 py-2 text-center">{p.goals}</td>
                <td className="px-4 py-2 text-center">{p.assists}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
