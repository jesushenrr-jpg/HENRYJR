/**
 * POST /api/corrigir
 * Proxy para o microserviço FastAPI de visão computacional.
 * Recebe a foto da folha + n_questoes, retorna as respostas detectadas.
 *
 * Body: multipart/form-data
 *   - file: Blob (JPEG/PNG)
 *   - simulado_id: string
 *   - n_questoes: string
 */
import { NextRequest, NextResponse } from 'next/server'
import { createClient }              from '@/lib/supabase/server'

const MICROSERVICO_URL = process.env.MICROSERVICO_URL ?? 'http://localhost:8000'

export async function POST(req: NextRequest) {
  // Verifica autenticação
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })
  }

  let formData: FormData
  try {
    formData = await req.formData()
  } catch {
    return NextResponse.json({ error: 'Formato de request inválido' }, { status: 400 })
  }

  const file       = formData.get('file')       as File | null
  const simIdStr   = formData.get('simulado_id') as string | null
  const nQuestStr  = formData.get('n_questoes')  as string | null

  if (!file || !simIdStr || !nQuestStr) {
    return NextResponse.json(
      { error: 'Campos obrigatórios: file, simulado_id, n_questoes' },
      { status: 400 }
    )
  }

  const simuladoId = parseInt(simIdStr, 10)
  const nQuestoes  = parseInt(nQuestStr, 10)

  if (isNaN(simuladoId) || isNaN(nQuestoes) || nQuestoes < 1 || nQuestoes > 180) {
    return NextResponse.json({ error: 'Parâmetros inválidos' }, { status: 400 })
  }

  // Valida propriedade do simulado
  const { data: sim } = await supabase
    .from('simulados')
    .select('id, total_questoes')
    .eq('id', simuladoId)
    .eq('usuario_id', user.id)
    .single()

  if (!sim) {
    return NextResponse.json({ error: 'Simulado não encontrado' }, { status: 404 })
  }

  // Repassa para o microserviço
  const upstream = new FormData()
  upstream.append('file', file)
  upstream.append('n_questoes', String(sim.total_questoes ?? nQuestoes))

  let respMicro: Response
  try {
    respMicro = await fetch(`${MICROSERVICO_URL}/corrigir`, {
      method: 'POST',
      body:   upstream,
      signal: AbortSignal.timeout(30_000),
    })
  } catch (err) {
    console.error('[corrigir] Microserviço indisponível:', err)
    return NextResponse.json(
      { error: 'Serviço de correção indisponível. Tente novamente em instantes.' },
      { status: 503 }
    )
  }

  if (!respMicro.ok) {
    const txt = await respMicro.text().catch(() => '')
    console.error(`[corrigir] Microserviço retornou ${respMicro.status}:`, txt)
    return NextResponse.json(
      { error: `Falha na correção: ${respMicro.statusText}` },
      { status: respMicro.status }
    )
  }

  const resultado = await respMicro.json()
  return NextResponse.json(resultado)
}
