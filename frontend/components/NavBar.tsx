import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'

export default async function NavBar() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  return (
    <nav className="bg-[#2a2a3e] border-b border-[#45475a] px-6 py-3 flex items-center justify-between">
      <Link href="/" className="text-[#7c6af7] font-bold text-xl tracking-tight">
        HenryJr
      </Link>
      <div className="flex items-center gap-4 text-sm">
        <Link href="/questoes" className="text-[#a6adc8] hover:text-white transition">
          Questões
        </Link>
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-[#585b70]">{user.email?.split('@')[0]}</span>
            <form action="/auth/signout" method="post">
              <button className="text-[#585b70] hover:text-[#f38ba8] transition">Sair</button>
            </form>
          </div>
        ) : (
          <Link
            href="/auth/login"
            className="bg-[#7c6af7] hover:bg-[#9580ff] text-white font-bold px-4 py-1.5 rounded-xl transition"
          >
            Entrar
          </Link>
        )}
      </div>
    </nav>
  )
}
