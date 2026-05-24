import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  serverExternalPackages: ['puppeteer-core', '@sparticuz/chromium'],
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
