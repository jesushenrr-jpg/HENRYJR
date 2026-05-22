import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'

const AREAS = [
  {
    nome: 'Linguagens, Codigos e suas Tecnologias',
    label: 'Linguagens',
    key: 'LCT',
    icone: '📖',
    bg: 'bg-sky-500/15',
    text: 'text-sky-300',
    border: 'border-sky-500/30',
    dot: 'bg-sky-400',
    bar: 'from-sky-500 to-sky-400',
    barSolid: 'bg-sky-400',
  },
  {
    nome: 'Ciencias Humanas e suas Tecnologias',
    label: 'Humanas',
    key: 'CHT',
    icone: '🌍',
    bg: 'bg-amber-500/15',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    dot: 'bg-amber-400',
    bar: 'from-amber-500 to-amber-400',
    barSolid: 'bg-amber-400',
  },
  {
    nome: 'Ciencias da Natureza e suas Tecnologias',
    label: 'C. Natureza',
    key: 'CNT',
    icone: '🔬',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-300',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
    bar: 'from-emerald-500 to-emerald-400',
    barSolid: 'bg-emerald-400',
  },
  {
    nome: 'Matematica e suas Tecnologias',
    label: 'Matemática',
    key: 'MAT',
    icone: '📐',
    bg: 'bg-violet-500/15',
    text: 'text-violet-300',
    border: 'border-violet-500/30',
    dot: 'bg-violet-400',
    bar: 'from-violet-500 to-violet-400',
    barSolid: 'bg-violet-400',
  },
]

function corPct(pct: number) {
  if (pct >= 70) return 'text-emerald-400'
  if (pct >= 50) return 'text-[#D4A853]'
  return 'text-red-400'
}

export default async function ProgressoPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')

  // Busca respostas do usuário + total real por área/competência em paralelo
  const [{ data: respostas }, { data: totaisQuestoes }] = await Promise.all([
    supabase
      .from('questoes_erradas')
      .select('area, competencia, acertou')
      .eq('usuario_id', user.id),
    supabase
      .from('questoes')
      .select('area, competencia')
      .eq('anulada', false),
  ])

  // ── Stats por área ───────────────────────────────────────────────────────
  type Stats = { total: number; acertos: number }
  const stats: Record<string, Stats> = {}
  for (const r of respostas ?? []) {
    if (!stats[r.area]) stats[r.area] = { total: 0, acertos: 0 }
    stats[r.area].total++
    if (r.acertou) stats[r.area].acertos++
  }

  // ── Stats por competência ────────────────────────────────────────────────
  type StatsComp = { total: number; acertos: number; area: string }
  const statsPorComp: Record<string, StatsComp> = {}
  for (const r of respostas ?? []) {
    if (!r.competencia) continue
    if (!statsPorComp[r.competencia]) statsPorComp[r.competencia] = { total: 0, acertos: 0, area: r.area }
    statsPorComp[r.competencia].total++
    if (r.acertou) statsPorComp[r.competencia].acertos++
  }

  // Total real de questões por área e por competência
  const totalRealPorArea: Record<string, number> = {}
  const totalRealPorComp: Record<string, number> = {}
  for (const r of totaisQuestoes ?? []) {
    totalRealPorArea[r.area] = (totalRealPorArea[r.area] ?? 0) + 1
    if (r.competencia) {
      if (!totalRealPorComp[r.competencia]) totalRealPorComp[r.competencia] = 0
      totalRealPorComp[r.competencia]++
    }
  }

  // Agrupa competências praticadas por área (ordenadas numericamente)
  const compPorArea: Record<string, string[]> = {}
  for (const [comp, s] of Object.entries(statsPorComp)) {
    if (!compPorArea[s.area]) compPorArea[s.area] = []
    compPorArea[s.area].push(comp)
  }
  for (const k of Object.keys(compPorArea)) {
    compPorArea[k].sort((a, b) => {
      const na = parseInt(a.replace(/\D/g, ''), 10)
      const nb = parseInt(b.replace(/\D/g, ''), 10)
      return na - nb
    })
  }

  const totalGeral   = Object.values(stats).reduce((s, a) => s + a.total, 0)
  const acertosGeral = Object.values(stats).reduce((s, a) => s + a.acertos, 0)
  const pctGeral     = totalGeral > 0 ? Math.round((acertosGeral / totalGeral) * 100) : 0

  // Streak de acertos seguidos
  const lista = respostas ?? []
  let streak = 0
  for (let i = lista.length - 1; i >= 0; i--) {
    if (lista[i].acertou) streak++
    else break
  }

  const totalCompPraticadas = Object.keys(statsPorComp).length

  return (
    <main className="anim-fade max-w-5xl mx-auto px-4 sm:px-6 py-8">

      <div className="mb-7">
        <h1 className="text-3xl font-extrabold tracking-tight">Seu progresso</h1>
        <p className="text-sm text-white/45 mt-1">
          Olá, <span className="text-white/70">{user.email?.split('@')[0]}</span> — acompanhe seu desempenho geral e por área.
        </p>
      </div>

      {/* Cards gerais */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">

        {/* Aproveitamento */}
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5">
          <div className="text-[11px] uppercase tracking-wider text-white/45 mb-2">Aproveitamento geral</div>
          <div className="flex items-baseline gap-2 mb-3">
            <div className="text-4xl font-extrabold tracking-tight">{pctGeral}%</div>
            <div className="text-[12px] text-white/45">{acertosGeral}/{totalGeral}</div>
          </div>
          <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#D4A853] to-amber-600 transition-all duration-700"
              style={{ width: `${pctGeral}%` }}
            />
          </div>
        </div>

        {/* Questões respondidas */}
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5">
          <div className="text-[11px] uppercase tracking-wider text-white/45 mb-2">Questões respondidas</div>
          <div className="text-4xl font-extrabold tracking-tight mb-1">{totalGeral}</div>
          <div className="text-[12px] text-white/45">de 2.890 disponíveis</div>
          <div className="mt-3 flex gap-4 text-xs">
            <span className="text-emerald-400 font-semibold">{acertosGeral} acertos</span>
            <span className="text-red-400 font-semibold">{totalGeral - acertosGeral} erros</span>
          </div>
        </div>

        {/* Streak */}
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5">
          <div className="text-[11px] uppercase tracking-wider text-white/45 mb-2 flex items-center gap-1.5">
            🔥 Acertos seguidos
          </div>
          <div className="text-4xl font-extrabold tracking-tight mb-1">{streak}</div>
          <div className="text-[12px] text-white/45">sequência atual</div>
        </div>
      </div>

      {/* Por área */}
      <h2 className="text-xl font-bold tracking-tight mb-4">Desempenho por área</h2>
      <div className="space-y-3 mb-10">
        {AREAS.map(a => {
          const s = stats[a.nome]
          const pct       = s && s.total > 0 ? Math.round((s.acertos / s.total) * 100) : 0
          const totalReal = totalRealPorArea[a.nome] ?? 1
          const cobertura = s ? Math.min(100, Math.round((s.total / totalReal) * 100)) : 0

          return (
            <div key={a.key} className="rounded-xl bg-[#161411] border border-[#2C2820] p-4 sm:p-5">
              <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg ${a.bg} ${a.text} border ${a.border} flex items-center justify-center text-base`}>
                    {a.icone}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{a.label}</div>
                    <div className="text-[11px] text-white/40">
                      {s?.total ?? 0} respondidas · {s?.acertos ?? 0} acertos
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-extrabold ${a.text}`}>{pct}%</div>
                  <div className="text-[10px] text-white/35 uppercase tracking-wider">aproveitamento</div>
                </div>
              </div>

              {/* Dual progress bars */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-[10px] text-white/40 uppercase tracking-wider mb-1">
                    <span>Acerto</span><span>{pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${a.bar} transition-all duration-700`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-[10px] text-white/40 uppercase tracking-wider mb-1">
                    <span>Cobertura</span><span>{cobertura}%</span>
                  </div>
                  <div className="h-1 rounded-full bg-white/[0.05] overflow-hidden">
                    <div
                      className={`h-full rounded-full opacity-60 ${a.dot} transition-all duration-700`}
                      style={{ width: `${cobertura}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Por competência H01–H30 */}
      {totalCompPraticadas > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold tracking-tight">Desempenho por competência</h2>
            <span className="text-[11px] text-white/40 bg-white/[0.05] rounded-full px-3 py-1 border border-[#2C2820]">
              {totalCompPraticadas}/30 competências
            </span>
          </div>

          <div className="space-y-6 mb-10">
            {AREAS.map(a => {
              const comps = compPorArea[a.nome] ?? []
              if (comps.length === 0) return null

              return (
                <div key={a.key} className="rounded-xl bg-[#161411] border border-[#2C2820] overflow-hidden">
                  {/* Cabeçalho da área */}
                  <div className={`flex items-center gap-2.5 px-4 py-3 border-b border-[#2C2820] ${a.bg}`}>
                    <span className="text-base">{a.icone}</span>
                    <span className={`font-semibold text-sm ${a.text}`}>{a.label}</span>
                    <span className="text-[11px] text-white/35 ml-auto">{comps.length} competência{comps.length !== 1 ? 's' : ''} praticada{comps.length !== 1 ? 's' : ''}</span>
                  </div>

                  {/* Grid de competências */}
                  <div className="divide-y divide-[#2C2820]/60">
                    {comps.map(comp => {
                      const s     = statsPorComp[comp]
                      const pct   = s.total > 0 ? Math.round((s.acertos / s.total) * 100) : 0
                      const total = totalRealPorComp[comp] ?? 0

                      return (
                        <div key={comp} className="flex items-center gap-3 px-4 py-3 hover:bg-white/[0.02] transition-colors">
                          {/* Badge da competência */}
                          <div className={`shrink-0 w-12 text-center text-[11px] font-bold rounded-md px-1.5 py-0.5 ${a.bg} ${a.text} border ${a.border}`}>
                            {comp}
                          </div>

                          {/* Barra de progresso */}
                          <div className="flex-1 min-w-0">
                            <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                              <div
                                className={`h-full rounded-full ${a.barSolid} transition-all duration-700`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>

                          {/* Stats */}
                          <div className="shrink-0 flex items-center gap-3 text-right">
                            <span className="text-[11px] text-white/35 hidden sm:block">
                              {s.acertos}/{s.total}
                            </span>
                            <span className={`text-sm font-extrabold w-10 text-right ${corPct(pct)}`}>
                              {pct}%
                            </span>
                          </div>

                          {/* Total disponível */}
                          {total > 0 && (
                            <div className="shrink-0 text-[10px] text-white/25 hidden md:block w-16 text-right">
                              {total} questões
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Empty state */}
      {totalGeral === 0 && (
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-8 text-center mt-4">
          <div className="text-4xl mb-3">📊</div>
          <h3 className="font-semibold text-white mb-1">Comece a praticar!</h3>
          <p className="text-sm text-white/45 mb-4">Resolva questões para ver seu progresso aqui.</p>
          <Link
            href="/questoes"
            className="inline-block px-4 py-2 rounded-lg bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] text-[13px] font-semibold transition"
          >
            Ir para questões
          </Link>
        </div>
      )}

    </main>
  )
}
