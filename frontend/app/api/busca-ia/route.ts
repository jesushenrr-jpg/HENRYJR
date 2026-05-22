import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'edge'

const AREAS_VALIDAS = [
  'Linguagens, Codigos e suas Tecnologias',
  'Ciencias Humanas e suas Tecnologias',
  'Ciencias da Natureza e suas Tecnologias',
  'Matematica e suas Tecnologias',
]

export async function POST(req: NextRequest) {
  const { query } = await req.json()
  if (!query?.trim()) {
    return NextResponse.json({ error: 'Query vazia' }, { status: 400 })
  }

  const prompt = `Você é um assistente para um banco de questões do ENEM (2009–2024).
O usuário quer encontrar questões sobre: "${query}"

Retorne APENAS um JSON válido com:
- "termos": array de 1 a 3 palavras-chave em português para busca textual (termos que provavelmente aparecem nos textos das questões)
- "area": exatamente uma das opções ou null — "Linguagens, Codigos e suas Tecnologias" | "Ciencias Humanas e suas Tecnologias" | "Ciencias da Natureza e suas Tecnologias" | "Matematica e suas Tecnologias"
- "competencia": código H01–H30 se claramente identificável, ou null

Exemplos:
Busca "funções do 2° grau" → {"termos":["função","equação","quadrática"],"area":"Matematica e suas Tecnologias","competencia":"H23"}
Busca "fake news e desinformação" → {"termos":["fake news","desinformação","notícia"],"area":"Linguagens, Codigos e suas Tecnologias","competencia":null}
Busca "fotossíntese" → {"termos":["fotossíntese","cloroplasto","luz solar"],"area":"Ciencias da Natureza e suas Tecnologias","competencia":null}
Busca "revolução industrial" → {"termos":["revolução industrial","industrialização","fábrica"],"area":"Ciencias Humanas e suas Tecnologias","competencia":null}
Busca "questões de física sobre ondas" → {"termos":["onda","frequência","comprimento de onda"],"area":"Ciencias da Natureza e suas Tecnologias","competencia":null}`

  const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.GROQ_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llama-3.1-8b-instant',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 150,
      temperature: 0.1,
      response_format: { type: 'json_object' },
    }),
  })

  if (!res.ok) {
    return NextResponse.json({ error: 'Erro ao consultar IA' }, { status: 502 })
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

  return NextResponse.json({ termos, area, competencia })
}
