'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function BuscaIA() {
  const [query, setQuery]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [erro, setErro]         = useState<string | null>(null)
  const [preview, setPreview]   = useState<{ termos: string[]; area: string | null; competencia: string | null } | null>(null)
  const router = useRouter()

  async function buscar() {
    const q = query.trim()
    if (!q) return
    setLoading(true)
    setErro(null)
    setPreview(null)
    try {
      const res = await fetch('/api/busca-ia', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error ?? 'Erro na busca')

      const { termos, area, competencia } = data as {
        termos: string[]
        area: string | null
        competencia: string | null
      }

      setPreview({ termos, area, competencia })

      const sp = new URLSearchParams()
      sp.set('busca', termos.join(','))
      sp.set('ia', '1')
      if (area)        sp.set('area', area)
      if (competencia) sp.set('competencia', competencia)
      router.push(`/questoes?${sp}`)
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : 'Erro ao buscar')
    }
    setLoading(false)
  }

  return (
    <div className="mb-5 rounded-2xl border border-[#D4A853]/30 bg-gradient-to-br from-[#D4A853]/10 via-[#161411] to-[#161411] p-4 sm:p-5 relative overflow-hidden">
      {/* Glow decorativo */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#D4A853]/10 blur-3xl rounded-full pointer-events-none" />

      <div className="relative">
        {/* Cabeçalho */}
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#D4A853] to-amber-600 flex items-center justify-center shrink-0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/>
            </svg>
          </div>
          <div>
            <div className="text-[14px] font-semibold flex items-center gap-2">
              Busca inteligente
              <span className="text-[9px] font-bold bg-gradient-to-r from-[#D4A853] to-amber-600 px-1.5 py-0.5 rounded tracking-wider text-[#0E0D0B]">IA</span>
            </div>
            <div className="text-[11px] text-white/50">Descreva um tema e a IA encontra questões relacionadas</div>
          </div>
        </div>

        {/* Campo + botão */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 relative">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && buscar()}
              placeholder='Ex: "fake news", "fotossíntese", "funções do 2° grau"…'
              className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-[#1E1B17]/80 border border-[#2C2820] focus:border-[#D4A853]/50 focus:bg-[#1E1B17] outline-none text-[13px] placeholder:text-white/25 transition"
            />
          </div>
          <button
            onClick={buscar}
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-40 disabled:cursor-not-allowed text-[#0E0D0B] text-[13px] font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-[#D4A853]/20 shrink-0"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Buscando…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/>
                </svg>
                Buscar com IA
              </>
            )}
          </button>
        </div>

        {/* Feedback da IA */}
        {preview && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[11px]">
            <span className="text-white/35">IA identificou:</span>
            {preview.termos.map(t => (
              <span key={t} className="px-2 py-0.5 rounded-md bg-[#D4A853]/15 border border-[#D4A853]/25 text-amber-300">
                {t}
              </span>
            ))}
            {preview.area && (
              <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-white/45">
                {preview.area.replace(' e suas Tecnologias', '')}
              </span>
            )}
            {preview.competencia && (
              <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-white/45 font-mono">
                {preview.competencia}
              </span>
            )}
          </div>
        )}

        {erro && (
          <p className="mt-2 text-[12px] text-rose-400">{erro}</p>
        )}
      </div>
    </div>
  )
}
