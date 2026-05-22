'use client'

/**
 * BaixarPDFSimulado
 * Gera e baixa o PDF do simulado inteiramente no browser.
 * Evita timeouts de serverless — @react-pdf/renderer funciona melhor no cliente.
 */
import { useState } from 'react'
import dynamic from 'next/dynamic'
import type { QuestaoSimulado, SimuladoInfo } from '@/lib/pdf/SimuladoPDF'

// Carrega o componente de download apenas no browser (sem SSR)
const PDFDownloadLink = dynamic(
  () => import('@react-pdf/renderer').then(m => m.PDFDownloadLink),
  { ssr: false }
)
const SimuladoPDFDoc = dynamic(
  () => import('@/lib/pdf/SimuladoPDF').then(m => m.SimuladoPDF),
  { ssr: false }
)

interface Props {
  simuladoId: number
  label?: string
  className?: string
}

type Estado = 'idle' | 'carregando' | 'pronto' | 'erro'

export default function BaixarPDFSimulado({ simuladoId, label = '🖨️ Imprimir e resolver', className }: Props) {
  const [estado,   setEstado]  = useState<Estado>('idle')
  const [questoes, setQuestoes] = useState<QuestaoSimulado[] | null>(null)
  const [simInfo,  setSimInfo]  = useState<SimuladoInfo | null>(null)

  async function carregar() {
    setEstado('carregando')
    try {
      const res = await fetch(`/api/simulado/${simuladoId}/questoes`)
      if (!res.ok) throw new Error('Erro ao buscar questões')
      const data = await res.json()
      setQuestoes(data.questoes)
      setSimInfo(data.simulado)
      setEstado('pronto')
    } catch {
      setEstado('erro')
    }
  }

  const baseClass = className ?? 'flex flex-col items-center gap-2 rounded-xl border border-[#2C2820] bg-[#1E1B17] hover:bg-[#252118] p-5 transition w-full'

  if (estado === 'idle') {
    return (
      <button onClick={carregar} className={baseClass}>
        <span className="text-3xl">🖨️</span>
        <span className="font-bold text-white/85">Imprimir e resolver</span>
        <span className="text-xs text-white/40">Baixar PDF · corrigir por foto depois</span>
      </button>
    )
  }

  if (estado === 'carregando') {
    return (
      <div className={baseClass}>
        <svg className="animate-spin w-6 h-6 text-white/40" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span className="text-sm text-white/50">Preparando PDF...</span>
      </div>
    )
  }

  if (estado === 'erro') {
    return (
      <button onClick={carregar} className={baseClass}>
        <span className="text-3xl">⚠️</span>
        <span className="font-bold text-red-400">Erro — tentar novamente</span>
      </button>
    )
  }

  // Estado 'pronto': mostra o link de download gerado no browser
  return (
    <PDFDownloadLink
      document={
        <SimuladoPDFDoc
          questoes={questoes!}
          simulado={simInfo!}
          incluirGabarito={false}
        />
      }
      fileName={`simulado-${simuladoId}.pdf`}
      className={baseClass}
    >
      {({ loading }) =>
        loading ? (
          <>
            <svg className="animate-spin w-6 h-6 text-white/40" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span className="text-sm text-white/50">Gerando PDF...</span>
          </>
        ) : (
          <>
            <span className="text-3xl">📥</span>
            <span className="font-bold text-emerald-400">Clique para baixar</span>
            <span className="text-xs text-white/40">{questoes?.length} questões · PDF pronto</span>
          </>
        )
      }
    </PDFDownloadLink>
  )
}
