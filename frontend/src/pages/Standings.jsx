import { useEffect, useState } from 'react'

function GroupTable({ teams }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 border-b">
            <th className="text-left py-2 pr-4">Team</th>
            {['MP','W','D','L','GF','GA','GD','Pts'].map(h => (
              <th key={h} className="w-8 text-center py-2">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {teams.map((t, i) => (
            <tr key={t.id} className={`border-b last:border-0 ${i < 2 ? 'bg-green-50' : ''}`}>
              <td className="py-2 pr-4 font-medium">{t.name}</td>
              {[t.matches_played, t.wins, t.draws, t.losses, t.goals_for, t.goals_against, t.goal_difference, t.points].map((v, j) => (
                <td key={j} className={`text-center py-2 ${j === 7 ? 'font-bold' : ''}`}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function BracketRound({ label, matches }) {
  return (
    <div className="min-w-48">
      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">{label}</h3>
      <div className="space-y-2">
        {matches.map(m => (
          <div key={m.match_id} className="bg-white border rounded p-2 text-xs">
            <div className="flex justify-between gap-2">
              <span className="flex-1 truncate">{m.home_team?.name}</span>
              <span className="font-bold">{m.home_score ?? '–'}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="flex-1 truncate">{m.away_team?.name}</span>
              <span className="font-bold">{m.away_score ?? '–'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Standings() {
  const [tab, setTab] = useState('group')
  const [groups, setGroups] = useState([])
  const [group, setGroup] = useState(null)
  const [standings, setStandings] = useState({})
  const [bracket, setBracket] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch('/api/teams')
      .then(r => r.json())
      .then(teams => {
        const g = [...new Set(teams.map(t => t.group_name))].sort()
        setGroups(g)
        setGroup(g[0] ?? 'A')
      })
  }, [])

  useEffect(() => {
    if (!group) return
    if (tab === 'group') {
      setLoading(true)
      fetch(`/api/standings/group?group=${group}`)
        .then(r => r.json())
        .then(setStandings)
        .finally(() => setLoading(false))
    } else {
      if (bracket) return
      setLoading(true)
      fetch('/api/standings/knockout')
        .then(r => r.json())
        .then(setBracket)
        .finally(() => setLoading(false))
    }
  }, [tab, group])

  const BRACKET_ROUNDS = [
    ['round_of_16', 'Round of 16'],
    ['quarterfinal', 'Quarter Finals'],
    ['semifinal', 'Semi Finals'],
    ['third_place', 'Third Place'],
    ['final', 'Final'],
  ]

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Standings</h1>

      <div className="flex gap-2">
        {['group', 'knockout'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded font-medium text-sm capitalize ${tab === t ? 'bg-green-700 text-white' : 'bg-white text-gray-600 shadow hover:bg-gray-50'}`}>
            {t === 'group' ? 'Group Stage' : 'Knockout Bracket'}
          </button>
        ))}
      </div>

      {tab === 'group' && (
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {groups.map(g => (
              <button key={g} onClick={() => setGroup(g)}
                className={`w-10 h-10 rounded font-bold text-sm ${group === g ? 'bg-green-700 text-white' : 'bg-white shadow text-gray-600 hover:bg-gray-50'}`}>
                {g}
              </button>
            ))}
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="font-semibold mb-3">Group {group}</h2>
            {loading ? <p className="text-gray-400">Loading…</p> : (
              standings[group] ? <GroupTable teams={standings[group]} /> : <p className="text-gray-400">No data.</p>
            )}
            <p className="text-xs text-gray-400 mt-2">Top 2 advance (highlighted)</p>
          </div>
        </div>
      )}

      {tab === 'knockout' && (
        loading ? <p className="text-gray-400">Loading…</p> : bracket ? (
          <div className="overflow-x-auto">
            <div className="flex gap-6 min-w-max pb-4">
              {BRACKET_ROUNDS.map(([key, label]) =>
                bracket[key] ? <BracketRound key={key} label={label} matches={bracket[key]} /> : null
              )}
            </div>
          </div>
        ) : null
      )}
    </div>
  )
}
