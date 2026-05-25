'use client'

import { useState, useRef } from 'react'

interface Props {
  questaoId: string
  enunciado: string[]
  comando: string
  alternativas: Record<string, string>
  gabarito: string
  ano: number
  numero: number
}

export default function ExplicarBtn({
  questaoId, enunciado, comando, alternativas, gabarito, ano, numero
}: Props) {
  const [estado, setEstado] = useState<'idle' | 'loading' | 'done' | 'erro'>('idle')
  const [texto, setTexto] = useState('')
  const [aberto, setAberto] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  async function explicar() {
    if (estado === 'loading') {
      abortRef.current?.abort()
      setEstado('idle')
      return
    }

    setEstado('loading')
    setTexto('')
    setAberto(true)
    abortRef.current = new AbortController()

    try {
      const res = await fetch('/api/explicar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enunciado: enunciado.join('\n'), comando, alternativas, gabarito, ano, numero }),
        signal: abortRef.current.signal,
      })

      if (!res.ok || !res.body) {
        setEstado('erro')
        setTexto('Não foi possível gerar a explicação. Tente novamente.')
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let acumulado = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        acumulado += decoder.decode(value, { stream: true })
        setTexto(acumulado)
      }

      setEstado('done')
    } catch (e: unknown) {
      if (e instanceof Error && e.name === 'AbortError') {
        setEstado('idle')
        return
      }
      setEstado('erro')
      setTexto('Erro de conexão. Verifique sua internet e tente novamente.')
    }
  }

  return (
    <div className="mt-2">
      <button
        onClick={explicar}
        className={`text-[11px] font-medium px-2.5 py-1 rounded-lg border transition-all ${
          estado === 'loading'
            ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 cursor-pointer'
            : 'bg-white/[0.04] border-white/10 text-white/50 hover:text-[#D4A853] hover:border-[#D4A853]/40 hover:bg-[#D4A853]/5 cursor-pointer'
        }`}
      >
        {estado === 'loading' ? (
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 border-2 border-amber-400/60 border-t-amber-400 rounded-full animate-spin" />
            Gerando...
          </span>
        ) : (
          <span className="flex items-center gap-1">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            {estado === 'done' ? 'Ver explicação' : 'Explicar com IA'}
          </span>
        )}
      </button>

      {aberto && texto && (
        <div className="mt-2 rounded-xl bg-[#0E0D0B] border border-[#D4A853]/20 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-[#D4A853]/60 font-medium uppercase tracking-wider">
              Explicação gerada por IA
            </span>
            <button
              onClick={() => { setAberto(false); setEstado('idle'); setTexto('') }}
              className="text-white/30 hover:text-white/60 transition"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          <div className="text-[12px] text-white/75 leading-relaxed whitespace-pre-wrap font-serif">
            {texto}
            {estado === 'loading' && (
              <span className="inline-block w-0.5 h-3.5 bg-amber-400 ml-0.5 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
