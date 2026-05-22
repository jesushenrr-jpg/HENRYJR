import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import Link             from 'next/link'

const AREAS = [
  { nome: 'Linguagens, Codigos e suas Tecnologias',    label: 'Linguagens',  icon: '📖', text: 'text-sky-300',     bg: 'bg-sky-500/15',     border: 'border-sky-500/30'     },
  { nome: 'Ciencias Humanas e suas Tecnologias',       label: 'Humanas',     icon: '🌍', text: 'text-amber-300',   bg: 'bg-amber-500/15',   border: 'border-amber-500/30'   },
  { nome: 'Ciencias da Natureza e suas Tecnologias',   label: 'C. Natureza', icon: '🔬', text: 'text-emerald-300', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  { nome: 'Matematica e suas Tecnologias',             label: 'Matemática',  icon: '📐', text: 'text-violet-300',  bg: 'bg-violet-500/15',  border: 'border-violet-500/30'  },
]

export default async function TiraTeima() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login')

  // Busca questões erradas (acertou = false ou null) com JOIN nas questões
  // Se a migração ainda não foi feita, cai no fallback com questao_id
  type RowNovo = {
    questao_id: number; acertou: boolean | null; area: string | null;
    ano: number | null; numero: number | null; respondido_em: string | null;
    questoes: { id: number; ano: number; numero: number; dia: string; area: string; competencia: string | null; enunciado: string[] } | null
  }

  const { data: erradas, error } = await supabase
    .from('questoes_erradas')
    .select(`
      questao_id, acertou, area, ano, numero, respondido_em,
      questoes ( id, ano, numero, dia, area, competencia, enunciado )
    `)
    .eq('usuario_id', user.id)
    .order('respondido_em', { ascending: false })

  // Detecta se migração foi feita
  const migracao = !error || error.code !== '42703'

  // Filtra apenas erradas (acertou = false, ou all se coluna não existe)
  let lista: RowNovo[] = []
  if (!error && erradas) {
    lista = (erradas as unknown as RowNovo[]).filter(r => r.acertou === false || r.acertou === null)
  }

  // Agrupa por área
  const porArea: Record<string, RowNovo[]> = {}
  for (const r of lista) {
    const area = r.area || r.questoes?.area || 'Outras'
    if (!porArea[area]) porArea[area] = []
    porArea[area].push(r)
  }

  const total = lista.length
  const totalPorArea = AREAS.map(a => ({
    ...a,
    itens: porArea[a.nome] ?? [],
  })).filter(a => a.itens.length > 0)

  return (
    <main className="anim-fade max-w-4xl mx-auto px-4 sm:px-6 py-8">

      <div className="mb-7">
        <h1 className="text-3xl font-extrabold tracking-tight">📓 Tira Teima</h1>
        <p className="text-sm text-white/45 mt-1">
          Questões que você errou — pratique até zerar
        </p>
      </div>

      {/* Aviso se migração pendente */}
      {!migracao && (
        <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm px-4 py-4 mb-6">
          <p className="font-semibold mb-1">⚠️ Migração pendente</p>
          <p className="text-amber-200/70 text-xs">
            Execute o arquivo <code className="bg-amber-900/30 px-1 rounded">migracao_questoes_erradas.sql</code> no{' '}
            <a href="https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh/sql/new" target="_blank" rel="noopener noreferrer" className="underline">
              Supabase SQL Editor
            </a>{' '}
            para ativar o rastreamento de erros.
          </p>
        </div>
      )}

      {total === 0 ? (
        /* Empty state */
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-8 text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h3 className="font-bold text-lg mb-1">Nenhum erro pendente!</h3>
          <p className="text-sm text-white/45 mb-5">
            {migracao
              ? 'Você zerou o Tira Teima. Continue praticando para manter o nível!'
              : 'Responda algumas questões para ver seus erros aqui.'}
          </p>
          <Link
            href="/questoes"
            className="inline-block px-5 py-2.5 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] font-semibold text-sm transition"
          >
            Praticar questões
          </Link>
        </div>
      ) : (
        <>
          {/* Resumo */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-7">
            <div className="rounded-xl bg-[#161411] border border-red-500/20 p-4 text-center">
              <div className="text-3xl font-extrabold text-red-400">{total}</div>
              <div className="text-[10px] uppercase tracking-wider text-white/35 mt-1">Para revisar</div>
            </div>
            {totalPorArea.slice(0, 3).map(a => (
              <div key={a.nome} className={`rounded-xl bg-[#161411] border ${a.border} p-4 text-center`}>
                <div className={`text-2xl font-extrabold ${a.text}`}>{a.itens.length}</div>
                <div className="text-[10px] uppercase tracking-wider text-white/35 mt-1">{a.icon} {a.label}</div>
              </div>
            ))}
          </div>

          {/* Botão iniciar + baixar PDF */}
          <div className="mb-7 flex flex-wrap gap-3">
            <Link
              href={`/simulado?modo=tira-teima`}
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] font-semibold text-sm shadow-lg shadow-[#D4A853]/25 transition"
            >
              📓 Iniciar sessão Tira Teima
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </Link>
            <a
              href="/api/pdf/tira-teima?gabarito=true"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/80 font-semibold text-sm transition"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <polyline points="9 15 12 18 15 15"/>
              </svg>
              Baixar PDF imprimível
            </a>
          </div>

          {/* Por área */}
          {totalPorArea.map(a => (
            <div key={a.nome} className="mb-8">
              <div className={`flex items-center gap-2 mb-3`}>
                <span className="text-xl">{a.icon}</span>
                <h2 className={`text-base font-bold ${a.text}`}>{a.label}</h2>
                <span className={`text-xs px-2 py-0.5 rounded-full ${a.bg} ${a.border} border ${a.text}`}>
                  {a.itens.length}
                </span>
              </div>

              <div className="space-y-2">
                {a.itens.map(r => {
                  const q = r.questoes
                  const ano     = q?.ano    ?? r.ano    ?? '—'
                  const numero  = q?.numero ?? r.numero ?? '—'
                  const preview = q?.enunciado?.[0]?.slice(0, 120) ?? ''
                  const comp    = q?.competencia

                  return (
                    <Link
                      key={r.questao_id}
                      href={`/questoes/${r.questao_id}`}
                      className="flex items-start gap-3 rounded-xl bg-[#161411] border border-[#2C2820] px-4 py-3 hover:border-red-500/30 transition group"
                    >
                      <div className="w-7 h-7 rounded-lg bg-red-500/12 border border-red-500/25 flex items-center justify-center shrink-0 mt-0.5">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-red-400">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-0.5">
                          <span className="text-[11px] text-white/45">ENEM {ano} — Q.{numero}</span>
                          {comp && <span className="text-[10px] text-[#D4A853]/60">{comp}</span>}
                        </div>
                        {preview && (
                          <p className="text-[13px] text-white/55 font-serif line-clamp-2 leading-snug">{preview}</p>
                        )}
                      </div>
                      <span className={`shrink-0 text-[11px] ${a.text} opacity-0 group-hover:opacity-100 transition`}>Ver →</span>
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </>
      )}
    </main>
  )
}
