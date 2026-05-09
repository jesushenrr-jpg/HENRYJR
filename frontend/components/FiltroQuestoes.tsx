'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useState, useTransition } from 'react'

interface Props {
  anos: number[]
  areas: string[]
}

export default function FiltroQuestoes({ anos, areas }: Props) {
  const router = useRouter()
  const sp = useSearchParams()
  const [isPending, startTransition] = useTransition()

  const [ano, setAno] = useState(sp.get('ano') ?? '')
  const [dia, setDia] = useState(sp.get('dia') ?? '')
  const [area, setArea] = useState(sp.get('area') ?? '')

  function aplicar() {
    const params = new URLSearchParams()
    if (ano) params.set('ano', ano)
    if (dia) params.set('dia', dia)
    if (area) params.set('area', area)
    startTransition(() => router.push(`/questoes?${params}`))
  }

  function limpar() {
    setAno(''); setDia(''); setArea('')
    startTransition(() => router.push('/questoes'))
  }

  const sel = 'bg-[#313244] text-white border border-[#45475a] rounded-xl px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[#7c6af7]'

  return (
    <div className="bg-[#2a2a3e] rounded-2xl p-4 flex flex-wrap gap-3 items-end">
      <div className="flex flex-col gap-1">
        <label className="text-[#a6adc8] text-xs">Ano</label>
        <select value={ano} onChange={e => setAno(e.target.value)} className={sel}>
          <option value="">Todos</option>
          {anos.slice().reverse().map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[#a6adc8] text-xs">Dia</label>
        <select value={dia} onChange={e => setDia(e.target.value)} className={sel}>
          <option value="">Ambos</option>
          <option value="dia1">Dia 1</option>
          <option value="dia2">Dia 2</option>
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-[#a6adc8] text-xs">Área</label>
        <select value={area} onChange={e => setArea(e.target.value)} className={`${sel} max-w-xs`}>
          <option value="">Todas</option>
          {areas.map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <button
        onClick={aplicar}
        disabled={isPending}
        className="bg-[#7c6af7] hover:bg-[#9580ff] text-white font-bold px-5 py-2 rounded-xl text-sm transition disabled:opacity-50"
      >
        {isPending ? '…' : 'Filtrar'}
      </button>

      <button
        onClick={limpar}
        className="bg-[#313244] hover:bg-[#45475a] text-[#a6adc8] px-4 py-2 rounded-xl text-sm transition"
      >
        Limpar
      </button>
    </div>
  )
}
