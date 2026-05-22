import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import Link             from 'next/link'

interface Props { params: Promise<{ id: string }> }

const AREAS: Record<string, { label: string; icon: string; text: string }> = {
  'Linguagens, Codigos e suas Tecnologias':    { label: 'Linguagens',  icon: '📖', text: 'text-sky-300'    },
  'Ciencias Humanas e suas Tecnologias':       { label: 'Humanas',     icon: '🌍', text: 'text-amber-300'  },
  'Ciencias da Natureza e suas Tecnologias':   { label: 'C. Natureza', icon: '🔬', text: 'text-emerald-300' },
  'Matematica e suas Tecnologias':             { label: 'Matemática',  icon: '📐', text: 'text-violet-300'  },
}

function medalha(pct: number) {
  if (pct >= 90) return { emoji: '🥇', label: 'Excelente!' }
  if (pct >= 70) return { emoji: '🥈', label: 'Muito bom!' }
  if (pct >= 50) return { emoji: '🥉', label: 'Bom!' }
  return { emoji: '📚', label: 'Continue estudando!' }
}

export default async function ResultadoPage({ params }: Props) {
  const { id }   = await params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login')

  const { data: sim } = await supabase
    .from('simulados')
    .select('*')
    .eq('id', id)
    .eq('usuario_id', user.id)
    .single()

  if (!sim) redirect('/simulado')
  if (sim.status !== 'concluido') redirect(`/simulado/${id}`)

  // Busca respostas com dados da questão
  const { data: resps } = await supabase
    .from('respostas_simulado')
    .select('questao_id, resposta, correta, questoes(numero, ano, dia, area, gabarito, competencia, enunciado, comando)')
    .eq('simulado_id', id)

  const total   = resps?.length ?? 0
  const acertos = resps?.filter(r => r.correta).length ?? 0
  const pct     = total > 0 ? Math.round((acertos / total) * 100) : 0
  const med     = medalha(pct)

  // Agrupa por área
  const porArea: Record<string, { acertos: number; total: number }> = {}
  for (const r of resps ?? []) {
    const q = (r.questoes as unknown) as { area: string } | null
    if (!q) continue
    if (!porArea[q.area]) porArea[q.area] = { acertos: 0, total: 0 }
    porArea[q.area].total++
    if (r.correta) porArea[q.area].acertos++
  }

  // Questões erradas
  const erradas = (resps ?? []).filter(r => !r.correta)
  const duracao = sim.concluido_em
    ? Math.round((new Date(sim.concluido_em).getTime() - new Date(sim.iniciado_em).getTime()) / 60000)
    : null

  return (
    <main className="anim-fade max-w-3xl mx-auto px-4 sm:px-6 py-8">

      {/* Hero resultado */}
      <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-6 sm:p-8 text-center mb-6">
        <div className="text-5xl mb-3">{med.emoji}</div>
        <h1 className="text-2xl font-extrabold mb-1">{med.label}</h1>
        <div className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-amber-300 to-[#D4A853] bg-clip-text text-transparent mb-1">
          {pct}%
        </div>
        <div className="text-white/45 text-sm mb-4">
          {acertos} acertos de {total} questões
          {duracao && <> · {duracao} min</>}
        </div>

        {/* Barra de acerto */}
        <div className="h-2 rounded-full bg-white/[0.08] overflow-hidden max-w-xs mx-auto">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#D4A853] to-amber-600 transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Por área */}
      {Object.keys(porArea).length > 0 && (
        <>
          <h2 className="text-lg font-bold mb-3">Desempenho por área</h2>
          <div className="space-y-2 mb-7">
            {Object.entries(porArea).map(([area, s]) => {
              const info = AREAS[area] ?? { label: area, icon: '📚', text: 'text-white' }
              const ap   = Math.round((s.acertos / s.total) * 100)
              return (
                <div key={area} className="rounded-xl bg-[#161411] border border-[#2C2820] px-4 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <span>{info.icon}</span>
                      <span className={info.text}>{info.label}</span>
                    </div>
                    <span className={`text-lg font-extrabold ${info.text}`}>{ap}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#D4A853] to-amber-500" style={{ width: `${ap}%` }} />
                  </div>
                  <div className="text-[11px] text-white/35 mt-1">{s.acertos}/{s.total} acertos</div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Questões erradas */}
      {erradas.length > 0 && (
        <>
          <h2 className="text-lg font-bold mb-3">
            Questões erradas <span className="text-red-400">({erradas.length})</span>
          </h2>
          <div className="space-y-2 mb-7">
            {erradas.map(r => {
              const q = (r.questoes as unknown) as {
                numero: number; ano: number; area: string;
                gabarito: string; competencia: string | null; enunciado: string[]
              } | null
              if (!q) return null
              const info = AREAS[q.area] ?? { label: q.area, icon: '📚', text: 'text-white' }
              return (
                <div key={r.questao_id} className="rounded-xl bg-[#161411] border border-[#2C2820] px-4 py-3 flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-red-500/15 border border-red-500/30 flex items-center justify-center shrink-0 mt-0.5">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-red-400">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-0.5">
                      <span className="text-xs text-white/50">ENEM {q.ano} — Q.{q.numero}</span>
                      {q.competencia && <span className="text-[10px] text-[#D4A853]/70">{q.competencia}</span>}
                      <span className={`text-[10px] ${info.text}`}>{info.icon} {info.label}</span>
                    </div>
                    <p className="text-[13px] text-white/60 line-clamp-2 font-serif">{q.enunciado?.[0]}</p>
                    <div className="flex items-center gap-3 mt-1 text-[11px]">
                      {r.resposta && (
                        <span className="text-red-400">Sua resp.: <strong>{r.resposta}</strong></span>
                      )}
                      <span className="text-emerald-400">Gabarito: <strong>{q.gabarito}</strong></span>
                    </div>
                  </div>
                  <Link
                    href={`/questoes/${r.questao_id}`}
                    className="shrink-0 text-[11px] text-[#D4A853] hover:text-amber-300 transition"
                  >
                    Ver →
                  </Link>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Ações */}
      <div className="flex flex-wrap gap-3">
        <Link
          href="/simulado"
          className="px-5 py-2.5 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] font-semibold text-sm transition"
        >
          Novo simulado
        </Link>
        <Link
          href="/tira-teima"
          className="px-5 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/85 font-semibold text-sm transition"
        >
          📓 Tira Teima
        </Link>
        <Link
          href="/progresso"
          className="px-5 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/85 font-semibold text-sm transition"
        >
          📊 Meu progresso
        </Link>
        <a
          href={`/api/pdf/simulado/${id}`}
          target="_blank"
          rel="noreferrer"
          className="px-5 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/85 font-semibold text-sm transition flex items-center gap-2"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <polyline points="9 15 12 18 15 15"/>
          </svg>
          Baixar PDF
        </a>
        <Link
          href={`/corrigir?simulado=${id}`}
          className="px-5 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/85 font-semibold text-sm transition flex items-center gap-2"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
            <circle cx="12" cy="13" r="4"/>
          </svg>
          Corrigir por foto
        </Link>
      </div>
    </main>
  )
}
