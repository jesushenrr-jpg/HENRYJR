/**
 * GET /api/pdf/simulado/[id]
 * Gera o PDF do simulado usando Puppeteer + @sparticuz/chromium.
 *
 * Funciona sem microserviço externo: o Chromium roda dentro da própria
 * função serverless do Vercel (bundle ≈ 50 MB, timeout máx. 60 s).
 *
 * Variáveis de ambiente (Vercel Dashboard → Settings → Environment Variables):
 *   NEXT_PUBLIC_SITE_URL  – URL canônica do site (ex.: https://frontend-two-khaki-40.vercel.app)
 *                           Se não definida, usa VERCEL_URL (injetado automaticamente pelo Vercel).
 *
 * Em desenvolvimento local:
 *   LOCAL_CHROME_PATH – caminho para o Chrome instalado na máquina
 *                       (ex.: C:\Program Files\Google\Chrome\Application\chrome.exe)
 */
import { NextRequest, NextResponse } from 'next/server'

export const maxDuration = 60   // segundos — máximo no plano Hobby do Vercel

interface Params { params: Promise<{ id: string }> }

/** Detecta a URL base correta dependendo do ambiente */
function getBaseUrl(): string {
  // 1. Variável explícita definida pelo dono do projeto
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, '')
  // 2. Vercel injeta VERCEL_URL automaticamente (sem https://)
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`
  // 3. Desenvolvimento local
  return 'http://localhost:3000'
}

export async function GET(req: NextRequest, { params }: Params) {
  const { id } = await params
  if (!id) return NextResponse.json({ error: 'ID inválido' }, { status: 400 })

  const url = `${getBaseUrl()}/simulado/${id}/imprimir?view=1`
  console.log('[pdf] iniciando →', url)

  // Repassa o cookie de sessão (Supabase Auth) para que a página carregue autenticada
  const cookieHeader = req.headers.get('cookie') ?? ''

  let browser: import('puppeteer-core').Browser | undefined
  try {
    /* ── Inicializa o Puppeteer ── */
    const isDev = process.env.NODE_ENV === 'development'

    let executablePath: string
    let launchArgs: string[]

    if (isDev) {
      // Desenvolvimento local — usa o Chrome do sistema
      const localChrome =
        process.env.LOCAL_CHROME_PATH ||
        (process.platform === 'win32'
          ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
          : process.platform === 'darwin'
          ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
          : '/usr/bin/google-chrome')
      executablePath = localChrome
      launchArgs = []
    } else {
      // Produção (Vercel Lambda) — usa o Chromium do @sparticuz/chromium
      const chromium = (await import('@sparticuz/chromium')).default
      executablePath = await chromium.executablePath()
      launchArgs = chromium.args
    }

    const puppeteer = (await import('puppeteer-core')).default

    browser = await puppeteer.launch({
      executablePath,
      args: [
        ...launchArgs,
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--font-render-hinting=none',
      ],
      headless: true,
    })

    const page = await browser.newPage()

    /* ── Injeta cookies de sessão ── */
    if (cookieHeader) {
      const baseUrl = getBaseUrl()
      const cookieObjects = cookieHeader.split(';').flatMap(pair => {
        const eq = pair.indexOf('=')
        if (eq === -1) return []
        const name  = pair.slice(0, eq).trim()
        const value = pair.slice(eq + 1).trim()
        return name ? [{ name, value, url: baseUrl }] : []
      })
      if (cookieObjects.length > 0) await page.setCookie(...cookieObjects)
    }

    /* ── Navega e aguarda o conteúdo ── */
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 40_000 })

    // Aguarda o bloco principal das questões (ou a mensagem de erro)
    await page.waitForSelector('.area-bloco, .sem-questoes', { timeout: 12_000 }).catch(() => {})

    // Folga extra para fontes e eventuais imagens lazy
    await new Promise(r => setTimeout(r, 600))

    /* ── Gera o PDF ── */
    await page.emulateMediaType('print')

    const pdf = await page.pdf({
      format:          'A4',
      printBackground: true,
      margin: {
        top:    '14mm',
        right:  '10mm',
        bottom: '12mm',
        left:   '10mm',
      },
      displayHeaderFooter: false,
    })

    console.log(`[pdf] gerado — ${pdf.length} bytes`)

    return new NextResponse(pdf, {
      status: 200,
      headers: {
        'Content-Type':        'application/pdf',
        'Content-Disposition': `attachment; filename="simulado-${id}.pdf"`,
        'Content-Length':      pdf.length.toString(),
      },
    })

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[pdf] erro:', msg)
    return NextResponse.json({ error: 'Falha ao gerar PDF', detail: msg }, { status: 500 })
  } finally {
    if (browser) await browser.close().catch(() => {})
  }
}
