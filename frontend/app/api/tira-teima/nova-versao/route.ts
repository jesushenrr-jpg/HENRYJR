/**
 * POST /api/tira-teima/nova-versao
 *
 * Gera uma nova versão do Tira Teima com base nas questões que o aluno errou
 * na última sessão. Chame este endpoint ao concluir um simulado modo Tira Teima.
 *
 * Body: { simulado_id: string }
 *
 * Lógica:
 * 1. Busca as respostas do simulado_id
 * 2. Para questões acertadas → marca zerada=true em questoes_erradas
 * 3. Para questões erradas → incrementa versao_tt (cria nova entrada ou atualiza)
 * 4. Retorna { versao_nova, questoes_na_nova_versao }
 */

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })

  const { simulado_id } = await req.json()
  if (!simulado_id) return NextResponse.json({ error: 'simulado_id obrigatório' }, { status: 400 })

  // Verificar que o simulado pertence ao usuário e é do tipo tira-teima
  const { data: sim } = await supabase
    .from('simulados')
    .select('tipo, status, questoes_ids')
    .eq('id', simulado_id)
    .eq('usuario_id', user.id)
    .single()

  if (!sim) return NextResponse.json({ error: 'Simulado não encontrado' }, { status: 404 })
  if (sim.tipo !== 'tira-teima') return NextResponse.json({ error: 'Simulado não é do tipo tira-teima' }, { status: 400 })
  if (sim.status !== 'concluido') return NextResponse.json({ error: 'Simulado ainda não concluído' }, { status: 400 })

  // Buscar respostas
  const { data: respostas } = await supabase
    .from('respostas_simulado')
    .select('questao_id, correta')
    .eq('simulado_id', simulado_id)

  if (!respostas?.length) return NextResponse.json({ versao_nova: 1, questoes_na_nova_versao: 0 })

  const acertadas   = respostas.filter(r => r.correta).map(r => r.questao_id)
  const erradasNovamente = respostas.filter(r => !r.correta).map(r => r.questao_id)

  // 1. Marcar questões acertadas como zeradas
  if (acertadas.length > 0) {
    await supabase
      .from('questoes_erradas')
      .update({ zerada: true, acertou: true })
      .eq('usuario_id', user.id)
      .in('questao_id', acertadas)
  }

  // 2. Determinar versão atual
  const { data: maxVersaoRow } = await supabase
    .from('questoes_erradas')
    .select('versao_tt')
    .eq('usuario_id', user.id)
    .order('versao_tt', { ascending: false })
    .limit(1)
    .single()

  const versaoAtual = (maxVersaoRow?.versao_tt ?? 1)
  const versaoNova  = versaoAtual + 1

  // 3. Para questões erradas novamente: atualizar para a nova versão
  if (erradasNovamente.length > 0) {
    await supabase
      .from('questoes_erradas')
      .update({ versao_tt: versaoNova, acertou: false, zerada: false })
      .eq('usuario_id', user.id)
      .in('questao_id', erradasNovamente)
  }

  return NextResponse.json({
    versao_nova: versaoNova,
    questoes_na_nova_versao: erradasNovamente.length,
    questoes_zeradas: acertadas.length,
  })
}
