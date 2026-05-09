'use client'

import { useState } from 'react'
import type { Questao, LetraAlternativa } from '@/lib/types'
import { urlPdf } from '@/lib/types'
import TextoLatex from './TextoLatex'

interface Props {
  questao: Questao
  onReportar?: () => void
}

const LETRAS: LetraAlternativa[] = ['A', 'B', 'C', 'D', 'E']

export default function CardQuestao({ questao, onReportar }: Props) {
  const [eliminadas, setEliminadas] = useState<Set<LetraAlternativa>>(new Set())
  const [resposta, setResposta] = useState<LetraAlternativa | null>(null)
  const [revelado, setRevelado] = useState(false)
  const [explicacao, setExplicacao] = useState('')
  const [explicandoLoading, setExplicandoLoading] = useState(false)

  function toggleEliminar(l: LetraAlternativa) {
    if (revelado) return
    setEliminadas(prev => {
      const n = new Set(prev)
      n.has(l) ? n.delete(l) : n.add(l)
      return n
    })
  }

  function selecionar(l: LetraAlternativa) {
    if (revelado || eliminadas.has(l)) return
    setResposta(l)
  }

  function revelar() {
    if (!resposta) return
    setRevelado(true)
  }

  async function explicar() {
    setExplicandoLoading(true)
    setExplicacao('')
    try {
      const res = await fetch('/api/explicar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enunciado: questao.enunciado.join('\n\n'),
          comando: questao.comando,
          alternativas: questao.alternativas,
          gabarito: questao.gabarito,
          ano: questao.ano,
          numero: questao.numero,
        }),
      })
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        setExplicacao(prev => prev + decoder.decode(value))
      }
    } catch {
      setExplicacao('Erro ao buscar explicação. Tente novamente.')
    }
    setExplicandoLoading(false)
  }

  function corAlternativa(l: LetraAlternativa) {
    if (!revelado) {
      if (eliminadas.has(l)) return 'opacity-30 line-through'
      if (resposta === l) return 'ring-2 ring-[#7c6af7] bg-[#7c6af7]/10'
      return 'hover:bg-[#313244] cursor-pointer'
    }
    if (l === questao.gabarito) return 'bg-[#40a02b]/20 ring-2 ring-[#40a02b]'
    if (l === resposta && l !== questao.gabarito) return 'bg-[#f38ba8]/20 ring-2 ring-[#f38ba8]'
    return 'opacity-40'
  }

  return (
    <div className="bg-[#2a2a3e] rounded-2xl p-6 shadow-lg space-y-4">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <span className="text-[#7c6af7] font-bold text-lg">
            Questão {questao.numero.toString().padStart(3, '0')}
          </span>
          <span className="text-[#585b70] text-sm ml-3">
            ENEM {questao.ano} · {questao.dia === 'dia1' ? 'Dia 1' : 'Dia 2'}
          </span>
          {questao.anulada && (
            <span className="ml-2 bg-[#f38ba8]/20 text-[#f38ba8] text-xs px-2 py-0.5 rounded-full">
              Anulada
            </span>
          )}
        </div>
        <span className="text-[#a6adc8] text-xs bg-[#313244] px-3 py-1 rounded-full">
          {questao.area}
        </span>
      </div>

      {/* Enunciado */}
      <div className="space-y-3 text-[#cdd6f4] text-sm leading-relaxed">
        {questao.enunciado.map((par, i) => {
          // Imagem posicionada antes_1 ou entre_i_i+1
          const imgAntes = questao.imagens?.find(
            img => img.posicao === `antes_${i + 1}` || (i === 0 && img.posicao === 'antes_1')
          )
          const imgEntre = i > 0
            ? questao.imagens?.find(img => img.posicao === `entre_${i}_${i + 1}`)
            : undefined

          return (
            <div key={i}>
              {imgAntes?.supabase_url && (
                <img src={imgAntes.supabase_url} alt="" className="max-w-full rounded-lg mb-2 mx-auto" />
              )}
              {imgEntre?.supabase_url && (
                <img src={imgEntre.supabase_url} alt="" className="max-w-full rounded-lg mb-2 mx-auto" />
              )}
              <TextoLatex texto={par} />
            </div>
          )
        })}
        {/* Imagem após o último parágrafo */}
        {questao.imagens?.find(img => img.posicao === 'apos_ultimo')?.supabase_url && (
          <img
            src={questao.imagens.find(img => img.posicao === 'apos_ultimo')!.supabase_url}
            alt=""
            className="max-w-full rounded-lg mx-auto"
          />
        )}
      </div>

      {/* Comando */}
      {questao.comando && (
        <p className="text-[#cdd6f4] text-sm font-medium border-l-2 border-[#7c6af7] pl-3">
          <TextoLatex texto={questao.comando} />
        </p>
      )}

      {/* Alternativas */}
      <div className="space-y-2">
        {LETRAS.map(l => {
          const texto = questao.alternativas?.[l]
          if (!texto) return null
          const imgAlt = questao.imagens_alternativas?.[l]
          return (
            <div
              key={l}
              onClick={() => selecionar(l)}
              className={`flex gap-3 items-start p-3 rounded-xl border border-[#45475a] transition-all select-none ${corAlternativa(l)}`}
            >
              {/* Botão tesoura */}
              <button
                onClick={e => { e.stopPropagation(); toggleEliminar(l) }}
                title={eliminadas.has(l) ? 'Restaurar' : 'Eliminar'}
                className="text-[#585b70] hover:text-[#fab387] mt-0.5 flex-shrink-0 text-xs"
              >
                ✂
              </button>
              <span className="font-bold text-[#7c6af7] flex-shrink-0">{l}</span>
              <div className="text-[#cdd6f4] text-sm flex-1">
                <TextoLatex texto={texto} />
                {imgAlt && (
                  <img
                    src={`https://bmhudlpihwxvaelokugh.supabase.co/storage/v1/object/public/imagens-questoes/${imgAlt}`}
                    alt=""
                    className="mt-2 max-w-xs rounded-lg"
                  />
                )}
              </div>
              {/* Ícone de resultado */}
              {revelado && l === questao.gabarito && (
                <span className="text-[#40a02b] flex-shrink-0">✓</span>
              )}
              {revelado && l === resposta && l !== questao.gabarito && (
                <span className="text-[#f38ba8] flex-shrink-0">✗</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Ações */}
      <div className="flex flex-wrap gap-2 pt-2">
        {!revelado && (
          <button
            onClick={revelar}
            disabled={!resposta}
            className="bg-[#7c6af7] hover:bg-[#9580ff] disabled:opacity-40 text-white text-sm font-bold px-4 py-2 rounded-xl transition"
          >
            Revelar resposta
          </button>
        )}
        {revelado && (
          <button
            onClick={explicar}
            disabled={explicandoLoading}
            className="bg-[#1e66f5] hover:bg-[#1455cc] text-white text-sm font-bold px-4 py-2 rounded-xl transition disabled:opacity-50"
          >
            {explicandoLoading ? 'Explicando…' : '✨ Explicar com IA'}
          </button>
        )}
        {questao.pagina_pdf != null && (
          <a
            href={urlPdf(questao.ano, questao.dia, questao.pagina_pdf)}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-[#313244] hover:bg-[#45475a] text-[#cdd6f4] text-sm px-4 py-2 rounded-xl transition"
          >
            📄 Ver PDF
          </a>
        )}
        {onReportar && (
          <button
            onClick={onReportar}
            className="bg-[#313244] hover:bg-[#45475a] text-[#585b70] hover:text-[#fab387] text-sm px-4 py-2 rounded-xl transition"
          >
            ⚑ Reportar erro
          </button>
        )}
      </div>

      {/* Explicação IA */}
      {explicacao && (
        <div className="bg-[#1e2030] rounded-xl p-4 text-[#cdd6f4] text-sm leading-relaxed whitespace-pre-wrap border border-[#45475a]">
          <p className="text-[#7c6af7] font-bold text-xs mb-2">✨ EXPLICAÇÃO — IA</p>
          {explicacao}
        </div>
      )}
    </div>
  )
}
