import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <nav className="bg-green-700 text-white px-6 py-3 flex items-center gap-6">
      <Link to="/" className="font-bold text-lg">WorldCup Hub</Link>
      <Link to="/matches">Matches</Link>
      <Link to="/standings">Standings</Link>
      <Link to="/teams">Teams</Link>
      <Link to="/players">Players</Link>
      <Link to="/leaderboard">Leaderboard</Link>
      <div className="ml-auto flex gap-4 items-center">
        {user ? (
          <>
            <Link to="/predictions">Predictions</Link>
            <Link to="/profile">{user.username}</Link>
            {user.is_admin && <Link to="/admin">Admin</Link>}
            <button onClick={handleLogout} className="underline">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}
