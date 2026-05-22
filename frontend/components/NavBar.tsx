import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import NavLinkActive from './NavLinkActive'

export default async function NavBar() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const iniciais = user?.email
    ? user.email.slice(0, 2).toUpperCase()
    : null

  return (
    <header className="sticky top-0 z-30 backdrop-blur-xl bg-[#0E0D0B]/85 border-b border-[#2C2820]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-[#1E1B17] border border-[#4A3F2F] flex items-center justify-center text-xs font-bold text-[#D4A853] shadow-sm group-hover:border-[#D4A853]/60 transition">
            H
          </div>
          <span className="font-bold text-[15px] tracking-tight text-[#F2EDE4]">
            Henry<span className="text-[#D4A853]">Jr</span>
          </span>
        </Link>

        {/* Nav desktop */}
        <nav className="hidden sm:flex items-center gap-5">
          <NavLinkActive href="/" label="Início" icon={<IconHome />} />
          <NavLinkActive href="/questoes" label="Questões" icon={<IconBook />} />
          {user && <NavLinkActive href="/simulado" label="Simulado" icon={<IconPlay />} />}
          {user && <NavLinkActive href="/tira-teima" label="Tira Teima" icon={<IconNote />} />}
          {user && <NavLinkActive href="/progresso" label="Progresso" icon={<IconChart />} />}
          {user && <NavLinkActive href="/corrigir" label="Corrigir foto" icon={<IconCamera />} />}
        </nav>

        {/* Auth */}
        <div className="flex items-center gap-2">
          {user ? (
            <>
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#1E1B17] border border-[#2C2820]">
                <div className="w-6 h-6 rounded-full bg-[#D4A853]/20 border border-[#D4A853]/30 flex items-center justify-center text-[10px] font-bold text-[#D4A853]">
                  {iniciais}
                </div>
                <span className="text-xs text-[#9E9589]">{user.email?.split('@')[0]}</span>
              </div>
              <form action="/auth/signout" method="post">
                <button
                  title="Sair"
                  className="p-1.5 rounded-lg text-[#635D56] hover:text-[#9E9589] hover:bg-[#1E1B17] transition"
                >
                  <IconLogout />
                </button>
              </form>
            </>
          ) : (
            <Link
              href="/auth/login"
              className="px-3.5 py-1.5 rounded-lg bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] text-[13px] font-semibold transition shadow-md shadow-[#D4A853]/20"
            >
              Entrar
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

/* ── Ícones ── */

function IconHome() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  )
}

function IconBook() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
    </svg>
  )
}

function IconChart() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="20" x2="12" y2="10"/>
      <line x1="18" y1="20" x2="18" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="16"/>
    </svg>
  )
}

function IconPlay() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="5 3 19 12 5 21 5 3"/>
    </svg>
  )
}

function IconNote() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  )
}

function IconCamera() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
      <circle cx="12" cy="13" r="4"/>
    </svg>
  )
}

function IconLogout() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  )
}
