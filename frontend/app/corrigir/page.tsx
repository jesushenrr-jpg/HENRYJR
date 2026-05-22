import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import Link             from 'next/link'
import CorrigirFolha    from './CorrigirFolha'

interface Props {
  searchParams: Promise<{ simulado?: string }>
}

export default async function CorrigirPage({ searchParams }: Props) {
  const { simulado: simStr } = await searchParams
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/auth/login')

  // Se simulado_id fornecido, busca os dados
  let sim: { id: number; total_questoes: number } | null = null
  let questaoIds: number[] = []
  let gabarito: Record<number, string> = {}

  if (simStr) {
    const simId = parseInt(simStr, 10)
    if (!isNaN(simId)) {
      const { data: simData } = await supabase
        .from('simulados')
        .select('id, total_questoes')
        .eq('id', simId)
        .eq('usuario_id', user.id)
        .single()

      if (simData) {
        sim = simData

        const { data: resps } = await supabase
          .from('respostas_simulado')
          .select('questao_id, questoes(gabarito)')
          .eq('simulado_id', simId)
          .order('questao_id', { ascending: true })

        if (resps) {
          resps.forEach((r, i) => {
            questaoIds.push(r.questao_id)
            const q = r.questoes as unknown as { gabarito: string | null } | null
            if (q?.gabarito) gabarito[i + 1] = q.gabarito
          })
        }
      }
    }
  }

  // Busca simulados recentes para seleção rápida
  const { data: recentes } = await supabase
    .from('simulados')
    .select('id, tipo, total_questoes, iniciado_em, status')
    .eq('usuario_id', user.id)
    .order('iniciado_em', { ascending: false })
    .limit(5)

  return (
    <main className="anim-fade max-w-2xl mx-auto px-4 sm:px-6 py-8">

      <div className="mb-7">
        <Link href="/simulado" className="text-xs text-white/35 hover:text-white/60 transition mb-3 inline-block">
          ← Simulados
        </Link>
        <h1 className="text-2xl font-extrabold tracking-tight">📷 Corrigir por foto</h1>
        <p className="text-sm text-white/45 mt-1">
          Fotografe sua folha de respostas impressa e receba a correção automática.
        </p>
      </div>

      {/* Seleção de simulado */}
      {!sim && (
        <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-5 mb-6">
          <p className="text-sm font-semibold text-white/70 mb-3">
            Qual simulado deseja corrigir?
          </p>
          {recentes && recentes.length > 0 ? (
            <div className="space-y-2">
              {recentes.map(s => (
                <Link
                  key={s.id}
                  href={`/corrigir?simulado=${s.id}`}
                  className="flex items-center justify-between rounded-xl border border-[#2C2820] hover:border-[#D4A853]/40 bg-[#0E0D0B] px-4 py-3 transition group"
                >
                  <div>
                    <span className="text-sm font-semibold text-white/80">
                      Simulado #{s.id}
                    </span>
                    <span className="text-xs text-white/35 ml-2">
                      {s.total_questoes} questões
                    </span>
                  </div>
                  <span className="text-xs text-[#D4A853] opacity-0 group-hover:opacity-100 transition">
                    Selecionar →
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-white/35 text-center py-4">
              Nenhum simulado criado ainda.{' '}
              <Link href="/simulado" className="text-[#D4A853] hover:text-amber-300 transition">
                Criar simulado
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Formulário de correção */}
      {sim ? (
        <>
          <div className="flex items-center gap-3 mb-5 rounded-xl bg-[#161411] border border-[#2C2820] px-4 py-3">
            <div className="w-8 h-8 rounded-lg bg-[#D4A853]/10 border border-[#D4A853]/20 flex items-center justify-center text-sm">
              📋
            </div>
            <div>
              <p className="text-sm font-semibold text-white/80">Simulado #{sim.id}</p>
              <p className="text-xs text-white/35">{sim.total_questoes} questões · Correção automática</p>
            </div>
            <Link
              href="/corrigir"
              className="ml-auto text-xs text-white/30 hover:text-white/60 transition"
            >
              Trocar
            </Link>
          </div>

          <CorrigirFolha
            simuladoId={sim.id}
            nQuestoes={sim.total_questoes}
            gabarito={gabarito}
            questaoIds={questaoIds}
          />
        </>
      ) : (
        <div className="rounded-xl bg-[#161411] border border-[#2C2820] p-6 text-center text-sm text-white/35">
          Selecione um simulado acima para continuar
        </div>
      )}

      {/* Informação sobre o processo */}
      <div className="mt-8 rounded-xl bg-[#161411] border border-[#2C2820] p-5">
        <p className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wider">Como funciona</p>
        <div className="space-y-3">
          {[
            { n: '1', t: 'Imprima a folha de respostas', d: 'Baixe o PDF do simulado e imprima a folha de respostas (última página).' },
            { n: '2', t: 'Preencha as bolinhas', d: 'Use caneta preta ou azul. Preencha completamente a bolinha da alternativa escolhida.' },
            { n: '3', t: 'Fotografe a folha', d: 'Foto de cima com todos os 4 cantos visíveis e boa iluminação.' },
            { n: '4', t: 'Receba a correção', d: 'O sistema detecta automaticamente as respostas e compara com o gabarito.' },
          ].map(s => (
            <div key={s.n} className="flex gap-3">
              <div className="w-5 h-5 rounded-full bg-[#D4A853]/15 border border-[#D4A853]/25 text-[#D4A853] text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                {s.n}
              </div>
              <div>
                <p className="text-xs font-semibold text-white/70">{s.t}</p>
                <p className="text-[11px] text-white/35 leading-relaxed">{s.d}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

    </main>
  )
}
