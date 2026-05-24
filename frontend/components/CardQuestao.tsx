'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { Questao, LetraAlternativa } from '@/lib/types'
import { urlPdf } from '@/lib/types'
import { COMPETENCIAS } from '@/lib/competencias'
import TextoLatex from './TextoLatex'
import ModalReportarErro from './ModalReportarErro'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  questao: Questao
  /** IDs vizinhos para navegação (opcional — usado na tela individual) */
  idAnterior?: number
  idProximo?: number
  /** Resultado já registrado anteriormente */
  respostaAnterior?: { acertou: boolean } | null
}

const LETRAS: LetraAlternativa[] = ['A', 'B', 'C', 'D', 'E']

const COR_AREA: Record<string, { bg: string; text: string; border: string }> = {
  'Linguagens, Codigos e suas Tecnologias':   { bg: 'bg-sky-500/15',     text: 'text-sky-300',     border: 'border-sky-500/30' },
  'Ciencias Humanas e suas Tecnologias':      { bg: 'bg-amber-500/15',   text: 'text-amber-300',   border: 'border-amber-500/30' },
  'Ciencias da Natureza e suas Tecnologias':  { bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  'Matematica e suas Tecnologias':            { bg: 'bg-violet-500/15',  text: 'text-violet-300',  border: 'border-violet-500/30' },
}

/** Detecta se o parágrafo é uma fonte/citação (ex: "Disponível em...", "NOME, A. Obra.") */
function isFonte(par: string): boolean {
  return (
    par.length < 220 &&
    /^(Disponível|[A-Z][A-Z]+,\s|[A-Z][a-z]+,\s[A-Z]\.|Acesso em|Fonte:|Adaptado)/.test(par)
  )
}

export default function CardQuestao({ questao, idAnterior, idProximo, respostaAnterior }: Props) {
  const [eliminadas, setEliminadas] = useState<Set<LetraAlternativa>>(new Set())
  const [resposta, setResposta]     = useState<LetraAlternativa | null>(null)
  const [revelado, setRevelado]     = useState(false)
  const [explicacao, setExplicacao] = useState('')
  const [explicLoading, setExplicLoading] = useState(false)
  const [modalReportar, setModalReportar] = useState(false)

  const corArea = COR_AREA[questao.area] ?? { bg: 'bg-white/5', text: 'text-white/50', border: 'border-white/10' }

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
    setResposta(l === resposta ? null : l)
  }

  function revelar() {
    if (!resposta || revelado) return
    setRevelado(true)
    fetch('/api/resposta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        questao_id:       questao.id,
        ano:              questao.ano,
        dia:              questao.dia,
        numero:           questao.numero,
        area:             questao.area,
        resposta_usuario: resposta,
        gabarito:         questao.gabarito,
      }),
    }).catch(() => {})
  }

  async function explicar() {
    setExplicLoading(true)
    setExplicacao('')
    try {
      const res = await fetch('/api/explicar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enunciado:    questao.enunciado.join('\n\n'),
          comando:      questao.comando,
          alternativas: questao.alternativas,
          gabarito:     questao.gabarito,
          ano:          questao.ano,
          numero:       questao.numero,
        }),
      })
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        setExplicacao(prev => prev + decoder.decode(value, { stream: true }))
      }
    } catch {
      setExplicacao('Erro ao buscar explicação. Tente novamente.')
    }
    setExplicLoading(false)
  }

  function classAlternativa(l: LetraAlternativa): string {
    const base = 'group/alt relative flex items-start gap-3 p-3.5 rounded-xl border transition-all select-none'
    if (eliminadas.has(l))
      return `${base} border-transparent opacity-30 line-through cursor-default`
    if (!revelado) {
      if (resposta === l)
        return `${base} border-[#D4A853] bg-[#D4A853]/10 cursor-pointer`
      return `${base} border-[#2C2820] bg-[#1E1B17] hover:border-white/15 cursor-pointer`
    }
    if (l === questao.gabarito)
      return `${base} border-emerald-500/50 bg-emerald-500/10 cursor-default`
    if (l === resposta && l !== questao.gabarito)
      return `${base} border-red-500/50 bg-red-500/10 cursor-default`
    return `${base} border-transparent opacity-30 cursor-default`
  }

  function letraClass(l: LetraAlternativa) {
    if (!revelado) {
      if (resposta === l) return 'bg-[#D4A853] text-[#0E0D0B]'
      return 'bg-white/[0.08] text-white/55'
    }
    if (l === questao.gabarito) return 'bg-emerald-500 text-white'
    if (l === resposta && l !== questao.gabarito) return 'bg-red-500 text-white'
    return 'bg-white/[0.08] text-white/55'
  }

  const acertou = revelado && resposta === questao.gabarito

  return (
    <article className="bg-[#161411] border border-[#2C2820] rounded-2xl overflow-hidden anim-fade">

      {/* Cabeçalho */}
      <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-3.5 border-b border-[#2C2820]">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${corArea.bg} ${corArea.text} border ${corArea.border}`}>
            {questao.area.split(',')[0].replace('Ciencias ', 'C. ').replace('Linguagens', 'Ling.').replace('Matematica', 'Mat.')}
          </span>
          {questao.competencia && (
            <span
              title={COMPETENCIAS[questao.competencia]?.descricao}
              className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.04] text-white/45 border border-white/10 font-mono cursor-help"
            >
              {questao.competencia}
            </span>
          )}
          <span className="text-white/15">·</span>
          <span className="text-[11px] text-white/40">
            ENEM {questao.ano} · {questao.dia === 'dia1' ? '1º dia' : '2º dia'} · Q. {questao.numero}
          </span>
          {/* Badge resposta anterior */}
          {respostaAnterior != null && (
            <span className={`ml-auto px-2 py-0.5 rounded text-[10px] font-semibold ${
              respostaAnterior.acertou
                ? 'bg-emerald-500/15 text-emerald-300'
                : 'bg-rose-500/15 text-rose-300'
            }`}>
              {respostaAnterior.acertou ? '✓ Acertou' : '✗ Errou'}
            </span>
          )}
          {questao.anulada && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">Anulada</span>
          )}
        </div>
        {/* Navegação prev/next (usada na tela individual) */}
        {(idAnterior != null || idProximo != null) && (
          <div className="flex items-center gap-1 flex-shrink-0">
            <Link
              href={idAnterior != null ? `/questoes/${idAnterior}` : '#'}
              aria-disabled={idAnterior == null}
              className={`p-1.5 rounded-md hover:bg-white/5 transition ${idAnterior == null ? 'opacity-30 pointer-events-none' : ''}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
            </Link>
            <Link
              href={idProximo != null ? `/questoes/${idProximo}` : '#'}
              aria-disabled={idProximo == null}
              className={`p-1.5 rounded-md hover:bg-white/5 transition ${idProximo == null ? 'opacity-30 pointer-events-none' : ''}`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </Link>
          </div>
        )}
      </div>

      <div className="px-5 sm:px-7 py-5 space-y-5">

        {/* Banner para enunciado indisponível (encoding protegido) */}
        {questao.enunciado[0]?.startsWith('⚠') && (
          <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-200 text-[13px] leading-relaxed">
            <svg className="shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <span>Enunciado não disponível — o PDF original usa fonte com encoding protegido pelo INEP. Use o botão <strong>Ver no PDF</strong> abaixo para ler a questão completa.</span>
          </div>
        )}

        {/* Enunciado — font-serif Lora, com detecção de parágrafo */}
        <div className="space-y-3">
          {questao.imagens?.find(img => img.posicao === 'antes_1')?.supabase_url && (
            <img
              src={questao.imagens.find(img => img.posicao === 'antes_1')!.supabase_url}
              alt="" className="w-full max-h-[280px] object-contain rounded-xl border border-[#2C2820] bg-white mb-2"
            />
          )}
          {questao.enunciado.map((par, i) => {
            if (par.startsWith('⚠')) return null
            const fonte    = isFonte(par)
            const isUltimo = i === questao.enunciado.length - 1
            const imgAntes = questao.imagens?.find(img => img.posicao === `antes_${i + 2}`)
            const imgEntre = i > 0 ? questao.imagens?.find(img => img.posicao === `entre_${i}_${i + 1}`) : undefined
            return (
              <div key={i}>
                {imgEntre?.supabase_url && (
                  <img src={imgEntre.supabase_url} alt="" className="max-w-full rounded-xl mb-3 mx-auto border border-[#2C2820]" />
                )}
                <p
                  className={`font-serif leading-[1.8] whitespace-pre-wrap ${
                    fonte
                      ? 'text-[12px] italic text-white/40'
                      : isUltimo && !par.startsWith('"') && !par.startsWith('"')
                      ? 'text-[15px] text-white/90 mt-4 pl-3 border-l-2 border-[#D4A853]'
                      : 'text-[15px] text-white/75'
                  }`}
                >
                  <TextoLatex texto={par} />
                </p>
                {imgAntes?.supabase_url && (
                  <img src={imgAntes.supabase_url} alt="" className="max-w-full rounded-xl mt-3 mx-auto border border-[#2C2820]" />
                )}
              </div>
            )
          })}
          {questao.imagens?.find(img => img.posicao === 'apos_ultimo')?.supabase_url && (
            <img
              src={questao.imagens.find(img => img.posicao === 'apos_ultimo')!.supabase_url}
              alt="" className="max-w-full rounded-xl mx-auto border border-[#2C2820]"
            />
          )}
        </div>

        {/* Comando separado (quando existe) */}
        {questao.comando && (
          <div className="pl-3 border-l-2 border-[#D4A853] text-white/80 text-[15px] font-serif italic leading-relaxed">
            <TextoLatex texto={questao.comando} />
          </div>
        )}

        {/* Alternativas */}
        <div className="space-y-2">
          {LETRAS.map(l => {
            const texto = questao.alternativas?.[l]
            const imgAlt = questao.imagens_alternativas?.[l]
            if (!texto && !imgAlt) return null
            const acertouEssa = revelado && l === questao.gabarito
            const errouEssa   = revelado && l === resposta && l !== questao.gabarito

            return (
              <div key={l} onClick={() => selecionar(l)} className={classAlternativa(l)}>

                {/* Tesoura — oculta, aparece no hover */}
                {!revelado && (
                  <button
                    onClick={e => { e.stopPropagation(); toggleEliminar(l) }}
                    title={eliminadas.has(l) ? 'Restaurar' : 'Eliminar'}
                    className="opacity-0 group-hover/alt:opacity-100 shrink-0 p-1 rounded-md hover:bg-white/10 text-white/30 hover:text-white/70 transition mt-0.5"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
                      <line x1="20" y1="4" x2="8.12" y2="15.88"/>
                      <line x1="14.47" y1="14.48" x2="20" y2="20"/>
                      <line x1="8.12" y1="8.12" x2="12" y2="12"/>
                    </svg>
                  </button>
                )}

                {/* Letra */}
                <div className={`shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-[12px] font-bold transition ${letraClass(l)}`}>
                  {acertouEssa ? (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                  ) : errouEssa ? (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  ) : l}
                </div>

                {/* Texto */}
                <span className={`font-serif text-[14.5px] leading-relaxed flex-1 ${
                  acertouEssa ? 'text-emerald-100'
                  : errouEssa  ? 'text-rose-100'
                  : resposta === l && !revelado ? 'text-white'
                  : 'text-white/80'
                } ${eliminadas.has(l) && !revelado ? 'line-through' : ''}`}>
                  <TextoLatex texto={texto} />
                  {imgAlt && (
                    <img
                      src={`https://bmhudlpihwxvaelokugh.supabase.co/storage/v1/object/public/imagens-questoes/${imgAlt}`}
                      alt="" className="mt-2 max-w-xs rounded-lg border border-[#2C2820]"
                    />
                  )}
                </span>
              </div>
            )
          })}
        </div>

        {/* Barra de ações */}
        <div className="flex flex-wrap items-center gap-2.5 pt-1">
          {!revelado ? (
            <button
              onClick={revelar}
              disabled={!resposta}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-[13px] transition ${
                resposta
                  ? 'bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] shadow-lg shadow-[#D4A853]/30'
                  : 'bg-white/5 text-white/35 cursor-not-allowed border border-[#2C2820]'
              }`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
              Revelar resposta
            </button>
          ) : (
            <>
              {/* Badge resultado */}
              <div className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-[12.5px] font-semibold border ${
                acertou
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
              }`}>
                {acertou ? (
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                ) : (
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                )}
                {acertou ? 'Correto!' : `Gabarito: ${questao.gabarito}`}
              </div>

              {/* Explicar com IA */}
              <button
                onClick={explicar}
                disabled={explicLoading}
                className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-[#D4A853] to-amber-600 hover:opacity-90 disabled:opacity-50 text-[#0E0D0B] font-semibold text-[12.5px] transition shadow-lg shadow-[#D4A853]/20"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/></svg>
                {explicLoading ? 'Explicando…' : 'Explicar com IA'}
              </button>

              {/* Próxima (só na tela individual) */}
              {idProximo != null && (
                <Link
                  href={`/questoes/${idProximo}`}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-[#2C2820] text-white/85 font-semibold text-[12.5px] transition"
                >
                  Próxima
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                </Link>
              )}
            </>
          )}

          {questao.pagina_pdf != null && (
            <a
              href={urlPdf(questao.ano, questao.dia, questao.pagina_pdf)}
              target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-white/5 hover:bg-white/10 border border-[#2C2820] text-white/60 hover:text-white/90 text-[13px] px-4 py-2.5 rounded-xl transition"
            >
              📄 Ver no PDF
            </a>
          )}

          <button
            onClick={() => setModalReportar(true)}
            className="ml-auto text-white/20 hover:text-amber-400 text-[11px] transition"
          >
            ⚑ Reportar erro
          </button>
        </div>

        {/* Explicação IA */}
        {(explicacao || explicLoading) && (
          <div className="border-t border-[#2C2820] bg-gradient-to-b from-[#D4A853]/5 to-transparent -mx-5 sm:-mx-7 px-5 sm:px-7 py-5 anim-slide">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-md bg-gradient-to-br from-[#D4A853] to-amber-600 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/></svg>
              </div>
              <span className="text-[12px] font-semibold text-amber-300 uppercase tracking-wider">Explicação por IA</span>
              {explicLoading && <span className="text-[10px] text-white/35">gerando…</span>}
            </div>
            {/* Cursor de digitação animado durante streaming */}
            <div className={`prose-exato font-serif text-[14px] leading-[1.8] text-white/75 ${explicLoading ? 'typing-cursor' : ''}`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p:      ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-bold text-white/90">{children}</strong>,
                  em:     ({ children }) => <em className="italic text-white/80">{children}</em>,
                  ul:     ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                  ol:     ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                  li:     ({ children }) => <li className="text-white/75">{children}</li>,
                  h1:     ({ children }) => <h1 className="font-bold text-white/90 text-base mb-2 mt-4 first:mt-0">{children}</h1>,
                  h2:     ({ children }) => <h2 className="font-bold text-white/90 text-[14px] mb-2 mt-4 first:mt-0">{children}</h2>,
                  h3:     ({ children }) => <h3 className="font-semibold text-white/85 mb-1 mt-3 first:mt-0">{children}</h3>,
                  hr:     () => <hr className="border-white/10 my-3" />,
                }}
              >
                {explicacao}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>

      {modalReportar && (
        <ModalReportarErro
          questaoId={questao.id}
          ano={questao.ano}
          dia={questao.dia}
          numero={questao.numero}
          onFechar={() => setModalReportar(false)}
        />
      )}
    </article>
  )
}
