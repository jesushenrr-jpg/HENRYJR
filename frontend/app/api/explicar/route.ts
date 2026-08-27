import { NextRequest } from 'next/server'
import { logEvent, requestId } from '@/lib/observability'

export const runtime = 'edge'

export async function POST(req: NextRequest) {
  const startedAt = Date.now()
  const id = requestId(req)
  const { enunciado, comando, alternativas, gabarito, ano, numero } = await req.json()

  const prompt = `Você é um professor especialista em vestibulares. Produza uma resolução detalhada, mas objetiva, para um estudante revisando a questão.

**ENEM ${ano} — Questão ${numero}**

${enunciado}

${comando}

Alternativas:
${Object.entries(alternativas as Record<string, string>)
  .map(([l, t]) => `${l}) ${t}`)
  .join('\n')}

**Gabarito: ${gabarito}**

Siga rigorosamente esta estrutura, em 250 a 400 palavras:
1. **Ideia central** — conceito necessário em 2 ou 3 frases.
2. **Aplicação à questão** — raciocínio direto até o gabarito, sem repetir todo o enunciado.
3. **Alternativas** — uma frase curta para a correta e uma frase curta para cada distrator.
4. **Para lembrar** — uma única frase de revisão.

Não repita a conclusão, não crie perguntas retóricas, não acrescente uma nova seção depois de "Para lembrar" e encerre a resposta completamente.`

  const apiKey = process.env.GROQ_API_KEY?.trim()
  if (!apiKey) {
    logEvent('error', 'ai.explain.config_missing', { request_id: id })
    return new Response('Serviço de IA não configurado no servidor.', { status: 503 })
  }

  let res: Response
  try {
    res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: process.env.GROQ_EXPLAIN_MODEL?.trim() || 'openai/gpt-oss-120b',
        messages: [{ role: 'user', content: prompt }],
        stream: true,
        temperature: 0.3,
        reasoning_effort: 'low',
        reasoning_format: 'hidden',
        max_completion_tokens: 1800,
      }),
    })
  } catch (error) {
    logEvent('error', 'ai.explain.network_error', {
      request_id: id,
      duration_ms: Date.now() - startedAt,
      error: error instanceof Error ? error.name : 'unknown',
    })
    return new Response('Não foi possível acessar o serviço de IA.', { status: 502 })
  }

  if (!res.ok) {
    const detalhe = (await res.text()).slice(0, 1000)
    logEvent('error', 'ai.explain.provider_error', {
      request_id: id,
      provider: 'groq',
      provider_status: res.status,
      duration_ms: Date.now() - startedAt,
      detail: detalhe,
    })
    return new Response(`Serviço de IA indisponível (Groq HTTP ${res.status}).`, { status: 502 })
  }

  if (!res.body) {
    logEvent('error', 'ai.explain.empty_stream', {
      request_id: id,
      duration_ms: Date.now() - startedAt,
    })
    return new Response('O serviço de IA respondeu sem conteúdo.', { status: 502 })
  }

  const encoder = new TextEncoder()
  const decoder = new TextDecoder()

  const stream = new ReadableStream({
    async start(controller) {
      const reader = res.body!.getReader()
      // Buffer acumula bytes até ter uma linha SSE completa
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // { stream: true } evita corrupção de caracteres multi-byte (ã, é, ç...)
        // que chegam partidos entre chunks
        buffer += decoder.decode(value, { stream: true })

        // Processa apenas linhas completas; o restante fica no buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            controller.close()
            return
          }
          try {
            const json = JSON.parse(data)
            const text = json.choices?.[0]?.delta?.content
            if (text) controller.enqueue(encoder.encode(text))
          } catch { /* linha ainda incompleta — não deveria acontecer aqui */ }
        }
      }

      // Flush do decoder (bytes retidos pelo stream: true)
      buffer += decoder.decode()
      for (const line of buffer.split('\n')) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') break
        try {
          const json = JSON.parse(data)
          const text = json.choices?.[0]?.delta?.content
          if (text) controller.enqueue(encoder.encode(text))
        } catch { }
      }

      controller.close()
    },
  })

  logEvent('info', 'ai.explain.stream_started', {
    request_id: id,
    provider: 'groq',
    duration_ms: Date.now() - startedAt,
  })
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'X-Request-Id': id,
    },
  })
}
