'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useState, useTransition } from 'react'
import { TODAS_HABILIDADES } from '@/lib/competencias'

interface Props {
  anos: number[]
  areas: string[]
}

export default function FiltroQuestoes({ anos, areas }: Props) {
  const router = useRouter()
  const sp = useSearchParams()
  const [isPending, startTransition] = useTransition()
  const [aberto, setAberto] = useState(
    !!(sp.get('ano') || sp.get('dia') || sp.get('area') || sp.get('competencia'))
  )

  const [ano,        setAno]        = useState(sp.get('ano')        ?? '')
  const [dia,        setDia]        = useState(sp.get('dia')        ?? '')
  const [area,       setArea]       = useState(sp.get('area')       ?? '')
  const [competencia,setCompetencia]= useState(sp.get('competencia')?? '')

  function aplicar() {
    const params = new URLSearchParams()
    if (ano)         params.set('ano', ano)
    if (dia)         params.set('dia', dia)
    if (area)        params.set('area', area)
    if (competencia) params.set('competencia', competencia)
    startTransition(() => router.push(`/questoes?${params}`))
  }

  function limpar() {
    setAno(''); setDia(''); setArea(''); setCompetencia('')
    startTransition(() => router.push('/questoes'))
  }

  const temFiltro = !!(ano || dia || area || competencia)

  const sel = 'bg-[#1E1B17]/60 text-white border border-[#2C2820] rounded-xl px-3 py-2 text-[13px] outline-none focus:border-[#D4A853]/50 transition'

  return (
    <div className="bg-[#161411] border border-[#2C2820] rounded-2xl overflow-hidden">
      <button
        onClick={() => setAberto(a => !a)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-white/[0.02] transition"
      >
        <div className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/40">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46"/>
          </svg>
          <span className="text-white/60 text-[13px] font-medium">Filtros</span>
          {temFiltro && (
            <span className="bg-[#D4A853]/20 text-amber-300 text-[10px] px-2 py-0.5 rounded-full border border-[#D4A853]/25 font-semibold">
              {[ano, dia, area, competencia].filter(Boolean).length} ativo{[ano, dia, area, competencia].filter(Boolean).length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <span className="text-white/30 text-[10px]">{aberto ? '▲' : '▼'}</span>
      </button>

      {aberto && (
        <div className="px-5 pb-5 pt-1 border-t border-[#2C2820]/50">
          <div className="flex flex-wrap gap-3 items-end mt-3">

            <div className="flex flex-col gap-1.5">
              <label className="text-white/40 text-[10px] uppercase tracking-wider font-medium">Ano</label>
              <select value={ano} onChange={e => setAno(e.target.value)} className={sel}>
                <option value="">Todos</option>
                {anos.map(a => (
                  <option key={a} value={a} className="bg-[#161411]">{a}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-white/40 text-[10px] uppercase tracking-wider font-medium">Dia</label>
              <select value={dia} onChange={e => setDia(e.target.value)} className={sel}>
                <option value="">Ambos</option>
                <option value="dia1" className="bg-[#161411]">Dia 1</option>
                <option value="dia2" className="bg-[#161411]">Dia 2</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-white/40 text-[10px] uppercase tracking-wider font-medium">Área</label>
              <select value={area} onChange={e => { setArea(e.target.value); setCompetencia('') }} className={`${sel} max-w-[220px]`}>
                <option value="">Todas</option>
                {areas.map(a => (
                  <option key={a} value={a} className="bg-[#161411]">
                    {a.replace(' e suas Tecnologias', '')}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-white/40 text-[10px] uppercase tracking-wider font-medium">Competência</label>
              <select value={competencia} onChange={e => setCompetencia(e.target.value)} className={sel}>
                <option value="">Todas</option>
                {TODAS_HABILIDADES.map(h => (
                  <option key={h} value={h} className="bg-[#161411]">{h}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 ml-auto">
              {temFiltro && (
                <button onClick={limpar} className="bg-white/[0.04] hover:bg-white/[0.08] border border-[#2C2820] text-white/50 hover:text-white/80 px-4 py-2 rounded-xl text-[13px] transition">
                  Limpar
                </button>
              )}
              <button
                onClick={aplicar}
                disabled={isPending}
                className="bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-50 text-[#0E0D0B] font-semibold px-5 py-2 rounded-xl text-[13px] transition shadow-lg shadow-[#D4A853]/20"
              >
                {isPending ? '…' : 'Aplicar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
