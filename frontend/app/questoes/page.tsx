import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import FiltroSidebar from '@/components/FiltroSidebar'
import BuscaIA from '@/components/BuscaIA'
import type { Questao } from '@/lib/types'
import { EVENTO_LABEL } from '@/lib/provas'

interface SearchParams {
  ano?: string
  dia?: string
  area?: string
  competencia?: string
  busca?: string
  ia?: string
  pagina?: string
  fonte?: string
  evento?: string
  turno?: string
  tipo?: string
}

const POR_PAGINA = 12

// Mapeamento de área para ícone/badge
const AREA_INFO: Record<string, { label: string; bg: string; text: string; border: string }> = {
  'Linguagens, Codigos e suas Tecnologias':   { label: 'Linguagens',  bg: 'bg-sky-500/15',     text: 'text-sky-300',     border: 'border-sky-500/30' },
  'Ciencias Humanas e suas Tecnologias':      { label: 'Humanas',     bg: 'bg-amber-500/15',   text: 'text-amber-300',   border: 'border-amber-500/30' },
  'Ciencias da Natureza e suas Tecnologias':  { label: 'C. Natureza', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  'Matematica e suas Tecnologias':            { label: 'Matemática',  bg: 'bg-violet-500/15',  text: 'text-violet-300',  border: 'border-violet-500/30' },
}

const AREAS = Object.keys(AREA_INFO)
const ANOS  = Array.from({ length: 16 }, (_, i) => 2024 - i)

export default async function QuestoesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>
}) {
  const params  = await searchParams
  const supabase = await createClient()

  const fonte       = (params.fonte ?? 'ENEM') as 'ENEM' | 'EXATO'
  const isExato     = fonte === 'EXATO'

  const ano         = params.ano ? parseInt(params.ano) : undefined
  const dia         = params.dia as 'dia1' | 'dia2' | undefined
  const area        = params.area
  const competencia = params.competencia
  const evento      = params.evento
  const turno       = params.turno
  const tipo        = params.tipo as 'PROVA' | 'SIMULADO' | undefined
  const buscaRaw    = params.busca?.trim()
  const isIA        = params.ia === '1'
  // busca pode ser comma-separated (IA) ou termo único (manual)
  const termosBusca = buscaRaw ? buscaRaw.split(',').map(t => t.trim()).filter(Boolean) : []
  const pagina      = params.pagina ? parseInt(params.pagina) : 1
  const offset      = (pagina - 1) * POR_PAGINA

  // Busca respostas do usuário (para badges)
  const { data: { user } } = await supabase.auth.getUser()
  let respostasMapa: Record<string, boolean> = {}
  if (user) {
    const { data: respostas } = await supabase
      .from('questoes_erradas')
      .select('numero, ano, dia, acertou')
      .eq('usuario_id', user.id)
    for (const r of respostas ?? []) {
      respostasMapa[`${r.ano}-${r.dia}-${r.numero}`] = r.acertou
    }
  }

  // Query principal
  let query = supabase
    .from('questoes')
    .select('id, numero, ano, dia, area, competencia, enunciado, gabarito, tem_imagem, anulada, fonte, evento, turno', { count: 'exact' })
    .eq('anulada', false)
    .eq('fonte', fonte)

  // Ordenação por fonte
  if (isExato) {
    query = query.order('numero', { ascending: true })
  } else {
    query = query.order('ano', { ascending: false }).order('numero', { ascending: true })
  }

  query = query.range(offset, offset + POR_PAGINA - 1)

  // Filtros ENEM
  if (!isExato) {
    if (ano)         query = query.eq('ano', ano)
    if (dia)         query = query.eq('dia', dia)
    if (competencia) query = query.eq('competencia', competencia)
  }

  // Filtros EXATO
  if (isExato) {
    if (evento) query = query.eq('evento', evento)
    if (turno)  query = query.eq('turno', turno)
  }

  // Filtro de área (ambos)
  if (area) query = query.eq('area', area)

  // Filtro de tipo (PROVA | SIMULADO)
  if (tipo) query = query.eq('tipo', tipo)

  if (termosBusca.length > 0) {
    const orFilter = termosBusca
      .flatMap(t => [`enunciado.ilike.%${t}%`, `comando.ilike.%${t}%`])
      .join(',')
    query = query.or(orFilter)
  }

  const { data: questoes, count } = await query
  const total        = count ?? 0
  const totalPaginas = Math.ceil(total / POR_PAGINA)

  // Monta params para paginação (mantém filtros)
  function paginaUrl(p: number) {
    const sp = new URLSearchParams()
    sp.set('fonte', fonte)
    if (!isExato) {
      if (ano)         sp.set('ano', String(ano))
      if (dia)         sp.set('dia', dia)
      if (competencia) sp.set('competencia', competencia)
    } else {
      if (evento) sp.set('evento', evento)
      if (turno)  sp.set('turno', turno)
    }
    if (area)          sp.set('area', area)
    if (buscaRaw)      sp.set('busca', buscaRaw)
    if (isIA)          sp.set('ia', '1')
    if (tipo)          sp.set('tipo', tipo)
    if (p > 1)         sp.set('pagina', String(p))
    return `/questoes?${sp}`
  }

  // Cor do badge de paginação ativa
  const paginaActiveBg = isExato ? 'bg-[#F59E0B] shadow-[#F59E0B]/20' : 'bg-[#3B82F6] shadow-[#3B82F6]/20'
  const hoverBorderColor = isExato ? 'hover:border-amber-500/30' : 'hover:border-blue-500/30'

  return (
    <main className="anim-fade max-w-6xl mx-auto px-4 sm:px-6 py-6">

      {/* Busca IA */}
      <BuscaIA />

      {/* Layout: sidebar + lista */}
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-5 mt-5">

        {/* Sidebar filtros */}
        <aside>
          <FiltroSidebar
            anos={ANOS}
            areas={AREAS}
            anoAtivo={ano}
            diaAtivo={dia}
            areaAtiva={area}
            competenciaAtiva={competencia}
            fonteAtiva={fonte}
            eventoAtivo={evento}
            turnoAtivo={turno}
            tipoAtivo={tipo}
          />
        </aside>

        {/* Lista de questões */}
        <section>

          {/* Busca IA ativa — banner */}
          {isIA && termosBusca.length > 0 && (
            <div className="mb-3 flex flex-wrap items-center gap-2 px-3 py-2.5 rounded-xl bg-[#D4A853]/8 border border-[#D4A853]/20">
              <div className="flex items-center gap-1.5 text-[11px] text-[#D4A853] font-semibold shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/>
                </svg>
                Busca IA:
              </div>
              {termosBusca.map(t => (
                <span key={t} className="px-2 py-0.5 rounded-md bg-[#D4A853]/15 border border-[#D4A853]/25 text-[#D4A853] text-[11px]">
                  {t}
                </span>
              ))}
              <Link href={`/questoes?fonte=${fonte}`} className="ml-auto text-[10px] text-[#635D56] hover:text-rose-400 transition">
                ✕ limpar
              </Link>
            </div>
          )}

          {/* Busca textual manual */}
          {!isIA && (
            <form method="get" action="/questoes" className="relative mb-4">
              <input type="hidden" name="fonte" value={fonte} />
              {!isExato && ano         && <input type="hidden" name="ano"         value={ano} />}
              {!isExato && dia         && <input type="hidden" name="dia"         value={dia} />}
              {!isExato && competencia && <input type="hidden" name="competencia" value={competencia} />}
              {isExato  && evento      && <input type="hidden" name="evento"      value={evento} />}
              {isExato  && turno       && <input type="hidden" name="turno"       value={turno} />}
              {area && <input type="hidden" name="area" value={area} />}
              {tipo && <input type="hidden" name="tipo" value={tipo} />}
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="absolute left-3 top-1/2 -translate-y-1/2 text-[#635D56] pointer-events-none">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              <input
                type="text"
                name="busca"
                defaultValue={buscaRaw}
                placeholder="Buscar por palavra-chave no enunciado…"
                className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-[#161411] border border-[#2C2820] focus:border-[#4A3F2F] outline-none text-[13px] text-[#F2EDE4] placeholder:text-[#635D56] transition"
              />
            </form>
          )}

          {/* Contador + limpar */}
          <div className="flex items-center justify-between mb-3">
            <div className="text-[12px] text-[#9E9589]">
              <span className="text-[#F2EDE4] font-semibold">{total.toLocaleString('pt-BR')}</span>{' '}
              {total === 1 ? 'questão' : 'questões'}
              {isExato && <span className="ml-1.5 px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20">EXATO</span>}
              {!isExato && <span className="ml-1.5 px-1.5 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20">ENEM</span>}
            </div>
            {!isIA && (ano || dia || area || competencia || buscaRaw || evento || turno || tipo) && (
              <Link href={`/questoes?fonte=${fonte}`} className="text-[11px] text-[#635D56] hover:text-[#F2EDE4] transition">
                limpar filtros
              </Link>
            )}
          </div>

          {/* Cards de questão (preview) */}
          <div className="space-y-3">
            {(questoes?.length ?? 0) === 0 && (
              <div className="rounded-xl bg-[#161411] border border-[#2C2820] p-10 text-center text-[#635D56] text-sm">
                Nenhuma questão encontrada com esses filtros.
              </div>
            )}

            {questoes?.map((q: any) => {
              const info = AREA_INFO[q.area]
              const chave = `${q.ano}-${q.dia}-${q.numero}`
              const acertou = respostasMapa[chave]
              const respondeu = chave in respostasMapa
              const isQExato = q.fonte === 'EXATO'

              return (
                <Link
                  key={q.id}
                  href={`/questoes/${q.id}`}
                  className={`group block rounded-xl bg-[#161411] border border-[#2C2820] ${hoverBorderColor} p-4 sm:p-5 transition anim-fade`}
                >
                  {/* Header do card */}
                  <div className="flex items-center gap-2 mb-2.5 flex-wrap">
                    {/* Badge fonte */}
                    {isQExato ? (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/30">
                        EXATO
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-blue-500/15 text-blue-300 border border-blue-500/30">
                        ENEM
                      </span>
                    )}

                    {/* Info contextual */}
                    {isQExato ? (
                      <>
                        {q.evento && (
                          <span className="text-[11px] text-[#9E9589]">
                            {EVENTO_LABEL[q.evento] ?? q.evento}
                          </span>
                        )}
                        {q.turno && (
                          <>
                            <span className="text-[#2C2820]">·</span>
                            <span className="text-[11px] text-[#9E9589]">
                              {q.turno === 'MANHA' ? 'Manhã' : 'Tarde'}
                            </span>
                          </>
                        )}
                        <span className="text-[#2C2820]">·</span>
                        <span className="text-[11px] text-[#9E9589]">Q. {q.numero}</span>
                      </>
                    ) : (
                      <>
                        <span className="text-[11px] text-[#9E9589]">
                          {q.ano} · {q.dia === 'dia1' ? '1º dia' : '2º dia'}
                        </span>
                        <span className="text-[#2C2820]">·</span>
                        <span className="text-[11px] text-[#9E9589]">Q. {q.numero}</span>
                      </>
                    )}

                    {/* Área */}
                    {info && (
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wider ${info.bg} ${info.text}`}>
                        {info.label}
                      </span>
                    )}
                    {q.competencia && (
                      <span className="text-[11px] text-[#635D56] font-mono">{q.competencia}</span>
                    )}

                    {/* Badge resposta anterior */}
                    {respondeu && (
                      <span className={`ml-auto px-2 py-0.5 rounded text-[10px] font-semibold ${
                        acertou ? 'bg-emerald-500/15 text-emerald-300' : 'bg-rose-500/15 text-rose-300'
                      }`}>
                        {acertou ? '✓ Acertou' : '✗ Errou'}
                      </span>
                    )}
                  </div>

                  {/* Preview do enunciado */}
                  <p className="font-serif text-[14.5px] leading-relaxed text-[#F2EDE4]/80 line-clamp-2 mb-3">
                    {Array.isArray(q.enunciado) ? q.enunciado[0] : q.enunciado}
                  </p>

                  <div className="flex items-center justify-between text-[12px]">
                    <span className="text-[#635D56]">5 alternativas · clique para responder</span>
                    <span className={`${isQExato ? 'text-amber-400' : 'text-blue-400'} group-hover:translate-x-1 transition`}>→</span>
                  </div>
                </Link>
              )
            })}
          </div>

          {/* Paginação */}
          {totalPaginas > 1 && (
            <div className="flex justify-center gap-1.5 mt-8 flex-wrap">
              {pagina > 1 && (
                <Link href={paginaUrl(pagina - 1)} className="w-9 h-9 flex items-center justify-center rounded-lg text-sm bg-[#1E1B17] border border-[#2C2820] text-[#9E9589] hover:bg-[#2C2820] transition">
                  ‹
                </Link>
              )}
              {Array.from({ length: Math.min(totalPaginas, 9) }, (_, i) => {
                const half = 4
                let start = Math.max(1, pagina - half)
                const end  = Math.min(totalPaginas, start + 8)
                start = Math.max(1, end - 8)
                const p = start + i
                if (p > totalPaginas) return null
                return (
                  <Link
                    key={p}
                    href={paginaUrl(p)}
                    className={`w-9 h-9 flex items-center justify-center rounded-lg text-sm font-semibold transition ${
                      p === pagina
                        ? `${paginaActiveBg} text-white shadow-lg`
                        : 'bg-[#1E1B17] border border-[#2C2820] text-[#9E9589] hover:bg-[#2C2820]'
                    }`}
                  >
                    {p}
                  </Link>
                )
              })}
              {pagina < totalPaginas && (
                <Link href={paginaUrl(pagina + 1)} className="w-9 h-9 flex items-center justify-center rounded-lg text-sm bg-[#1E1B17] border border-[#2C2820] text-[#9E9589] hover:bg-[#2C2820] transition">
                  ›
                </Link>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
