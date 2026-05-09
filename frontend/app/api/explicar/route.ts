import { NextRequest } from 'next/server'

export const runtime = 'edge'

export async function POST(req: NextRequest) {
  const { enunciado, comando, alternativas, gabarito, ano, numero } = await req.json()

  const prompt = `Você é um professor especialista em ENEM. Explique de forma clara e didática a solução da seguinte questão.

**ENEM ${ano} — Questão ${numero}**

${enunciado}

${comando}

Alternativas:
${Object.entries(alternativas as Record<string, string>)
  .map(([l, t]) => `${l}) ${t}`)
  .join('\n')}

**Gabarito: ${gabarito}**

Explique por que a alternativa ${gabarito} é a correta e por que as demais estão erradas. Seja objetivo e didático.`

  const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'llama-3.3-70b-versatile',
      messages: [{ role: 'user', content: prompt }],
      stream: true,
      temperature: 0.3,
      max_tokens: 1024,
    }),
  })

  if (!res.ok || !res.body) {
    return new Response('Erro ao conectar com a IA.', { status: 500 })
  }

  // Transforma o stream SSE do Groq em texto puro para o cliente
  const encoder = new TextEncoder()
  const decoder = new TextDecoder()

  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body!.getReader()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const json = JSON.parse(data)
            const text = json.choices?.[0]?.delta?.content
            if (text) controller.enqueue(encoder.encode(text))
          } catch { /* ignora linhas inválidas */ }
        }
      }
      controller.close()
    },
  })

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
