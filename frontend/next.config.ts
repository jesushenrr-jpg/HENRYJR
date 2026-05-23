import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  serverExternalPackages: ['@react-pdf/renderer', 'puppeteer-core', '@sparticuz/chromium'],
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
