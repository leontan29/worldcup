import { useEffect, useState } from 'react'

function LeaderboardTable({ players, stat }) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 border-b">
          <tr>
            <th className="text-left px-4 py-3 w-8">#</th>
            <th className="text-left px-4 py-3">Player</th>
            <th className="text-left px-4 py-3">Team</th>
            <th className="text-left px-4 py-3">Pos</th>
            <th className="text-center px-4 py-3">Goals</th>
            <th className="text-center px-4 py-3">Assists</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p, i) => (
            <tr key={p.id} className={`border-b last:border-0 ${i === 0 ? 'bg-yellow-50' : ''}`}>
              <td className="px-4 py-3 text-gray-400 font-mono">{i + 1}</td>
              <td className="px-4 py-3 font-medium">{p.name}</td>
              <td className="px-4 py-3 text-gray-500">{p.team_name}</td>
              <td className="px-4 py-3 text-gray-500">{p.position}</td>
              <td className={`px-4 py-3 text-center font-bold ${stat === 'goals' ? 'text-green-700' : ''}`}>{p.goals}</td>
              <td className={`px-4 py-3 text-center font-bold ${stat === 'assists' ? 'text-green-700' : ''}`}>{p.assists}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Players() {
  const [tab, setTab] = useState('goals')
  const [data, setData] = useState({ goals: null, assists: null })

  useEffect(() => {
    if (data[tab]) return
    fetch(`/api/leaderboards/${tab}`)
      .then(r => r.json())
      .then(rows => setData(d => ({ ...d, [tab]: rows })))
  }, [tab])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Player Stats</h1>
      <div className="flex gap-2">
        {['goals', 'assists'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded font-medium text-sm capitalize ${tab === t ? 'bg-green-700 text-white' : 'bg-white shadow text-gray-600 hover:bg-gray-50'}`}>
            Top {t === 'goals' ? 'Scorers' : 'Assisters'}
          </button>
        ))}
      </div>
      {data[tab] ? <LeaderboardTable players={data[tab]} stat={tab} /> : <p className="text-gray-400">Loading…</p>}
    </div>
  )
}
