'use client'

import { createClient } from '@/lib/supabase/client'
import { useState } from 'react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [modo, setModo] = useState<'login' | 'cadastro'>('login')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')
  const supabase = createClient()

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMsg('')
    const fn = modo === 'login'
      ? supabase.auth.signInWithPassword({ email, password: senha })
      : supabase.auth.signUp({ email, password: senha, options: { emailRedirectTo: `${location.origin}/auth/callback` } })
    const { error } = await fn
    if (error) setMsg(error.message)
    else if (modo === 'cadastro') setMsg('Verifique seu e-mail para confirmar o cadastro.')
    else window.location.href = '/'
    setLoading(false)
  }

  async function handleGoogle() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` },
    })
  }

  return (
    <div className="min-h-screen bg-[#1e1e2e] flex items-center justify-center p-4">
      <div className="bg-[#2a2a3e] rounded-2xl p-8 w-full max-w-md shadow-xl">
        <h1 className="text-2xl font-bold text-white mb-2 text-center">HenryJr</h1>
        <p className="text-[#a6adc8] text-center text-sm mb-8">Banco de Questões ENEM</p>

        {/* Google */}
        <button
          onClick={handleGoogle}
          className="w-full flex items-center justify-center gap-3 bg-white text-gray-800 font-semibold py-3 rounded-xl mb-6 hover:bg-gray-100 transition"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuar com Google
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-[#45475a]" />
          <span className="text-[#585b70] text-xs">ou</span>
          <div className="flex-1 h-px bg-[#45475a]" />
        </div>

        {/* Email */}
        <form onSubmit={handleEmail} className="space-y-4">
          <input
            type="email"
            placeholder="E-mail"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full bg-[#313244] text-white placeholder-[#585b70] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-[#7c6af7]"
          />
          <input
            type="password"
            placeholder="Senha"
            value={senha}
            onChange={e => setSenha(e.target.value)}
            required
            className="w-full bg-[#313244] text-white placeholder-[#585b70] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-[#7c6af7]"
          />
          {msg && <p className="text-sm text-[#fab387] text-center">{msg}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#7c6af7] hover:bg-[#9580ff] text-white font-bold py-3 rounded-xl transition disabled:opacity-50"
          >
            {loading ? 'Aguarde…' : modo === 'login' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        <p className="text-center text-sm text-[#a6adc8] mt-4">
          {modo === 'login' ? 'Não tem conta?' : 'Já tem conta?'}{' '}
          <button
            onClick={() => { setModo(m => m === 'login' ? 'cadastro' : 'login'); setMsg('') }}
            className="text-[#7c6af7] hover:underline"
          >
            {modo === 'login' ? 'Criar conta' : 'Entrar'}
          </button>
        </p>
      </div>
    </div>
  )
}
