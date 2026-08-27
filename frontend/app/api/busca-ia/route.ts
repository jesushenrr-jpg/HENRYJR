import { NextRequest, NextResponse } from 'next/server'
import { logEvent, requestId } from '@/lib/observability'

export const runtime = 'edge'

const AREAS_VALIDAS = [
  'Linguagens, Codigos e suas Tecnologias',
  'Ciencias Humanas e suas Tecnologias',
  'Ciencias da Natureza e suas Tecnologias',
  'Matematica e suas Tecnologias',
]

export async function POST(req: NextRequest) {
  const startedAt = Date.now()
  const id = requestId(req)
  const { query } = await req.json()
  if (!query?.trim()) {
    return NextResponse.json({ error: 'Query vazia' }, { status: 400 })
  }

  const prompt = `Você é um assistente para um banco de questões do ENEM (2009–2024).
O usuário quer encontrar questões sobre: "${query}"

Retorne APENAS um JSON válido com:
- "termos": array de 2 a 4 palavras-chave curtas em português para busca textual. Inclua o termo original e sinônimos amplos que provavelmente aparecem literalmente nos textos das questões.
- "area": exatamente uma das opções ou null — "Linguagens, Codigos e suas Tecnologias" | "Ciencias Humanas e suas Tecnologias" | "Ciencias da Natureza e suas Tecnologias" | "Matematica e suas Tecnologias"
- "competencia": código H01–H30 se claramente identificável, ou null

Exemplos:
Busca "funções do 2° grau" → {"termos":["função","equação","quadrática"],"area":"Matematica e suas Tecnologias","competencia":"H23"}
Busca "fake news e desinformação" → {"termos":["fake news","desinformação","notícia"],"area":"Linguagens, Codigos e suas Tecnologias","competencia":null}
Busca "fotossíntese" → {"termos":["fotossíntese","cloroplasto","luz solar"],"area":"Ciencias da Natureza e suas Tecnologias","competencia":null}
Busca "revolução industrial" → {"termos":["revolução industrial","industrialização","fábrica"],"area":"Ciencias Humanas e suas Tecnologias","competencia":null}
Busca "questões de física sobre ondas" → {"termos":["onda","frequência","comprimento de onda"],"area":"Ciencias da Natureza e suas Tecnologias","competencia":null}`

  const apiKey = process.env.GROQ_API_KEY?.trim()
  if (!apiKey) {
    logEvent('error', 'ai.search.config_missing', { request_id: id })
    return NextResponse.json({ termos: [query.trim()], area: null, competencia: null, fallback: true })
  }

  let res: Response
  try {
    res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: process.env.GROQ_SEARCH_MODEL?.trim() || 'openai/gpt-oss-20b',
        messages: [{ role: 'user', content: prompt }],
        max_completion_tokens: 300,
        reasoning_effort: 'low',
        temperature: 0.1,
        response_format: { type: 'json_object' },
      }),
    })
  } catch (error) {
    logEvent('error', 'ai.search.network_error', {
      request_id: id,
      duration_ms: Date.now() - startedAt,
      error: error instanceof Error ? error.name : 'unknown',
    })
    return NextResponse.json({ termos: [query.trim()], area: null, competencia: null, fallback: true })
  }

  if (!res.ok) {
    const detalhe = (await res.text()).slice(0, 1000)
    logEvent('error', 'ai.search.provider_error', {
      request_id: id,
      provider: 'groq',
      provider_status: res.status,
      duration_ms: Date.now() - startedAt,
      detail: detalhe,
    })
    return NextResponse.json({ termos: [query.trim()], area: null, competencia: null, fallback: true })
  }

  const data = await res.json()
  const content = data.choices?.[0]?.message?.content ?? '{}'

  let termos: string[] = []
  let area: string | null = null
  let competencia: string | null = null

  try {
    const parsed = JSON.parse(content)
    termos = Array.isArray(parsed.termos)
      ? parsed.termos.slice(0, 3).map((t: unknown) => String(t).trim()).filter(Boolean)
      : []
    area = AREAS_VALIDAS.includes(parsed.area) ? parsed.area : null
    competencia = /^H\d{2}$/.test(parsed.competencia ?? '') ? parsed.competencia : null
  } catch {
    // fallback: usa a query como termo direto
  }

  if (termos.length === 0) termos = [query.trim()]

  logEvent('info', 'ai.search.success', {
    request_id: id,
    provider: 'groq',
    duration_ms: Date.now() - startedAt,
    terms_count: termos.length,
  })
  return NextResponse.json({ termos, area, competencia })
}
