import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { parseDate } from '../api/dates'

export default function MatchDetail() {
  const { id } = useParams()
  const [match, setMatch] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/matches/${id}`)
      .then(r => r.json())
      .then(setMatch)
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <p className="text-gray-400">Loading…</p>
  if (!match) return <p className="text-red-500">Match not found.</p>

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link to="/matches" className="text-green-700 hover:underline text-sm">← Back to Matches</Link>

      <div className="bg-white rounded-xl shadow p-6 text-center">
        <p className="text-sm text-gray-400 mb-4">
          {parseDate(match.match_date).toLocaleString()} · {match.venue?.name}, {match.venue?.city}
        </p>
        <div className="flex items-center justify-center gap-8">
          <div className="text-right">
            <Link to={`/teams/${match.home_team?.id}`} className="text-xl font-bold hover:text-green-700">
              {match.home_team?.name}
            </Link>
            <p className="text-xs text-gray-400">{match.home_team?.country_code}</p>
          </div>
          <div className="text-4xl font-bold px-4">
            {match.status === 'completed'
              ? `${match.home_score} – ${match.away_score}`
              : <span className="text-2xl text-gray-400">vs</span>}
          </div>
          <div className="text-left">
            <Link to={`/teams/${match.away_team?.id}`} className="text-xl font-bold hover:text-green-700">
              {match.away_team?.name}
            </Link>
            <p className="text-xs text-gray-400">{match.away_team?.country_code}</p>
          </div>
        </div>
        <p className="text-sm text-gray-500 mt-3 capitalize">{match.stage?.replace(/_/g, ' ')} · {match.status}</p>
      </div>

      {match.events?.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-4">Match Events</h2>
          <div className="space-y-2">
            {match.events.map((ev, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="w-10 text-right font-mono text-gray-400">{ev.minute}'</span>
                <span className="capitalize text-gray-500">{ev.event_type?.replace(/_/g, ' ')}</span>
                <span className="font-medium">{ev.player_name}</span>
                <span className="text-xs text-gray-400">{ev.team_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {match.events?.length === 0 && match.status === 'completed' && (
        <p className="text-gray-400 text-sm">No event details available for this match.</p>
      )}
    </div>
  )
}
