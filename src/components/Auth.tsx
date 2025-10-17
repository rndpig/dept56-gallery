import React, { useState } from 'react'
import { supabase } from '../lib/supabase'

interface AuthProps {
  onAuthSuccess: () => void
}

export function Auth({ onAuthSuccess }: AuthProps) {
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null)

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
        })
        if (error) throw error
        setMessage({
          type: 'success',
          text: 'Check your email for the confirmation link!',
        })
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error
        onAuthSuccess()
      }
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.message || 'An error occurred',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="rounded-3xl border border-gray-200 bg-white shadow-lg p-8">
          <div className="flex items-center justify-center mb-6">
            <span className="inline-grid place-items-center h-16 w-16 rounded-2xl bg-indigo-600 text-white font-bold text-2xl">
              56
            </span>
          </div>
          <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
            Department 56 Gallery
          </h1>
          <p className="text-center text-gray-600 mb-6">
            {isSignUp ? 'Create your account' : 'Sign in to your collection'}
          </p>

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-xl border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full rounded-xl border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="••••••••"
              />
            </div>

            {message && (
              <div
                className={`rounded-xl p-3 text-sm ${
                  message.type === 'error'
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-green-50 text-green-700 border border-green-200'
                }`}
              >
                {message.text}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white rounded-xl px-4 py-3 text-sm font-medium hover:bg-indigo-700 active:scale-[0.99] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : isSignUp ? 'Sign Up' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsSignUp(!isSignUp)
                setMessage(null)
              }}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
            </button>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          Your collection data is private and secure
        </p>
      </div>
    </div>
  )
}
