import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function strength(pw) {
  let score = 0
  if (pw.length >= 8) score++
  if (/[A-Z]/.test(pw)) score++
  if (/[0-9]/.test(pw)) score++
  if (/[^a-zA-Z0-9]/.test(pw)) score++
  return score
}

const STRENGTH_LABEL = ['', 'Weak', 'Fair', 'Good', 'Strong']
const STRENGTH_COLOR = ['', 'bg-red-400', 'bg-yellow-400', 'bg-blue-400', 'bg-green-500']

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  function set(field) {
    return e => setForm(f => ({ ...f, [field]: e.target.value }))
  }

  const pwStrength = strength(form.password)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setErrors({})
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (!res.ok) {
        if (data.details) setErrors(data.details)
        else setErrors({ general: data.error || 'Registration failed' })
        return
      }
      await login(data)
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-6 text-center">Create Account</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-4">
        {errors.general && (
          <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{errors.general}</p>
        )}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            type="text"
            value={form.username}
            onChange={set('username')}
            required
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username[0]}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            value={form.email}
            onChange={set('email')}
            required
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email[0]}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            type="password"
            value={form.password}
            onChange={set('password')}
            required
            className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          {form.password && (
            <div className="mt-1">
              <div className="flex gap-1 h-1">
                {[1,2,3,4].map(i => (
                  <div key={i} className={`flex-1 rounded ${i <= pwStrength ? STRENGTH_COLOR[pwStrength] : 'bg-gray-200'}`} />
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">{STRENGTH_LABEL[pwStrength]}</p>
            </div>
          )}
          {errors.password && (
            <ul className="text-red-500 text-xs mt-1 list-disc list-inside">
              {errors.password.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-700 text-white py-2 rounded font-medium hover:bg-green-800 disabled:opacity-50"
        >
          {loading ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="text-center text-sm text-gray-500">
          Have an account? <Link to="/login" className="text-green-700 hover:underline">Sign in</Link>
        </p>
      </form>
    </div>
  )
}
