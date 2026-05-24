/**
 * GET /api/pdf/tira-teima
 * Gera e retorna o PDF do Tira Teima usando Puppeteer (mesmo padrão do simulado).
 *
 * Navega para /tira-teima/imprimir?view=1 com os cookies de sessão do usuário.
 *
 * Query params:
 *   ?versao=1   → versão do tira-teima (repassada como query param para a página)
 *   ?gabarito=true
 */
import { NextRequest, NextResponse } from 'next/server'

export const maxDuration = 60

function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_SITE_URL) return process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, '')
  if (process.env.VERCEL_URL)           return `https://${process.env.VERCEL_URL}`
  return 'http://localhost:3000'
}

export async function GET(req: NextRequest) {
  const versao          = req.nextUrl.searchParams.get('versao') ?? '1'
  const incluirGabarito = req.nextUrl.searchParams.get('gabarito') === 'true'
  const cookieHeader    = req.headers.get('cookie') ?? ''

  const baseUrl = getBaseUrl()
  const params  = new URLSearchParams({ view: '1', versao, ...(incluirGabarito && { gabarito: 'true' }) })
  const url     = `${baseUrl}/tira-teima/imprimir?${params}`

  console.log('[pdf/tira-teima] iniciando →', url)

  let browser: import('puppeteer-core').Browser | undefined
  try {
    const isDev = process.env.NODE_ENV === 'development'
    let executablePath: string
    let launchArgs: string[]

    if (isDev) {
      executablePath =
        process.env.LOCAL_CHROME_PATH ||
        (process.platform === 'win32'
          ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
          : process.platform === 'darwin'
          ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
          : '/usr/bin/google-chrome')
      launchArgs = []
    } else {
      const chromium = (await import('@sparticuz/chromium')).default
      executablePath = await chromium.executablePath()
      launchArgs     = chromium.args
    }

    const puppeteer = (await import('puppeteer-core')).default

    browser = await puppeteer.launch({
      executablePath,
      args: [...launchArgs, '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
      headless: true,
    })

    const page = await browser.newPage()

    if (cookieHeader) {
      const cookies = cookieHeader.split(';').flatMap(pair => {
        const eq = pair.indexOf('=')
        if (eq === -1) return []
        const name  = pair.slice(0, eq).trim()
        const value = pair.slice(eq + 1).trim()
        return name ? [{ name, value, url: baseUrl }] : []
      })
      if (cookies.length > 0) await page.setCookie(...cookies)
    }

    await page.goto(url, { waitUntil: 'networkidle0', timeout: 40_000 })
    await page.waitForSelector('.area-bloco, .sem-questoes, .nao-implementado', { timeout: 12_000 }).catch(() => {})
    await new Promise(r => setTimeout(r, 600))
    await page.emulateMediaType('print')

    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: { top: '14mm', right: '10mm', bottom: '12mm', left: '10mm' },
      displayHeaderFooter: false,
    })

    const buf = Buffer.from(pdf)
    console.log(`[pdf/tira-teima] gerado — ${buf.length} bytes`)

    return new NextResponse(buf, {
      status: 200,
      headers: {
        'Content-Type':        'application/pdf',
        'Content-Disposition': `attachment; filename="tira-teima-v${versao}.pdf"`,
        'Content-Length':      buf.length.toString(),
      },
    })

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[pdf/tira-teima] erro:', msg)
    return NextResponse.json({ error: 'Falha ao gerar PDF do Tira Teima', detail: msg }, { status: 500 })
  } finally {
    if (browser) await browser.close().catch(() => {})
  }
}
