import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { parseDate } from '../api/dates'

function MatchCard({ match }) {
  return (
    <Link to={`/matches/${match.id}`} className="block bg-white rounded-lg shadow p-4 hover:shadow-md transition">
      <div className="text-xs text-gray-500 mb-2">
        {parseDate(match.match_date).toLocaleString()} · {match.venue?.name}
      </div>
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 text-right font-medium">{match.home_team?.name}</div>
        <div className="text-center font-bold text-lg w-16">
          {match.status === 'completed'
            ? `${match.home_score} – ${match.away_score}`
            : 'vs'}
        </div>
        <div className="flex-1 font-medium">{match.away_team?.name}</div>
      </div>
      <div className="text-xs text-center text-gray-400 mt-1 capitalize">{match.stage} · {match.status}</div>
    </Link>
  )
}

export default function Home() {
  const { user } = useAuth()
  const [matches, setMatches] = useState([])
  const [label, setLabel] = useState('')
  const [loading, setLoading] = useState(true)
  const [info, setInfo] = useState(null)

  useEffect(() => {
    fetch('/api/info').then(r => r.json()).then(setInfo)
  }, [])

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10)
    fetch(`/api/matches?date=${today}`)
      .then(r => r.json())
      .then(data => {
        if (data.length > 0) {
          setMatches(data)
          setLabel("Today's Matches")
          return
        }
        return fetch('/api/matches').then(r => r.json()).then(all => {
          const upcoming = all.filter(m => m.status === 'scheduled').slice(0, 5)
          if (upcoming.length > 0) {
            setMatches(upcoming)
            setLabel('Upcoming Matches')
          } else {
            const recent = all.filter(m => m.status === 'completed').slice(-5).reverse()
            setMatches(recent)
            setLabel('Recent Results')
          }
        })
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-8">
      <div className="text-center py-8 bg-green-700 text-white rounded-xl">
        <h1 className="text-3xl font-bold mb-2">WorldCup Hub</h1>
        <p className="text-green-200">{info ? `${info.year} FIFA World Cup · ${info.host}` : ''}</p>
        {!user && (
          <div className="mt-4 flex gap-3 justify-center">
            <Link to="/register" className="bg-white text-green-700 font-semibold px-4 py-2 rounded hover:bg-green-50">
              Get Started
            </Link>
            <Link to="/login" className="border border-white text-white px-4 py-2 rounded hover:bg-green-600">
              Sign In
            </Link>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { to: '/matches', label: 'Matches' },
          { to: '/standings', label: 'Standings' },
          { to: '/teams', label: 'Teams' },
          { to: '/leaderboard', label: 'Leaderboard' },
        ].map(({ to, label }) => (
          <Link key={to} to={to}
            className="bg-white rounded-lg shadow p-4 text-center font-medium text-green-700 hover:bg-green-50 hover:shadow-md transition">
            {label}
          </Link>
        ))}
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-3">{label}</h2>
        {loading ? (
          <p className="text-gray-400">Loading…</p>
        ) : matches.length === 0 ? (
          <p className="text-gray-400">No matches found.</p>
        ) : (
          <div className="space-y-3">
            {matches.map(m => <MatchCard key={m.id} match={m} />)}
          </div>
        )}
        <Link to="/matches" className="inline-block mt-4 text-green-700 hover:underline text-sm">
          View all matches →
        </Link>
      </section>
    </div>
  )
}
