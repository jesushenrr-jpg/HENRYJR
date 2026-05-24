import type { Metadata } from 'next'
import { Playfair_Display, Source_Serif_4, DM_Sans } from 'next/font/google'
import './globals.css'
import NavBar from '@/components/NavBar'
import MobileTabBar from '@/components/MobileTabBar'

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  display: 'swap',
  style: ['normal', 'italic'],
})

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-source-serif',
  display: 'swap',
  style: ['normal', 'italic'],
  weight: ['300', '400', '600'],
})

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dm-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'HenryJr — Banco de Provas',
  description: 'Todas as questões do ENEM 2009–2024 e simulados EXATO com IA, Tira Teima e progresso por competência.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${playfair.variable} ${sourceSerif.variable} ${dmSans.variable}`}>
      <body className="font-sans bg-[#0E0D0B] text-[#F2EDE4] antialiased">
        <NavBar />
        {/* pb-16 reserva espaço para a MobileTabBar em mobile */}
        <div className="min-h-screen pb-16 sm:pb-0">
          {children}
        </div>
        <MobileTabBar />
      </body>
    </html>
  )
}
