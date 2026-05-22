import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import ImprimirClient   from './ImprimirClient'

interface Props { params: Promise<{ id: string }> }

export default async function ImprimirPage({ params }: Props) {
  const { id }   = await params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login')

  const { data: sim } = await supabase
    .from('simulados')
    .select('id, tipo, total_questoes, status, iniciado_em, questoes_ids')
    .eq('id', id)
    .eq('usuario_id', user.id)
    .single()

  if (!sim) redirect('/simulado')

  // Busca questões via respostas_simulado ou questoes_ids
  let questoes: Record<string, unknown>[] = []

  const { data: resps } = await supabase
    .from('respostas_simulado')
    .select('questoes(id,numero,ano,dia,area,enunciado,comando,alternativas,gabarito,anulada)')
    .eq('simulado_id', id)
    .order('questao_id', { ascending: true })

  if (resps?.length) {
    questoes = resps.map(r => r.questoes as unknown as Record<string, unknown>).filter(Boolean)
  } else if (sim.questoes_ids?.length) {
    const { data: qs } = await supabase
      .from('questoes')
      .select('id,numero,ano,dia,area,enunciado,comando,alternativas,gabarito,anulada')
      .in('id', sim.questoes_ids)
      .order('ano').order('numero')
    questoes = qs ?? []
  }

  return (
    <ImprimirClient
      questoes={questoes}
      simulado={{ id: sim.id, total: sim.total_questoes ?? questoes.length, iniciado_em: sim.iniciado_em }}
    />
  )
}
