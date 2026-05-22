/**
 * GET /api/pdf/simulado/[id]
 * Gera e retorna o PDF do simulado (questões + folha de respostas + gabarito).
 *
 * Query params:
 *   ?gabarito=true   → inclui gabarito na folha de respostas (para o professor)
 */
import { NextRequest, NextResponse } from 'next/server'
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { renderToBuffer } = require('@react-pdf/renderer') as { renderToBuffer: (el: unknown) => Promise<Buffer> }
import React                          from 'react'
import { createClient }               from '@/lib/supabase/server'
import { SimuladoPDF }                from '@/lib/pdf/SimuladoPDF'
import type { QuestaoSimulado }       from '@/lib/pdf/SimuladoPDF'

interface Params { params: Promise<{ id: string }> }

export async function GET(req: NextRequest, { params }: Params) {
  const { id } = await params
  if (!id) {
    return NextResponse.json({ error: 'ID inválido' }, { status: 400 })
  }
  // Suporta tanto UUID (string) quanto integer
  const simId: string | number = /^\d+$/.test(id) ? parseInt(id, 10) : id

  const supabase = await createClient()

  // Verifica autenticação
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })
  }

  // Busca metadados do simulado
  const { data: sim, error: simErr } = await supabase
    .from('simulados')
    .select('id, tipo, total_questoes, status, iniciado_em')
    .eq('id', simId)
    .eq('usuario_id', user.id)
    .single()

  if (simErr || !sim) {
    return NextResponse.json({ error: 'Simulado não encontrado' }, { status: 404 })
  }

  // Tenta buscar questões via respostas_simulado (simulado já respondido)
  const { data: respostas } = await supabase
    .from('respostas_simulado')
    .select(`
      questao_id,
      questoes (
        id, numero, ano, dia, area, competencia,
        enunciado, comando, alternativas, gabarito,
        tem_imagem, imagens, anulada
      )
    `)
    .eq('simulado_id', simId)
    .order('questao_id', { ascending: true })

  let questoes: QuestaoSimulado[] = (respostas ?? [])
    .map(r => r.questoes as unknown as QuestaoSimulado)
    .filter(Boolean)

  // Fallback: simulado recém-criado (ainda sem respostas) → busca via questoes_ids
  if (questoes.length === 0) {
    const { data: simFull } = await supabase
      .from('simulados')
      .select('questoes_ids')
      .eq('id', simId)
      .single()

    const ids: number[] = simFull?.questoes_ids ?? []
    if (ids.length === 0) {
      return NextResponse.json({ error: 'Sem questões no simulado' }, { status: 404 })
    }

    const { data: qs } = await supabase
      .from('questoes')
      .select('id, numero, ano, dia, area, competencia, enunciado, comando, alternativas, gabarito, tem_imagem, imagens, anulada')
      .in('id', ids)
      .order('ano', { ascending: true })
      .order('numero', { ascending: true })

    questoes = (qs ?? []) as unknown as QuestaoSimulado[]
  }

  if (questoes.length === 0) {
    return NextResponse.json({ error: 'Sem questões no simulado' }, { status: 404 })
  }

  const incluirGabarito = req.nextUrl.searchParams.get('gabarito') === 'true'

  // Gera o PDF
  let buffer: Buffer
  try {
    buffer = await renderToBuffer(
      React.createElement(SimuladoPDF, {
        questoes,
        simulado: {
          id:        sim.id,
          tipo:      sim.tipo ?? 'simulado',
          total:     sim.total_questoes ?? questoes.length,
          criado_em: sim.iniciado_em,
        },
        incluirGabarito,
      })
    )
  } catch (err) {
    console.error('[PDF] Erro ao gerar:', err)
    return NextResponse.json({ error: 'Falha ao gerar PDF' }, { status: 500 })
  }

  const filename = `simulado-${simId}${incluirGabarito ? '-gabarito' : ''}.pdf`

  return new NextResponse(new Uint8Array(buffer), {
    status: 200,
    headers: {
      'Content-Type':        'application/pdf',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Content-Length':      buffer.length.toString(),
    },
  })
}
