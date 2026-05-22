'use client'

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'

interface Props {
  simuladoId: number
  nQuestoes:  number
  gabarito:   Record<number, string>   // seq → letra correta
  questaoIds: number[]                  // ids no Supabase (por seq)
}

interface ResultadoMicro {
  sucesso:       boolean
  respostas:     (string | null)[]
  n_marcadas:    number
  n_ambiguas:    number
  conf_media:    number
  confiancas:    number[]
  erro?:         string
}

const LETRAS = ['A', 'B', 'C', 'D', 'E']

export default function CorrigirFolha({ simuladoId, nQuestoes, gabarito, questaoIds }: Props) {
  const router                   = useRouter()
  const inputRef                 = useRef<HTMLInputElement>(null)
  const [preview, setPreview]    = useState<string | null>(null)
  const [arquivo, setArquivo]    = useState<File | null>(null)
  const [status, setStatus]      = useState<'idle' | 'uploading' | 'ok' | 'erro'>('idle')
  const [resultado, setResultado]= useState<ResultadoMicro | null>(null)
  const [subErro, setSubErro]    = useState('')

  const onFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return
    setArquivo(file)
    setStatus('idle')
    setResultado(null)
    const url = URL.createObjectURL(file)
    setPreview(url)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }, [onFile])

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFile(file)
  }

  async function enviar() {
    if (!arquivo) return
    setStatus('uploading')
    setSubErro('')

    const fd = new FormData()
    fd.append('file', arquivo)
    fd.append('simulado_id', String(simuladoId))
    fd.append('n_questoes', String(nQuestoes))

    try {
      const resp = await fetch('/api/corrigir', { method: 'POST', body: fd })
      const data = await resp.json()

      if (!resp.ok || !data.sucesso) {
        setStatus('erro')
        setSubErro(data.erro ?? 'Falha desconhecida')
        return
      }

      setResultado(data)
      setStatus('ok')
    } catch {
      setStatus('erro')
      setSubErro('Erro de rede. Verifique sua conexão.')
    }
  }

  // Calcula resultado
  const acertos = resultado
    ? resultado.respostas.filter((r, i) => r && gabarito[i + 1] && r === gabarito[i + 1]).length
    : 0
  const pct = resultado ? Math.round((acertos / nQuestoes) * 100) : 0

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-5">

      {/* Drop zone */}
      {status !== 'ok' && (
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className="relative rounded-2xl border-2 border-dashed border-[#2C2820] hover:border-[#D4A853]/50 bg-[#161411] transition cursor-pointer overflow-hidden"
          style={{ minHeight: 180 }}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={onChange}
            className="absolute inset-0 opacity-0 cursor-pointer"
            style={{ zIndex: -1 }}
          />

          {preview ? (
            // Pré-visualização da imagem
            <div className="flex flex-col items-center p-4 gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={preview}
                alt="Folha de respostas"
                className="max-h-48 rounded-xl object-contain border border-[#2C2820]"
              />
              <p className="text-xs text-white/40">
                {arquivo?.name} · Clique para trocar
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 py-10 px-6 text-center">
              <div className="w-12 h-12 rounded-2xl bg-[#D4A853]/10 border border-[#D4A853]/20 flex items-center justify-center">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-[#D4A853]">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-white/80">
                  Arraste a foto aqui ou clique para selecionar
                </p>
                <p className="text-xs text-white/35 mt-1">
                  JPEG ou PNG · Resolução mínima recomendada: 1000×1400 px
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Dicas de foto */}
      {!preview && (
        <div className="rounded-xl bg-[#161411] border border-[#2C2820] p-4">
          <p className="text-xs font-semibold text-white/60 mb-2">📸 Como fotografar bem</p>
          <ul className="space-y-1 text-xs text-white/40">
            <li>• Todos os 4 cantos da folha devem estar visíveis</li>
            <li>• Iluminação uniforme, sem sombras fortes sobre as bolinhas</li>
            <li>• Folha flat sobre superfície plana (não dobrada)</li>
            <li>• Foto de cima, não de lado (evite perspectiva extrema)</li>
          </ul>
        </div>
      )}

      {/* Botão enviar */}
      {arquivo && status !== 'ok' && (
        <button
          onClick={enviar}
          disabled={status === 'uploading'}
          className="w-full py-3 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] disabled:opacity-50 text-[#0E0D0B] font-semibold text-sm transition flex items-center justify-center gap-2"
        >
          {status === 'uploading' ? (
            <>
              <span className="w-4 h-4 border-2 border-[#0E0D0B]/30 border-t-[#0E0D0B] rounded-full animate-spin" />
              Analisando folha…
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Corrigir folha
            </>
          )}
        </button>
      )}

      {/* Erro */}
      {status === 'erro' && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3">
          <p className="text-sm font-semibold text-red-400 mb-1">Não foi possível corrigir</p>
          <p className="text-xs text-red-300/70">{subErro}</p>
          <button
            onClick={() => setStatus('idle')}
            className="mt-2 text-xs text-red-400 underline"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Resultado */}
      {status === 'ok' && resultado && (
        <div className="space-y-4">

          {/* Card principal */}
          <div className="rounded-2xl bg-[#161411] border border-[#2C2820] p-6 text-center">
            <div className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-amber-300 to-[#D4A853] bg-clip-text text-transparent mb-1">
              {pct}%
            </div>
            <div className="text-sm text-white/45 mb-4">
              {acertos} acertos de {nQuestoes} questões
            </div>
            <div className="h-2 rounded-full bg-white/[0.08] overflow-hidden max-w-xs mx-auto">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#D4A853] to-amber-600"
                style={{ width: `${pct}%` }}
              />
            </div>

            {resultado.n_ambiguas > 0 && (
              <p className="text-xs text-amber-400/70 mt-3">
                ⚠ {resultado.n_ambiguas} questão(ões) com resposta ambígua (confiança baixa)
              </p>
            )}
            {resultado.n_marcadas < nQuestoes && (
              <p className="text-xs text-white/40 mt-1">
                {nQuestoes - resultado.n_marcadas} questão(ões) não identificadas
              </p>
            )}
          </div>

          {/* Tabela de respostas */}
          <div className="rounded-xl bg-[#161411] border border-[#2C2820] overflow-hidden">
            <div className="px-4 py-3 border-b border-[#2C2820]">
              <p className="text-xs font-semibold text-white/60 uppercase tracking-wider">Respostas detectadas</p>
            </div>
            <div className="grid grid-cols-5 sm:grid-cols-10 divide-x divide-y divide-[#2C2820]/60">
              {resultado.respostas.map((r, i) => {
                const correto  = gabarito[i + 1]
                const acertou  = r && correto && r === correto
                const errou    = r && correto && r !== correto
                const conf     = resultado.confiancas[i] ?? 0

                return (
                  <div key={i} className="flex flex-col items-center py-2 px-1">
                    <span className="text-[9px] text-white/30 mb-0.5">{i + 1}</span>
                    <span className={`text-sm font-bold ${
                      acertou ? 'text-emerald-400' :
                      errou   ? 'text-red-400'     : 'text-white/50'
                    }`}>
                      {r ?? '—'}
                    </span>
                    {correto && r !== correto && (
                      <span className="text-[8px] text-white/30">{correto}</span>
                    )}
                    {conf > 0 && conf < 0.6 && (
                      <span className="text-[7px] text-amber-400/60">?</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Ações */}
          <div className="flex gap-3 flex-wrap">
            <button
              onClick={() => router.push('/tira-teima')}
              className="px-4 py-2.5 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] font-semibold text-sm transition"
            >
              📓 Ver Tira Teima
            </button>
            <button
              onClick={() => { setStatus('idle'); setPreview(null); setArquivo(null); setResultado(null) }}
              className="px-4 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-[#2C2820] text-white/70 font-semibold text-sm transition"
            >
              Corrigir outra folha
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
