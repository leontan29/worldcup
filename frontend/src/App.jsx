import { Routes, Route, Outlet } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'

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

const Placeholder = ({ name }) => <div className="p-4 text-gray-500">{name}</div>

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/matches" element={<Placeholder name="Matches" />} />
        <Route path="/matches/:id" element={<Placeholder name="Match Detail" />} />
        <Route path="/standings" element={<Placeholder name="Standings" />} />
        <Route path="/teams" element={<Placeholder name="Teams" />} />
        <Route path="/teams/:id" element={<Placeholder name="Team Detail" />} />
        <Route path="/players" element={<Placeholder name="Players" />} />
        <Route path="/leaderboard" element={<Placeholder name="Leaderboard" />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/predictions" element={
          <ProtectedRoute><Placeholder name="Predictions" /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><Placeholder name="Profile" /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute adminOnly><Placeholder name="Admin" /></ProtectedRoute>
        } />
      </Route>
    </Routes>
  )
}
