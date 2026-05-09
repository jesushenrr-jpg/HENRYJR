import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import './globals.css'
import NavBar from '@/components/NavBar'

const geist = Geist({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HenryJr — Banco de Questões ENEM',
  description: 'Todas as questões do ENEM 2009–2024 com simulados, IA e Tira Teima.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${geist.className} bg-[#1e1e2e] text-white antialiased`}>
        <NavBar />
        {children}
      </body>
    </html>
  )
}
