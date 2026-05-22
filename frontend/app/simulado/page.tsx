'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'

// Nunca renderizar no servidor — @react-pdf usa APIs do browser
const BaixarPDFSimulado = dynamic(() => import('./BaixarPDFSimulado'), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-[#2C2820] bg-[#1E1B17] p-5 opacity-50">
      <span className="text-3xl">🖨️</span>
      <span className="font-bold text-white/85">Imprimir e resolver</span>
      <span className="text-xs text-white/40">Carregando...</span>
    </div>
  ),
})

const PROVAS = [
  {
    key:       'enem',
    label:     'ENEM',
    icon:      '📝',
    desc:      '2009–2024 · 2.880 questões',
    available: true,
  },
  {
    key:       'exato',
    label:     'EXATO',
    icon:      '🎓',
    desc:      'Em breve',
    available: false,
  },
  {
    key:       'fuvest',
    label:     'Outras',
    icon:      '📚',
    desc:      'Em breve',
    available: false,
  },
]

const AREAS = [
  { key: 'Linguagens, Codigos e suas Tecnologias',    label: 'Linguagens',  icon: '📖', text: 'text-sky-300',     bg: 'bg-sky-500/15',     border: 'border-sky-500/30'     },
  { key: 'Ciencias Humanas e suas Tecnologias',       label: 'Humanas',     icon: '🌍', text: 'text-amber-300',   bg: 'bg-amber-500/15',   border: 'border-amber-500/30'   },
  { key: 'Ciencias da Natureza e suas Tecnologias',   label: 'C. Natureza', icon: '🔬', text: 'text-emerald-300', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  { key: 'Matematica e suas Tecnologias',             label: 'Matemática',  icon: '📐', text: 'text-violet-300',  bg: 'bg-violet-500/15',  border: 'border-violet-500/30'  },
]

const QTDS = [10, 20, 30, 45]
const ANOS = Array.from({ length: 16 }, (_, i) => 2009 + i)

export default function SimuladoConfig() {
  const router = useRouter()

  const [prova,       setProva]      = useState('enem')
  const [area,        setArea]       = useState('')
  const [anoInicio,   setAnoInicio]  = useState(2009)
  const [anoFim,      setAnoFim]     = useState(2024)
  const [quantidade,  setQtd]        = useState(20)
  const [loading,     setLoading]    = useState(false)
  const [erro,        setErro]       = useState('')
  // Após criar: mostra opções de ação
  const [simuladoId,  setSimuladoId] = useState<number | null>(null)

  async function criar() {
    setErro('')
    setLoading(true)
    try {
      const res = await fetch('/api/simulado/criar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          area:       area || undefined,
          ano_inicio: anoInicio,
          ano_fim:    anoFim,
          quantidade,
        }),
      })
      const json = await res.json()
      if (!res.ok) { setErro(json.error || 'Erro ao criar simulado'); setLoading(false); return }
      setSimuladoId(json.simulado_id)
    } catch {
      setErro('Erro de rede. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // ── Tela pós-criação ────────────────────────────────────────────────────────
  if (simuladoId !== null) {
    return (
      <main className="anim-fade max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-8 text-center">
          <div className="text-4xl mb-3">✅</div>
          <h1 className="text-2xl font-extrabold mb-1">Simulado criado!</h1>
          <p className="text-sm text-white/45 mb-8">
            {quantidade} questões · Como deseja fazer?
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
            {/* Responder online */}
            <button
              onClick={() => router.push(`/simulado/${simuladoId}`)}
              className="flex flex-col items-center gap-2 rounded-xl border border-[#D4A853]/40 bg-[#D4A853]/10 hover:bg-[#D4A853]/20 p-5 transition"
            >
              <span className="text-3xl">🖥️</span>
              <span className="font-bold text-amber-200">Responder online</span>
              <span className="text-xs text-white/40">Cronômetro + correção automática</span>
            </button>

            {/* Baixar PDF para impressão — gerado no browser */}
            <BaixarPDFSimulado simuladoId={simuladoId} />
          </div>

          <button
            onClick={() => setSimuladoId(null)}
            className="text-xs text-white/30 hover:text-white/60 transition"
          >
            ← Reconfigurar simulado
          </button>
        </div>
      </main>
    )
  }

  // ── Formulário de configuração ──────────────────────────────────────────────
  return (
    <main className="anim-fade max-w-2xl mx-auto px-4 sm:px-6 py-8">

      {/* Cabeçalho com botão cancelar */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Novo Simulado</h1>
          <p className="text-sm text-white/45 mt-1">Configure e inicie seu simulado personalizado</p>
        </div>
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 border border-[#2C2820] rounded-lg px-3 py-1.5 transition mt-1"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
          </svg>
          Cancelar
        </Link>
      </div>

      {/* Seleção de prova */}
      <section className="mb-7">
        <h2 className="text-[11px] uppercase tracking-wider text-white/45 mb-3">Prova</h2>
        <div className="grid grid-cols-3 gap-2">
          {PROVAS.map(p => (
            <button
              key={p.key}
              onClick={() => p.available && setProva(p.key)}
              disabled={!p.available}
              className={`rounded-xl border p-3 text-left transition ${
                !p.available
                  ? 'border-[#2C2820] bg-[#161411] opacity-40 cursor-not-allowed'
                  : prova === p.key
                  ? 'border-[#D4A853] bg-[#D4A853]/15 text-amber-200'
                  : 'border-[#2C2820] bg-[#161411] text-white/60 hover:border-[#D4A853]/40'
              }`}
            >
              <div className="text-xl mb-1">{p.icon}</div>
              <div className="text-sm font-bold">{p.label}</div>
              <div className="text-[11px] text-white/40 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>
      </section>

      {/* Área */}
      <section className="mb-7">
        <h2 className="text-[11px] uppercase tracking-wider text-white/45 mb-3">Área de Conhecimento</h2>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setArea('')}
            className={`rounded-xl border p-3 text-left text-sm font-medium transition ${
              area === ''
                ? 'border-[#D4A853] bg-[#D4A853]/15 text-amber-200'
                : 'border-[#2C2820] bg-[#161411] text-white/60 hover:border-[#D4A853]/40'
            }`}
          >
            <span className="text-xl mr-2">🎯</span>
            Todas as áreas
          </button>
          {AREAS.map(a => (
            <button
              key={a.key}
              onClick={() => setArea(a.key)}
              className={`rounded-xl border p-3 text-left text-sm font-medium transition ${
                area === a.key
                  ? `${a.border} ${a.bg} ${a.text}`
                  : 'border-[#2C2820] bg-[#161411] text-white/60 hover:border-[#2C2820]/80'
              }`}
            >
              <span className="text-xl mr-2">{a.icon}</span>
              {a.label}
            </button>
          ))}
        </div>
      </section>

      {/* Anos */}
      <section className="mb-7">
        <h2 className="text-[11px] uppercase tracking-wider text-white/45 mb-3">Período</h2>
        <div className="flex gap-3 items-center">
          <div className="flex-1">
            <label className="text-xs text-white/45 mb-1 block">De</label>
            <select
              value={anoInicio}
              onChange={e => setAnoInicio(Number(e.target.value))}
              className="w-full rounded-lg bg-[#161411] border border-[#2C2820] text-white text-sm px-3 py-2 focus:outline-none focus:border-[#D4A853]/60"
            >
              {ANOS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <span className="text-white/30 mt-5">—</span>
          <div className="flex-1">
            <label className="text-xs text-white/45 mb-1 block">Até</label>
            <select
              value={anoFim}
              onChange={e => setAnoFim(Number(e.target.value))}
              className="w-full rounded-lg bg-[#161411] border border-[#2C2820] text-white text-sm px-3 py-2 focus:outline-none focus:border-[#D4A853]/60"
            >
              {ANOS.filter(a => a >= anoInicio).map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        </div>
      </section>

      {/* Quantidade */}
      <section className="mb-8">
        <h2 className="text-[11px] uppercase tracking-wider text-white/45 mb-3">Número de questões</h2>
        <div className="flex gap-2">
          {QTDS.map(q => (
            <button
              key={q}
              onClick={() => setQtd(q)}
              className={`flex-1 rounded-xl border py-3 text-sm font-bold transition ${
                quantidade === q
                  ? 'border-[#D4A853] bg-[#D4A853]/15 text-amber-200'
                  : 'border-[#2C2820] bg-[#161411] text-white/60 hover:border-[#D4A853]/40'
              }`}
            >
              {q}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-white/30 mt-2">
          Tempo sugerido: ~{Math.round(quantidade * 3)} minutos
        </p>
      </section>

      {/* Erro */}
      {erro && (
        <div className="mb-4 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-sm px-4 py-3">
          {erro}
        </div>
      )}

      {/* Botão criar */}
      <button
        onClick={criar}
        disabled={loading || prova !== 'enem'}
        className="w-full py-3.5 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-50 text-[#0E0D0B] font-bold text-sm shadow-lg shadow-[#D4A853]/25 transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Criando simulado...
          </>
        ) : (
          <>
            Criar Simulado
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
            </svg>
          </>
        )}
      </button>
    </main>
  )
}
