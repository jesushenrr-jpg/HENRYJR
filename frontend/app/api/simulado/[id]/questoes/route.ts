/**
 * GET /api/simulado/[id]/questoes
 * Retorna as questões do simulado como JSON (para geração de PDF client-side).
 */
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

interface Params { params: Promise<{ id: string }> }

export async function GET(_req: NextRequest, { params }: Params) {
  const { id } = await params
  if (!id) return NextResponse.json({ error: 'ID inválido' }, { status: 400 })

  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })

  // Busca metadados do simulado (verifica dono)
  const { data: sim, error: simErr } = await supabase
    .from('simulados')
    .select('id, tipo, total_questoes, status, iniciado_em, questoes_ids')
    .eq('id', id)
    .eq('usuario_id', user.id)
    .single()

  if (simErr || !sim) {
    return NextResponse.json({ error: 'Simulado não encontrado' }, { status: 404 })
  }

  // Tenta buscar via respostas_simulado (simulado respondido)
  const { data: respostas } = await supabase
    .from('respostas_simulado')
    .select('questao_id, questoes(id, numero, ano, dia, area, competencia, enunciado, comando, alternativas, gabarito, tem_imagem, imagens, anulada)')
    .eq('simulado_id', id)
    .order('questao_id', { ascending: true })

  let questoes = (respostas ?? [])
    .map(r => r.questoes)
    .filter(Boolean)

  // Fallback: busca direto pelos IDs do simulado
  if (questoes.length === 0 && sim.questoes_ids?.length) {
    const { data: qs } = await supabase
      .from('questoes')
      .select('id, numero, ano, dia, area, competencia, enunciado, comando, alternativas, gabarito, tem_imagem, imagens, anulada')
      .in('id', sim.questoes_ids)
      .order('ano', { ascending: true })
      .order('numero', { ascending: true })
    questoes = qs ?? []
  }

  return NextResponse.json({
    simulado: {
      id:        sim.id,
      tipo:      sim.tipo ?? 'simulado',
      total:     sim.total_questoes ?? questoes.length,
      criado_em: sim.iniciado_em,
    },
    questoes,
  })
}
