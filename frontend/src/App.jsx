import { Routes, Route, Outlet } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Matches from './pages/Matches'
import MatchDetail from './pages/MatchDetail'
import Standings from './pages/Standings'
import Teams from './pages/Teams'
import TeamDetail from './pages/TeamDetail'
import Players from './pages/Players'
import Leaderboard from './pages/Leaderboard'
import Predictions from './pages/Predictions'
import Profile from './pages/Profile'
import Admin from './pages/Admin'

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/matches" element={<Matches />} />
        <Route path="/matches/:id" element={<MatchDetail />} />
        <Route path="/standings" element={<Standings />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/teams/:id" element={<TeamDetail />} />
        <Route path="/players" element={<Players />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/predictions" element={
          <ProtectedRoute><Predictions /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><Profile /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute adminOnly><Admin /></ProtectedRoute>
        } />
      </Route>
    </Routes>
  )
}
