/**
 * GET /api/pdf/tira-teima
 * Gera e retorna o PDF do Tira Teima do usuário logado.
 * Inclui as questões erradas (da tabela questoes_erradas) em layout ENEM.
 *
 * Query params:
 *   ?gabarito=true  → inclui gabarito
 *   ?versao=1       → versão do tira-teima (padrão: 1)
 */
import { NextRequest, NextResponse } from 'next/server'
// eslint-disable-next-line @typescript-eslint/no-require-imports
const { renderToBuffer } = require('@react-pdf/renderer') as { renderToBuffer: (el: unknown) => Promise<Buffer> }
import React                          from 'react'
import { createClient }               from '@/lib/supabase/server'
import { SimuladoPDF }                from '@/lib/pdf/SimuladoPDF'
import type { QuestaoSimulado }       from '@/lib/pdf/SimuladoPDF'

export async function GET(req: NextRequest) {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })
  }

  const versao          = parseInt(req.nextUrl.searchParams.get('versao') ?? '1', 10)
  const incluirGabarito = req.nextUrl.searchParams.get('gabarito') === 'true'

  // Busca questões erradas do usuário (sem acerto na última tentativa)
  const { data: erradas } = await supabase
    .from('questoes_erradas')
    .select(`
      questao_id, acertou,
      questoes (
        id, numero, ano, dia, area, competencia,
        enunciado, comando, alternativas, gabarito,
        tem_imagem, imagens, anulada
      )
    `)
    .eq('usuario_id', user.id)
    .eq('acertou', false)
    .order('questao_id', { ascending: true })

  if (!erradas?.length) {
    return NextResponse.json({ error: 'Nenhuma questão errada encontrada' }, { status: 404 })
  }

  // Remove duplicatas (mantém a mais recente por questão)
  const vistas = new Set<number>()
  const questoes: QuestaoSimulado[] = []
  for (const r of erradas) {
    const q = r.questoes as unknown as QuestaoSimulado
    if (q && !vistas.has(q.id)) {
      vistas.add(q.id)
      questoes.push(q)
    }
  }

  const agora = new Date().toISOString()

  let buffer: Buffer
  try {
    buffer = await renderToBuffer(
      React.createElement(SimuladoPDF, {
        questoes,
        simulado: {
          id:        versao,
          tipo:      'tira-teima',
          total:     questoes.length,
          criado_em: agora,
        },
        incluirGabarito,
      })
    )
  } catch (err) {
    console.error('[PDF Tira Teima] Erro:', err)
    return NextResponse.json({ error: 'Falha ao gerar PDF' }, { status: 500 })
  }

  const filename = `tira-teima-v${versao}.pdf`

  return new NextResponse(new Uint8Array(buffer), {
    status: 200,
    headers: {
      'Content-Type':        'application/pdf',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Content-Length':      buffer.length.toString(),
    },
  })
}
