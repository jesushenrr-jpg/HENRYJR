'use client'

import { useEffect } from 'react'

interface Alternativas { A: string; B: string; C: string; D: string; E: string }
interface Questao {
  id: number; numero: number; ano: number; dia: string; area: string
  enunciado: string[]; comando: string | null
  alternativas: Alternativas; gabarito: string | null; anulada?: boolean
}
interface SimInfo { id: number; total: number; iniciado_em: string }

interface Props {
  questoes: Record<string, unknown>[]
  simulado: SimInfo
}

const AREAS: Record<string, string> = {
  'Linguagens, Codigos e suas Tecnologias':    'Linguagens',
  'Ciencias Humanas e suas Tecnologias':       'Humanas',
  'Ciencias da Natureza e suas Tecnologias':   'C. Natureza',
  'Matematica e suas Tecnologias':             'Matemática',
}

export default function ImprimirClient({ questoes, simulado }: Props) {
  const qs = questoes as unknown as Questao[]

  useEffect(() => {
    // Pequeno delay para garantir que o CSS de print carregou
    const t = setTimeout(() => window.print(), 800)
    return () => clearTimeout(t)
  }, [])

  const data = new Date(simulado.iniciado_em).toLocaleDateString('pt-BR')

  return (
    <>
      {/* Barra de controle — some na impressão */}
      <div className="no-print fixed top-0 left-0 right-0 z-50 bg-[#161411] border-b border-[#2C2820] px-6 py-3 flex items-center justify-between">
        <span className="text-sm text-white/60">
          Simulado #{simulado.id} · {qs.length} questões
        </span>
        <div className="flex gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-1.5 rounded-lg bg-[#D4A853] text-[#0E0D0B] text-sm font-bold"
          >
            🖨️ Imprimir / Salvar PDF
          </button>
          <button
            onClick={() => window.close()}
            className="px-4 py-1.5 rounded-lg bg-white/10 text-white/70 text-sm"
          >
            Fechar
          </button>
        </div>
      </div>

      {/* Conteúdo imprimível */}
      <div className="print-body pt-14">

        {/* Cabeçalho */}
        <div className="print-header">
          <div className="print-header-title">HenryJr — Simulado ENEM</div>
          <div className="print-header-sub">
            Simulado #{simulado.id} · {qs.length} questões · {data}
          </div>
          <div className="print-header-sub">
            Nome: ______________________________ &nbsp;&nbsp; Data: ___/___/______
          </div>
        </div>

        {/* Questões */}
        {qs.map((q, idx) => (
          <div key={q.id} className="print-questao">
            <div className="print-questao-num">
              Questão {idx + 1}
              <span className="print-questao-meta">
                ENEM {q.ano} · {AREAS[q.area] ?? q.area}
                {q.anulada && ' · ANULADA'}
              </span>
            </div>

            {/* Enunciado */}
            {q.enunciado?.map((p, i) => (
              <p key={i} className="print-enunciado">{p}</p>
            ))}
            {q.comando && <p className="print-comando">{q.comando}</p>}

            {/* Alternativas */}
            <div className="print-alts">
              {(['A','B','C','D','E'] as const).map(letra => (
                q.alternativas?.[letra] && (
                  <div key={letra} className="print-alt">
                    <span className="print-alt-letra">{letra}</span>
                    <span className="print-alt-texto">{q.alternativas[letra]}</span>
                  </div>
                )
              ))}
            </div>
          </div>
        ))}

        {/* Folha de respostas */}
        <div className="print-folha">
          <div className="print-folha-titulo">FOLHA DE RESPOSTAS</div>
          <div className="print-folha-grid">
            {qs.map((_, idx) => (
              <div key={idx} className="print-folha-linha">
                <span className="print-folha-num">{String(idx + 1).padStart(2, '0')}</span>
                {['A','B','C','D','E'].map(l => (
                  <span key={l} className="print-bolinha">{l}</span>
                ))}
              </div>
            ))}
          </div>
        </div>

      </div>

      <style>{`
        @media print {
          .no-print { display: none !important; }
          .print-body { padding-top: 0 !important; }
          body { background: white !important; color: black !important; }
        }

        .print-body {
          max-width: 800px;
          margin: 0 auto;
          padding: 24px;
          font-family: Georgia, serif;
          color: #111;
          background: white;
        }

        .print-header {
          text-align: center;
          border-bottom: 2px solid #000;
          padding-bottom: 12px;
          margin-bottom: 24px;
        }
        .print-header-title { font-size: 20px; font-weight: bold; }
        .print-header-sub { font-size: 12px; color: #555; margin-top: 4px; }

        .print-questao {
          margin-bottom: 28px;
          page-break-inside: avoid;
          border-bottom: 1px solid #ddd;
          padding-bottom: 20px;
        }
        .print-questao-num {
          font-size: 13px;
          font-weight: bold;
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .print-questao-meta {
          font-weight: normal;
          font-size: 11px;
          color: #777;
        }
        .print-enunciado {
          font-size: 13px;
          line-height: 1.6;
          margin-bottom: 6px;
          color: #222;
        }
        .print-comando {
          font-size: 13px;
          font-weight: bold;
          margin: 8px 0;
          color: #111;
        }
        .print-alts { margin-top: 10px; }
        .print-alt {
          display: flex;
          gap: 8px;
          align-items: flex-start;
          margin-bottom: 5px;
          font-size: 13px;
        }
        .print-alt-letra {
          font-weight: bold;
          min-width: 18px;
          color: #333;
        }
        .print-alt-texto { color: #222; line-height: 1.5; }

        .print-folha {
          page-break-before: always;
          margin-top: 32px;
        }
        .print-folha-titulo {
          text-align: center;
          font-size: 16px;
          font-weight: bold;
          border: 2px solid #000;
          padding: 8px;
          margin-bottom: 20px;
        }
        .print-folha-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 8px;
        }
        .print-folha-linha {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 12px;
        }
        .print-folha-num {
          font-weight: bold;
          min-width: 22px;
          font-size: 11px;
        }
        .print-bolinha {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 20px;
          height: 20px;
          border: 1.5px solid #333;
          border-radius: 50%;
          font-size: 10px;
          font-weight: bold;
          cursor: default;
        }
      `}</style>
    </>
  )
}
