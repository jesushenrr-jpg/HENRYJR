'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface Questao {
  id:           number
  ano:          number
  dia:          string
  numero:       number
  area:         string
  competencia:  string | null
  enunciado:    string[]
  comando:      string | null
  alternativas: Record<string, string>
  gabarito:     string | null
  tem_imagem:   boolean
  imagens:      { path: string; posicao: string }[]
}

interface Props {
  simuladoId:    number
  questoes:      Questao[]
  totalQuestoes: number
}

const LETRAS = ['A', 'B', 'C', 'D', 'E'] as const

// Detecta paragráfo de fonte/citação
function isFonte(p: string) {
  return /^(Disponível|[A-Z][A-Z]+,\s|https?:|www\.|BRASIL\.|Fonte:|In:|apud|apud )/.test(p) ||
    p.length < 60 && /^[\d\w]/.test(p) && p.includes('.')
}

function formatarTempo(s: number) {
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
  return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}

export default function SimuladoPlayer({ simuladoId, questoes, totalQuestoes }: Props) {
  const router  = useRouter()
  const [idx,   setIdx]      = useState(0)
  const [resps, setResps]    = useState<Record<number, string>>({})
  const [elim,  setElim]     = useState<Record<number, Set<string>>>({})
  const [secs,  setSecs]     = useState(totalQuestoes * 3 * 60) // 3 min/questão
  const [submitting, setSub] = useState(false)
  const [confirmSub, setConf]= useState(false)
  const [erro,  setErro]     = useState('')

  const q = questoes[idx]

  // Timer
  useEffect(() => {
    const t = setInterval(() => setSecs(s => s > 0 ? s - 1 : 0), 1000)
    return () => clearInterval(t)
  }, [])

  // Auto-submit quando timer zera
  useEffect(() => {
    if (secs === 0) submeter()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secs])

  function marcar(letra: string) {
    setResps(prev => {
      const next = { ...prev }
      if (next[q.id] === letra) delete next[q.id]
      else next[q.id] = letra
      return next
    })
  }

  function toggleEliminar(letra: string) {
    setElim(prev => {
      const set = new Set(prev[q.id] ?? [])
      if (set.has(letra)) set.delete(letra)
      else set.add(letra)
      return { ...prev, [q.id]: set }
    })
  }

  const submeter = useCallback(async () => {
    if (submitting) return
    setSub(true)
    setErro('')
    try {
      const res = await fetch('/api/simulado/submeter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulado_id: simuladoId, respostas: resps }),
      })
      const json = await res.json()
      if (!res.ok) { setErro(json.error || 'Erro ao submeter'); setSub(false); return }
      router.push(`/simulado/${simuladoId}/resultado`)
    } catch {
      setErro('Erro de rede. Tente novamente.')
      setSub(false)
    }
  }, [simuladoId, resps, submitting, router])

  const respondidas = Object.keys(resps).length
  const pct = Math.round((respondidas / totalQuestoes) * 100)
  const timerCor = secs < 300 ? 'text-red-400' : secs < 600 ? 'text-amber-400' : 'text-white/60'

  const altElim = elim[q.id] ?? new Set<string>()

  return (
    <main className="anim-fade max-w-3xl mx-auto px-4 sm:px-6 py-6">

      {/* Header fixo */}
      <div className="flex items-center justify-between mb-5 gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <span className="text-sm text-white/50">
            <span className="font-bold text-white">{idx + 1}</span>/{totalQuestoes}
          </span>
          <div className="h-1.5 w-32 rounded-full bg-white/[0.08] overflow-hidden">
            <div className="h-full rounded-full bg-[#D4A853] transition-all" style={{ width: `${(idx+1)/totalQuestoes*100}%` }} />
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Respondidas */}
          <span className="text-[12px] text-white/40">
            <span className="text-emerald-400 font-bold">{respondidas}</span>/{totalQuestoes} respondidas
          </span>
          {/* Timer */}
          <div className={`font-mono text-sm font-bold tabular-nums ${timerCor}`}>
            ⏱ {formatarTempo(secs)}
          </div>
        </div>
      </div>

      {/* Barra de progresso geral */}
      <div className="h-1 rounded-full bg-white/[0.06] overflow-hidden mb-6">
        <div className="h-full rounded-full bg-gradient-to-r from-[#D4A853] to-amber-600 transition-all duration-300" style={{ width: `${pct}%` }} />
      </div>

      {/* Card questão */}
      <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5 sm:p-6 mb-5">

        {/* Meta */}
        <div className="flex items-center justify-between mb-4 text-[11px] text-white/35 uppercase tracking-wider">
          <span>ENEM {q.ano} — Q.{String(q.numero).padStart(2,'0')}</span>
          {q.competencia && <span className="text-[#D4A853]/70">{q.competencia}</span>}
        </div>

        {/* Enunciado */}
        <div className="space-y-3 mb-5">
          {q.enunciado.map((p, i) => {
            const fonte = isFonte(p)
            const isLast = i === q.enunciado.length - 1
            return (
              <p key={i} className={
                fonte
                  ? 'text-[12px] italic text-white/40'
                  : isLast && q.enunciado.length > 1
                    ? 'font-serif text-[15px] leading-relaxed text-white/90 border-l-2 border-[#D4A853]/50 pl-3'
                    : 'font-serif text-[15px] leading-relaxed text-white/85'
              }>
                {p}
              </p>
            )
          })}
          {q.comando && (
            <p className="text-[14px] text-white/80 font-medium mt-1">{q.comando}</p>
          )}
        </div>

        {/* Alternativas */}
        <div className="space-y-2">
          {LETRAS.filter(l => q.alternativas[l]).map(letra => {
            const selecionada  = resps[q.id] === letra
            const eliminada    = altElim.has(letra)
            return (
              <div key={letra} className="group/alt flex items-start gap-2">
                {/* Tesoura */}
                <button
                  onClick={() => toggleEliminar(letra)}
                  className="shrink-0 mt-1 opacity-0 group-hover/alt:opacity-100 transition text-white/25 hover:text-red-400"
                  title="Eliminar alternativa"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
                    <line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/>
                    <line x1="8.12" y1="8.12" x2="12" y2="12"/>
                  </svg>
                </button>

                <button
                  onClick={() => !eliminada && marcar(letra)}
                  className={`flex-1 flex items-start gap-3 rounded-lg border px-3 py-2.5 text-left text-sm transition ${
                    eliminada
                      ? 'opacity-30 cursor-not-allowed border-[#2C2820] bg-transparent line-through'
                      : selecionada
                        ? 'border-[#D4A853] bg-[#D4A853]/12 text-white'
                        : 'border-[#2C2820] bg-transparent text-white/75 hover:border-[#D4A853]/40 hover:bg-white/[0.03]'
                  }`}
                >
                  <span className={`shrink-0 w-6 h-6 rounded-md text-[11px] font-bold flex items-center justify-center transition ${
                    selecionada ? 'bg-[#D4A853] text-[#0E0D0B]' : 'bg-white/[0.07] text-white/50'
                  }`}>
                    {letra}
                  </span>
                  <span className="leading-snug pt-0.5">{q.alternativas[letra]}</span>
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Navegação entre questões */}
      <div className="flex items-center justify-between gap-3 mb-5">
        <button
          onClick={() => setIdx(i => Math.max(0, i - 1))}
          disabled={idx === 0}
          className="px-4 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] disabled:opacity-30 text-sm font-medium transition"
        >
          ← Anterior
        </button>

        {/* Mapa de questões */}
        <div className="flex-1 flex flex-wrap gap-1 justify-center">
          {questoes.map((qx, i) => (
            <button
              key={qx.id}
              onClick={() => setIdx(i)}
              className={`w-6 h-6 rounded text-[10px] font-bold transition ${
                i === idx
                  ? 'bg-[#D4A853] text-[#0E0D0B]'
                  : resps[qx.id]
                    ? 'bg-emerald-500/30 text-emerald-300'
                    : 'bg-white/[0.07] text-white/40 hover:bg-white/[0.12]'
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>

        {idx < questoes.length - 1 ? (
          <button
            onClick={() => setIdx(i => Math.min(questoes.length - 1, i + 1))}
            className="px-4 py-2 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-sm font-medium transition"
          >
            Próxima →
          </button>
        ) : (
          <button
            onClick={() => setConf(true)}
            className="px-4 py-2 rounded-lg bg-[#D4A853] hover:bg-[#B8882A] text-sm font-bold text-[#0E0D0B] transition"
          >
            Finalizar →
          </button>
        )}
      </div>

      {/* Erro */}
      {erro && (
        <div className="rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-sm px-4 py-3 mb-4">
          {erro}
        </div>
      )}

      {/* Modal confirmação */}
      {confirmSub && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-6 max-w-sm w-full">
            <h3 className="text-lg font-bold mb-2">Encerrar simulado?</h3>
            <p className="text-sm text-white/50 mb-1">
              Respondidas: <span className="text-white font-semibold">{respondidas}</span>/{totalQuestoes}
            </p>
            {totalQuestoes - respondidas > 0 && (
              <p className="text-sm text-amber-400 mb-4">
                ⚠️ {totalQuestoes - respondidas} questão(ões) sem resposta.
              </p>
            )}
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setConf(false)}
                className="flex-1 py-2.5 rounded-lg border border-[#2C2820] text-sm font-medium hover:bg-white/[0.05] transition"
              >
                Continuar
              </button>
              <button
                onClick={() => { setConf(false); submeter() }}
                disabled={submitting}
                className="flex-1 py-2.5 rounded-lg bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-50 text-sm font-bold text-white transition"
              >
                {submitting ? 'Enviando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
