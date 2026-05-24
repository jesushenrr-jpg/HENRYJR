'use client'

import { createClient } from '@/lib/supabase/client'
import { useState } from 'react'
import Link from 'next/link'

export default function LoginPage() {
  const [email, setEmail]         = useState('')
  const [senha, setSenha]         = useState('')
  const [nome, setNome]           = useState('')
  const [showPwd, setShowPwd]     = useState(false)
  const [modo, setModo]           = useState<'login' | 'cadastro'>('login')
  const [loading, setLoading]     = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [msg, setMsg]             = useState<{ texto: string; tipo: 'erro' | 'ok' } | null>(null)
  const supabase = createClient()

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMsg(null)

    const fn = modo === 'login'
      ? supabase.auth.signInWithPassword({ email, password: senha })
      : supabase.auth.signUp({
          email,
          password: senha,
          options: {
            emailRedirectTo: `${location.origin}/auth/callback`,
            data: { full_name: nome || email.split('@')[0] },
          },
        })

    const { error } = await fn
    if (error) {
      setMsg({ texto: traduzirErro(error.message), tipo: 'erro' })
    } else if (modo === 'cadastro') {
      setMsg({ texto: 'Verifique seu e-mail para confirmar o cadastro.', tipo: 'ok' })
    } else {
      window.location.href = '/'
    }
    setLoading(false)
  }

  async function handleGoogle() {
    setGoogleLoading(true)
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` },
    })
  }

  function traduzirErro(m: string): string {
    if (m.includes('Invalid login credentials')) return 'E-mail ou senha incorretos.'
    if (m.includes('Email not confirmed'))       return 'Confirme seu e-mail antes de entrar.'
    if (m.includes('User already registered'))   return 'Este e-mail já está cadastrado.'
    if (m.includes('Password should be'))        return 'A senha deve ter pelo menos 6 caracteres.'
    return m
  }

  return (
    <div className="anim-fade min-h-screen flex items-center justify-center px-4 py-10 relative overflow-hidden">

      {/* Glow de fundo */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[10%] left-1/3 w-[500px] h-[500px] rounded-full bg-[#D4A853]/15 blur-[120px] pulse-glow" />
        <div
          className="absolute bottom-[10%] right-1/4 w-[400px] h-[400px] rounded-full bg-sky-500/10 blur-[120px] pulse-glow"
          style={{ animationDelay: '1.2s' }}
        />
      </div>

      <div className="relative w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#D4A853] to-amber-600 mb-4 shadow-lg shadow-[#D4A853]/30">
            <span className="text-xl font-bold text-white">H</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            {modo === 'login' ? 'Bem-vindo de volta' : 'Crie sua conta'}
          </h1>
          <p className="text-sm text-white/45 mt-1">Acesse a plataforma de questões do ENEM</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5 sm:p-6">

          {/* Tabs */}
          <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-[#1E1B17]/60 mb-5">
            {(['login', 'cadastro'] as const).map(m => (
              <button
                key={m}
                onClick={() => { setModo(m); setMsg(null) }}
                className={`py-2 rounded-lg text-[13px] font-semibold transition ${
                  modo === m
                    ? 'bg-[#D4A853] text-[#0E0D0B] shadow-lg shadow-[#D4A853]/20'
                    : 'text-white/55 hover:text-white/85'
                }`}
              >
                {m === 'login' ? 'Entrar' : 'Cadastro'}
              </button>
            ))}
          </div>

          {/* Google */}
          <button
            onClick={handleGoogle}
            disabled={googleLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white hover:bg-white/95 disabled:opacity-70 text-zinc-800 font-semibold text-[13px] transition mb-4"
          >
            <svg viewBox="0 0 24 24" width="18" height="18">
              <path fill="#4285f4" d="M22.5 12.27c0-.79-.07-1.54-.2-2.27H12v4.51h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.32z"/>
              <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"/>
              <path fill="#fbbc04" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1 0-.74.13-1.44.35-2.1V7.07H2.18A11 11 0 0 0 1 12c0 1.78.43 3.46 1.18 4.94z"/>
              <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.07L5.84 9.9C6.71 7.31 9.14 5.38 12 5.38z"/>
            </svg>
            {googleLoading ? 'Redirecionando…' : 'Continuar com Google'}
          </button>

          <div className="flex items-center gap-3 my-4 text-[11px] text-white/35">
            <div className="flex-1 h-px bg-[#2C2820]" />
            ou e-mail
            <div className="flex-1 h-px bg-[#2C2820]" />
          </div>

          {/* Formulário */}
          <form onSubmit={handleEmail} className="space-y-3">

            {/* Campo nome — só no cadastro */}
            {modo === 'cadastro' && (
              <label className="block">
                <span className="block text-[11px] font-medium text-white/55 mb-1.5">Nome completo</span>
                <input
                  type="text"
                  value={nome}
                  onChange={e => setNome(e.target.value)}
                  placeholder="Como devemos te chamar?"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#1E1B17]/60 border border-[#2C2820] focus:border-[#D4A853]/50 focus:bg-[#1E1B17] outline-none text-[13px] placeholder:text-white/25 transition"
                />
              </label>
            )}

            <label className="block">
              <span className="block text-[11px] font-medium text-white/55 mb-1.5">E-mail</span>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="seu@email.com"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#1E1B17]/60 border border-[#2C2820] focus:border-[#D4A853]/50 focus:bg-[#1E1B17] outline-none text-[13px] placeholder:text-white/25 transition"
              />
            </label>

            <label className="block">
              <span className="block text-[11px] font-medium text-white/55 mb-1.5">Senha</span>
              <div className="relative">
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={senha}
                  onChange={e => setSenha(e.target.value)}
                  required
                  minLength={6}
                  placeholder="Mínimo 6 caracteres"
                  className="w-full px-3.5 py-2.5 pr-10 rounded-xl bg-[#1E1B17]/60 border border-[#2C2820] focus:border-[#D4A853]/50 focus:bg-[#1E1B17] outline-none text-[13px] placeholder:text-white/25 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/35 hover:text-white/75 transition"
                >
                  {showPwd ? <EyeOff /> : <Eye />}
                </button>
              </div>
            </label>

            {modo === 'login' && (
              <div className="flex justify-end -mt-1">
                <button
                  type="button"
                  className="text-[11px] text-amber-400 hover:text-amber-300 transition"
                  onClick={async () => {
                    if (!email) { setMsg({ texto: 'Digite seu e-mail primeiro.', tipo: 'erro' }); return }
                    const { error } = await supabase.auth.resetPasswordForEmail(email, {
                      redirectTo: `${location.origin}/auth/callback?next=/auth/reset-password`,
                    })
                    setMsg(error
                      ? { texto: 'Erro ao enviar e-mail.', tipo: 'erro' }
                      : { texto: 'E-mail de redefinição enviado! Verifique sua caixa.', tipo: 'ok' }
                    )
                  }}
                >
                  Esqueci minha senha
                </button>
              </div>
            )}

            {msg && (
              <p className={`text-sm text-center px-3 py-2 rounded-xl ${
                msg.tipo === 'ok'
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-red-500/10 text-red-400'
              }`}>
                {msg.texto}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-50 text-[#0E0D0B] font-semibold text-[13px] transition shadow-lg shadow-[#D4A853]/30 mt-1"
            >
              {loading ? 'Aguarde…' : modo === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </form>

          <p className="text-center text-[11px] text-white/35 mt-5">
            {modo === 'login' ? 'Não tem conta? ' : 'Já tem conta? '}
            <button
              onClick={() => { setModo(modo === 'login' ? 'cadastro' : 'login'); setMsg(null) }}
              className="text-amber-400 hover:text-amber-300 font-semibold transition"
            >
              {modo === 'login' ? 'Cadastre-se' : 'Faça login'}
            </button>
          </p>
        </div>

        <Link
          href="/"
          className="block text-center mt-5 text-[12px] text-white/40 hover:text-white/70 transition"
        >
          ← Voltar para a página inicial
        </Link>
      </div>
    </div>
  )
}

function Eye() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>
    </svg>
  )
}

function EyeOff() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>
      <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>
      <line x1="2" y1="2" x2="22" y2="22"/>
    </svg>
  )
}
