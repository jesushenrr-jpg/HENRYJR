/**
 * GET /api/pdf/simulado/[id]
 * Proxy para o microserviço Puppeteer que gera o PDF do simulado.
 *
 * Variáveis de ambiente necessárias no Vercel:
 *   PDF_SERVICE_URL  – URL base do pdf-service (ex.: https://pdf-service.up.railway.app)
 *   PDF_API_KEY      – mesma chave configurada no pdf-service (opcional mas recomendado)
 */
import { NextRequest, NextResponse } from 'next/server'

interface Params { params: Promise<{ id: string }> }

export async function GET(req: NextRequest, { params }: Params) {
  const { id } = await params

  const serviceUrl = process.env.PDF_SERVICE_URL
  if (!serviceUrl) {
    return NextResponse.json(
      { error: 'PDF_SERVICE_URL não configurado' },
      { status: 503 }
    )
  }

  // Repassa os cookies do browser (sessão Supabase) para o microserviço,
  // que os injeta no Puppeteer para que a página autenticada carregue.
  const cookieHeader = req.headers.get('cookie') || ''
  const apiKey       = process.env.PDF_API_KEY || ''

  const upstreamUrl = `${serviceUrl.replace(/\/$/, '')}/pdf/${id}`

  let upstream: Response
  try {
    upstream = await fetch(upstreamUrl, {
      headers: {
        ...(cookieHeader && { cookie: cookieHeader }),
        ...(apiKey       && { 'x-api-key': apiKey }),
      },
      // Timeout de 60 s (Puppeteer pode demorar em cold start)
      signal: AbortSignal.timeout(60_000),
    })
  } catch (err) {
    console.error('[/api/pdf] Erro ao chamar pdf-service:', err)
    return NextResponse.json({ error: 'Serviço de PDF indisponível' }, { status: 502 })
  }

  if (!upstream.ok) {
    const body = await upstream.text().catch(() => '')
    console.error(`[/api/pdf] pdf-service retornou ${upstream.status}:`, body)
    return NextResponse.json(
      { error: 'Falha ao gerar PDF', detail: body },
      { status: upstream.status }
    )
  }

  const pdf      = await upstream.arrayBuffer()
  const filename = `simulado-${id}.pdf`

  return new NextResponse(pdf, {
    status: 200,
    headers: {
      'Content-Type':        'application/pdf',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Content-Length':      pdf.byteLength.toString(),
    },
  })
}
