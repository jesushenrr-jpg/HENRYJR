import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  serverExternalPackages: ['puppeteer-core', '@sparticuz/chromium'],

  // Inclui os binários do Chromium no bundle das funções serverless do Vercel.
  // Sem isso o file-tracing do Next.js exclui arquivos não-JS e o @sparticuz/chromium
  // não encontra seu executável em /var/task/…/node_modules/@sparticuz/chromium/bin
  outputFileTracingIncludes: {
    '/api/pdf/simulado/[id]': ['./node_modules/@sparticuz/chromium/**/*'],
    '/api/pdf/tira-teima':    ['./node_modules/@sparticuz/chromium/**/*'],
  },

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'bmhudlpihwxvaelokugh.supabase.co',
      },
    ],
  },
}

export default nextConfig
