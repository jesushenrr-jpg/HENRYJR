import { createClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import CardQuestao from '@/components/CardQuestao'
import type { Questao } from '@/lib/types'

interface Props {
  params: Promise<{ id: string }>
}

export default async function QuestaoPage({ params }: Props) {
  const { id } = await params
  const supabase = await createClient()

  // Busca a questão pelo id
  const { data: questao } = await supabase
    .from('questoes')
    .select('*')
    .eq('id', parseInt(id))
    .single()

  if (!questao) notFound()

  // Busca resposta anterior do usuário (se logado)
  const { data: { user } } = await supabase.auth.getUser()
  let respostaAnterior: { acertou: boolean } | null = null
  if (user) {
    const { data: resp } = await supabase
      .from('questoes_erradas')
      .select('acertou')
      .eq('usuario_id', user.id)
      .eq('ano', questao.ano)
      .eq('dia', questao.dia)
      .eq('numero', questao.numero)
      .maybeSingle()
    if (resp) respostaAnterior = { acertou: resp.acertou }
  }

  // Busca questão anterior e próxima (mesma ordem: ano desc, numero asc)
  const [{ data: anterior }, { data: proximo }] = await Promise.all([
    supabase
      .from('questoes')
      .select('id')
      .eq('anulada', false)
      .or(`ano.lt.${questao.ano},and(ano.eq.${questao.ano},numero.lt.${questao.numero})`)
      .order('ano', { ascending: false })
      .order('numero', { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabase
      .from('questoes')
      .select('id')
      .eq('anulada', false)
      .or(`ano.gt.${questao.ano},and(ano.eq.${questao.ano},numero.gt.${questao.numero})`)
      .order('ano', { ascending: true })
      .order('numero', { ascending: true })
      .limit(1)
      .maybeSingle(),
  ])

  // Número da questão na lista geral (aproximado)
  const { count: posicao } = await supabase
    .from('questoes')
    .select('*', { count: 'exact', head: true })
    .eq('anulada', false)
    .or(`ano.gt.${questao.ano},and(ano.eq.${questao.ano},numero.lte.${questao.numero})`)

  return (
    <main className="max-w-3xl mx-auto px-4 sm:px-6 py-6">

      {/* Breadcrumb + navegação */}
      <div className="flex items-center gap-2 text-[12px] text-white/40 mb-5">
        <Link href="/questoes" className="hover:text-white/70 transition">
          Questões
        </Link>
        <span>›</span>
        <span className="text-white/70">Questão {questao.numero}</span>

        <div className="ml-auto flex items-center gap-1">
          <Link
            href={anterior ? `/questoes/${anterior.id}` : '#'}
            aria-disabled={!anterior}
            className={`p-1.5 rounded-md hover:bg-white/5 transition ${!anterior ? 'opacity-30 pointer-events-none' : ''}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </Link>
          {posicao && (
            <span className="text-[11px] tabular-nums text-white/35">
              {posicao}
            </span>
          )}
          <Link
            href={proximo ? `/questoes/${proximo.id}` : '#'}
            aria-disabled={!proximo}
            className={`p-1.5 rounded-md hover:bg-white/5 transition ${!proximo ? 'opacity-30 pointer-events-none' : ''}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </Link>
        </div>
      </div>

      {/* Card da questão */}
      <CardQuestao
        questao={questao as Questao}
        idAnterior={anterior?.id ?? undefined}
        idProximo={proximo?.id ?? undefined}
        respostaAnterior={respostaAnterior}
      />

      {/* Link voltar */}
      <div className="mt-5 text-center">
        <Link
          href="/questoes"
          className="text-[12px] text-white/35 hover:text-white/60 transition"
        >
          ← Voltar para lista de questões
        </Link>
      </div>
    </main>
  )
}
