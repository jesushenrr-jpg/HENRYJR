import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import SimuladoPlayer   from './SimuladoPlayer'

interface Props { params: Promise<{ id: string }> }

export default async function SimuladoPage({ params }: Props) {
  const { id }   = await params
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/auth/login')

  // Carrega o simulado
  const { data: sim } = await supabase
    .from('simulados')
    .select('*')
    .eq('id', id)
    .eq('usuario_id', user.id)
    .single()

  if (!sim) redirect('/simulado')
  if (sim.status === 'concluido') redirect(`/simulado/${id}/resultado`)

  // Carrega as questões do simulado
  const { data: questoes } = await supabase
    .from('questoes')
    .select('id, ano, dia, numero, area, competencia, enunciado, comando, alternativas, gabarito, tem_imagem, imagens')
    .in('id', sim.questoes_ids)
    .order('ano')
    .order('numero')

  if (!questoes || questoes.length === 0) redirect('/simulado')

  // Ordena conforme questoes_ids (ordem do simulado)
  const ordenadas = (sim.questoes_ids as number[]).map(
    qid => questoes.find(q => q.id === qid)!
  ).filter(Boolean)

  return (
    <SimuladoPlayer
      simuladoId={Number(id)}
      questoes={ordenadas}
      totalQuestoes={sim.total_questoes}
    />
  )
}
