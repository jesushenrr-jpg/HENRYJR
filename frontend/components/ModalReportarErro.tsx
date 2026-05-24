'use client'

import { useState } from 'react'

interface Props {
  questaoId: number
  ano: number
  dia: string
  numero: number
  onFechar: () => void
}

const TIPOS_ERRO = [
  'Gabarito incorreto',
  'Alternativa com texto errado ou cortado',
  'Enunciado incompleto ou errado',
  'Imagem ausente ou incorreta',
  'Fórmula matemática incorreta',
  'Questão duplicada',
  'Outro',
]

export default function ModalReportarErro({ questaoId, ano, dia, numero, onFechar }: Props) {
  const [tipo, setTipo]         = useState(TIPOS_ERRO[0])
  const [descricao, setDescricao] = useState('')
  const [enviando, setEnviando]  = useState(false)
  const [enviado, setEnviado]    = useState(false)
  const [erro, setErro]          = useState('')

  async function enviar() {
    setEnviando(true)
    setErro('')
    try {
      const res = await fetch('/api/reportar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questao_id: questaoId, ano, dia, numero, tipo_erro: tipo, descricao }),
      })
      if (!res.ok) throw new Error('Erro ao enviar')
      setEnviado(true)
    } catch {
      setErro('Não foi possível enviar o relatório. Tente novamente.')
    }
    setEnviando(false)
  }

  return (
    /* Overlay */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={e => { if (e.target === e.currentTarget) onFechar() }}
    >
      <div className="bg-[#161411] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">

        {/* Cabeçalho */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-white/[0.06]">
          <div>
            <h2 className="text-white font-semibold text-base">Reportar Erro</h2>
            <p className="text-white/40 text-xs mt-0.5">
              Questão {String(numero).padStart(3, '0')} · ENEM {ano} — {dia === 'dia1' ? 'Dia 1' : 'Dia 2'}
            </p>
          </div>
          <button
            onClick={onFechar}
            className="text-white/30 hover:text-white/70 text-xl leading-none transition"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-5">
          {enviado ? (
            <div className="text-center py-4">
              <div className="text-3xl mb-3">✅</div>
              <p className="text-white font-semibold mb-1">Relatório enviado!</p>
              <p className="text-white/50 text-sm mb-5">Obrigado por contribuir com a qualidade da plataforma.</p>
              <button
                onClick={onFechar}
                className="bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] text-sm font-semibold px-6 py-2 rounded-xl transition"
              >
                Fechar
              </button>
            </div>
          ) : (
            <div className="space-y-4">

              {/* Tipo do erro */}
              <div>
                <label className="block text-white/60 text-xs font-medium mb-1.5 uppercase tracking-wide">
                  Tipo de erro
                </label>
                <select
                  value={tipo}
                  onChange={e => setTipo(e.target.value)}
                  className="w-full bg-[#1E1B17] border border-[#2C2820] rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-[#D4A853]/50 transition"
                >
                  {TIPOS_ERRO.map(t => (
                    <option key={t} value={t} className="bg-[#161411]">{t}</option>
                  ))}
                </select>
              </div>

              {/* Descrição */}
              <div>
                <label className="block text-white/60 text-xs font-medium mb-1.5 uppercase tracking-wide">
                  Descrição <span className="text-white/30 normal-case">(opcional)</span>
                </label>
                <textarea
                  value={descricao}
                  onChange={e => setDescricao(e.target.value)}
                  placeholder="Descreva o problema com mais detalhes..."
                  rows={3}
                  className="w-full bg-[#1E1B17] border border-[#2C2820] rounded-xl px-3 py-2.5 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-[#D4A853]/50 transition resize-none"
                />
              </div>

              {erro && (
                <p className="text-red-400 text-xs">{erro}</p>
              )}

              {/* Ações */}
              <div className="flex gap-2 pt-1">
                <button
                  onClick={onFechar}
                  className="flex-1 bg-white/5 hover:bg-white/10 border border-white/5 text-white/60 hover:text-white/90 text-sm font-semibold py-2.5 rounded-xl transition"
                >
                  Cancelar
                </button>
                <button
                  onClick={enviar}
                  disabled={enviando}
                  className="flex-1 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-xl transition"
                >
                  {enviando ? 'Enviando…' : '⚑ Enviar relatório'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
