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
  'Linguagens, Codigos e suas Tecnologias':    'Linguagens e Códigos',
  'Ciencias Humanas e suas Tecnologias':       'Ciências Humanas',
  'Ciencias da Natureza e suas Tecnologias':   'Ciências da Natureza',
  'Matematica e suas Tecnologias':             'Matemática',
}

export default function ImprimirClient({ questoes, simulado }: Props) {
  const qs = questoes as unknown as Questao[]

  useEffect(() => {
    const t = setTimeout(() => window.print(), 900)
    return () => clearTimeout(t)
  }, [])

  const data = new Date(simulado.iniciado_em).toLocaleDateString('pt-BR')

  // Divide em 2 colunas como o ENEM
  const col1 = qs.filter((_, i) => i % 2 === 0)
  const col2 = qs.filter((_, i) => i % 2 === 1)

  return (
    <>
      {/* Barra de controle — oculta na impressão */}
      <div className="no-print">
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
          background: '#161411', borderBottom: '1px solid #2C2820',
          padding: '10px 24px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14 }}>
            Simulado #{simulado.id} · {qs.length} questões
          </span>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={() => window.print()} style={{
              background: '#D4A853', color: '#0E0D0B', border: 'none',
              borderRadius: 8, padding: '6px 18px', fontWeight: 700,
              fontSize: 13, cursor: 'pointer',
            }}>
              🖨️ Imprimir / Salvar PDF
            </button>
            <button onClick={() => window.close()} style={{
              background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.7)',
              border: 'none', borderRadius: 8, padding: '6px 14px',
              fontSize: 13, cursor: 'pointer',
            }}>
              Fechar
            </button>
          </div>
        </div>
      </div>

      {/* ── CONTEÚDO IMPRIMÍVEL ── */}
      <div className="caderno">

        {/* ── CAPA / CABEÇALHO ── */}
        <div className="capa">
          <div className="capa-logo">HENRYJR</div>
          <div className="capa-titulo">Simulado ENEM</div>
          <div className="capa-sub">
            Simulado #{simulado.id} &nbsp;·&nbsp; {qs.length} questões &nbsp;·&nbsp; {data}
          </div>
          <div className="capa-campos">
            <div className="campo">
              <span className="campo-label">NOME</span>
              <span className="campo-linha" />
            </div>
            <div className="campo campo-sm">
              <span className="campo-label">DATA</span>
              <span className="campo-linha" />
            </div>
          </div>
          <div className="capa-instrucoes">
            <strong>INSTRUÇÕES:</strong> Leia atentamente cada questão. Marque apenas uma alternativa por questão
            na Folha de Respostas (última página). Use caneta azul ou preta para preencher completamente a bolinha.
          </div>
        </div>

        {/* ── QUESTÕES em 2 colunas ── */}
        <div className="questoes-wrap">
          <div className="coluna">
            {col1.map((q, idx) => (
              <QuestaoCard key={q.id} q={q} num={idx * 2 + 1} />
            ))}
          </div>
          <div className="separador-vertical" />
          <div className="coluna">
            {col2.map((q, idx) => (
              <QuestaoCard key={q.id} q={q} num={idx * 2 + 2} />
            ))}
          </div>
        </div>

        {/* ── FOLHA DE RESPOSTAS ── */}
        <div className="folha-respostas">
          <div className="folha-header">
            <div className="folha-titulo">FOLHA DE RESPOSTAS</div>
            <div className="folha-sub">Preencha completamente a bolinha da alternativa escolhida</div>
          </div>

          <div className="folha-campos">
            <div className="folha-campo">
              NOME: <span className="folha-linha" />
            </div>
            <div className="folha-campo folha-campo-sm">
              DATA: <span className="folha-linha" />
            </div>
          </div>

          <div className="folha-grid">
            {qs.map((q, idx) => (
              <div key={q.id} className="folha-item">
                <span className="folha-num">{String(idx + 1).padStart(2, '0')}</span>
                {['A','B','C','D','E'].map(l => (
                  <span key={l} className="bolinha">{l}</span>
                ))}
              </div>
            ))}
          </div>

          <div className="folha-rodape">
            HenryJr · Banco de Questões ENEM · henryjr.vercel.app
          </div>
        </div>

      </div>

      {/* ── ESTILOS ── */}
      <style>{`
        /* Remove cabeçalho/rodapé do browser na impressão */
        @page {
          size: A4;
          margin: 14mm 12mm 14mm 12mm;
        }

        @media print {
          .no-print { display: none !important; }
          html, body { background: white !important; }

          /* Oculta toda a interface do site */
          header, nav, footer, [class*="NavBar"],
          [class*="MobileTab"], [class*="layout"] > *:not(.caderno) {
            display: none !important;
          }

          .caderno { padding-top: 0 !important; }

          /* Quebra de página antes da folha */
          .folha-respostas { page-break-before: always; }

          /* Evita quebra no meio de questão */
          .questao { page-break-inside: avoid; }

          /* Colunas lado a lado no print */
          .questoes-wrap {
            display: flex !important;
            flex-direction: row !important;
          }
        }

        /* ── Base ── */
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body { background: #f0f0f0; }

        .caderno {
          max-width: 210mm;
          margin: 0 auto;
          background: white;
          font-family: 'Times New Roman', Times, serif;
          font-size: 11pt;
          color: #111;
          padding-top: 52px; /* espaço para barra de controle */
        }

        /* ── Capa ── */
        .capa {
          padding: 20px 20px 16px;
          border-bottom: 3px solid #000;
          margin-bottom: 0;
        }
        .capa-logo {
          font-family: Arial, sans-serif;
          font-size: 9pt;
          font-weight: 900;
          letter-spacing: 4px;
          color: #B8882A;
          margin-bottom: 2px;
        }
        .capa-titulo {
          font-size: 20pt;
          font-weight: bold;
          letter-spacing: 1px;
          line-height: 1;
          margin-bottom: 4px;
        }
        .capa-sub {
          font-size: 9pt;
          color: #555;
          margin-bottom: 12px;
        }
        .capa-campos {
          display: flex;
          gap: 16px;
          margin-bottom: 10px;
        }
        .campo {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          border-bottom: 1.5px solid #333;
          padding-bottom: 2px;
        }
        .campo-sm { flex: 0 0 120px; }
        .campo-label {
          font-size: 8pt;
          font-weight: bold;
          letter-spacing: 1px;
          color: #555;
          white-space: nowrap;
        }
        .campo-linha { flex: 1; }

        .capa-instrucoes {
          font-size: 8.5pt;
          color: #444;
          background: #f8f8f8;
          border-left: 3px solid #B8882A;
          padding: 6px 10px;
          line-height: 1.5;
        }

        /* ── Questões ── */
        .questoes-wrap {
          display: flex;
          flex-direction: row;
          align-items: flex-start;
          padding: 0;
        }
        .coluna {
          flex: 1;
          padding: 12px 14px;
        }
        .separador-vertical {
          width: 1px;
          background: #ccc;
          align-self: stretch;
          margin: 12px 0;
        }

        .questao {
          margin-bottom: 18px;
          padding-bottom: 14px;
          border-bottom: 1px solid #ddd;
        }
        .questao:last-child { border-bottom: none; }

        .q-header {
          display: flex;
          align-items: baseline;
          gap: 8px;
          margin-bottom: 6px;
        }
        .q-num {
          font-size: 10pt;
          font-weight: bold;
          font-family: Arial, sans-serif;
          color: #000;
          white-space: nowrap;
        }
        .q-meta {
          font-size: 8pt;
          color: #777;
          font-family: Arial, sans-serif;
        }
        .q-anulada {
          font-size: 8pt;
          color: #c00;
          font-weight: bold;
        }

        .q-enunciado {
          font-size: 10pt;
          line-height: 1.55;
          color: #222;
          margin-bottom: 4px;
          text-align: justify;
        }
        .q-fonte {
          font-size: 8.5pt;
          color: #666;
          font-style: italic;
          margin-bottom: 4px;
        }
        .q-comando {
          font-size: 10pt;
          font-weight: bold;
          line-height: 1.5;
          color: #111;
          margin: 8px 0 6px;
          text-align: justify;
        }

        .q-alts { margin-top: 4px; }
        .q-alt {
          display: flex;
          gap: 6px;
          align-items: flex-start;
          margin-bottom: 3px;
          font-size: 10pt;
          line-height: 1.45;
        }
        .q-alt-letra {
          font-weight: bold;
          min-width: 14px;
          color: #000;
          font-family: Arial, sans-serif;
          padding-top: 1px;
        }
        .q-alt-texto {
          color: #222;
          text-align: justify;
        }

        /* ── Folha de Respostas ── */
        .folha-respostas {
          padding: 20px 20px 16px;
          border-top: 3px solid #000;
          margin-top: 8px;
          min-height: 160mm;
        }
        .folha-header {
          text-align: center;
          margin-bottom: 14px;
        }
        .folha-titulo {
          font-family: Arial, sans-serif;
          font-size: 14pt;
          font-weight: 900;
          letter-spacing: 3px;
          border: 2px solid #000;
          display: inline-block;
          padding: 6px 24px;
          margin-bottom: 4px;
        }
        .folha-sub {
          font-size: 8.5pt;
          color: #666;
          font-family: Arial, sans-serif;
        }

        .folha-campos {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;
        }
        .folha-campo {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 9pt;
          font-family: Arial, sans-serif;
          font-weight: bold;
          border-bottom: 1.5px solid #333;
          padding-bottom: 2px;
        }
        .folha-campo-sm { flex: 0 0 130px; }
        .folha-linha { flex: 1; }

        .folha-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 6px 12px;
          margin-bottom: 20px;
        }
        .folha-item {
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .folha-num {
          font-family: Arial, sans-serif;
          font-size: 9pt;
          font-weight: bold;
          min-width: 22px;
          text-align: right;
          color: #333;
        }
        .bolinha {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 18px;
          height: 18px;
          border: 1.5px solid #333;
          border-radius: 50%;
          font-size: 8pt;
          font-weight: bold;
          font-family: Arial, sans-serif;
          color: #333;
          flex-shrink: 0;
        }

        .folha-rodape {
          text-align: center;
          font-size: 8pt;
          color: #aaa;
          font-family: Arial, sans-serif;
          margin-top: 24px;
          border-top: 1px solid #eee;
          padding-top: 8px;
        }
      `}</style>
    </>
  )
}

function QuestaoCard({ q, num }: { q: Questao; num: number }) {
  const area = AREAS[q.area] ?? q.area

  return (
    <div className="questao">
      <div className="q-header">
        <span className="q-num">QUESTÃO {String(num).padStart(2, '0')}</span>
        <span className="q-meta">ENEM {q.ano} · {area}</span>
        {q.anulada && <span className="q-anulada">ANULADA</span>}
      </div>

      {q.enunciado?.map((p, i) => {
        // Detecta linha de fonte/referência (itálico — geralmente mais curta e com padrões)
        const isFonte = p.length < 120 && (
          p.includes('Disponível') || p.includes('Acesso em') ||
          /^[A-Z]{2,}[\.,]/.test(p) || p.startsWith('Fonte:')
        )
        return isFonte
          ? <p key={i} className="q-fonte">{p}</p>
          : <p key={i} className="q-enunciado">{p}</p>
      })}

      {q.comando && <p className="q-comando">{q.comando}</p>}

      <div className="q-alts">
        {(['A','B','C','D','E'] as const).map(letra =>
          q.alternativas?.[letra] ? (
            <div key={letra} className="q-alt">
              <span className="q-alt-letra">{letra}</span>
              <span className="q-alt-texto">{q.alternativas[letra]}</span>
            </div>
          ) : null
        )}
      </div>
    </div>
  )
}
