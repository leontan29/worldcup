import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

const GROUPS = ['A','B','C','D','E','F','G','H']

export default function Teams() {
  const [teams, setTeams] = useState([])
  const [group, setGroup] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const url = group ? `/api/teams?group=${group}` : '/api/teams'
    setLoading(true)
    fetch(url).then(r => r.json()).then(setTeams).finally(() => setLoading(false))
  }, [group])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Teams</h1>
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setGroup('')}
          className={`px-3 py-1 rounded text-sm font-medium ${group === '' ? 'bg-green-700 text-white' : 'bg-white shadow text-gray-600 hover:bg-gray-50'}`}>
          All
        </button>
        {GROUPS.map(g => (
          <button key={g} onClick={() => setGroup(g)}
            className={`w-9 h-9 rounded text-sm font-bold ${group === g ? 'bg-green-700 text-white' : 'bg-white shadow text-gray-600 hover:bg-gray-50'}`}>
            {g}
          </button>
        ))}
      </div>
      {loading ? <p className="text-gray-400">Loading…</p> : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {teams.map(t => (
            <Link key={t.id} to={`/teams/${t.id}`}
              className="bg-white rounded-lg shadow p-4 hover:shadow-md transition">
              <div className="font-bold">{t.name}</div>
              <div className="text-xs text-gray-500 mt-1">
                Group {t.group_name} · #{t.fifa_ranking} FIFA
              </div>
              <div className="text-xs text-gray-400 mt-1">{t.coach}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
