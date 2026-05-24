'use client'
import { useEffect, useState } from 'react'

/* ── Tipos ── */
interface Alternativas { A: string; B: string; C: string; D: string; E: string }
interface Questao {
  id: number; numero: number; ano: number; dia: string; area: string
  enunciado: string[]; comando: string | null
  alternativas: Alternativas; gabarito: string | null; anulada?: boolean
}
interface SimInfo { id: number; total: number; iniciado_em: string }
interface Props { questoes: Record<string, unknown>[]; simulado: SimInfo }

/* ── Constantes ── */
const AREA_ORDER = [
  'Linguagens, Codigos e suas Tecnologias',
  'Ciencias Humanas e suas Tecnologias',
  'Ciencias da Natureza e suas Tecnologias',
  'Matematica e suas Tecnologias',
]
const AREA_LABEL: Record<string, string> = {
  'Linguagens, Codigos e suas Tecnologias':  'Linguagens, Códigos e suas Tecnologias',
  'Ciencias Humanas e suas Tecnologias':     'Ciências Humanas e suas Tecnologias',
  'Ciencias da Natureza e suas Tecnologias': 'Ciências da Natureza e suas Tecnologias',
  'Matematica e suas Tecnologias':           'Matemática e suas Tecnologias',
}
const AREA_COLOR: Record<string, string> = {
  'Linguagens, Codigos e suas Tecnologias':  '#0077B6',
  'Ciencias Humanas e suas Tecnologias':     '#B45309',
  'Ciencias da Natureza e suas Tecnologias': '#166534',
  'Matematica e suas Tecnologias':           '#5B21B6',
}

/* Frases — substituir pelas oficiais do ENEM quando disponíveis */
const FRASES = [
  'O sucesso é a soma de pequenos esforços repetidos dia após dia.',
  'O conhecimento é a única riqueza que ninguém pode tirar de você.',
  'Estudar hoje é investir no seu amanhã.',
  'O futuro pertence àqueles que acreditam na beleza de seus sonhos.',
  'A educação é o passaporte para o futuro de quem deseja ir mais longe.',
  'Cada questão resolvida é um passo a mais rumo ao seu objetivo.',
  'Persistência é o caminho do êxito.',
  'O esforço de hoje é o resultado de amanhã.',
]

/* ── Barcode CSS puro (sem Unicode) ── */
function Barcode({ width = 150, height = 9, id = '' }: { width?: number; height?: number; id?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <div style={{
        width, height,
        background: `repeating-linear-gradient(
          90deg,
          #111 0px,   #111 2px,
          white  2px, white  4px,
          #111   4px, #111   7px,
          white  7px, white  8px,
          #111   8px, #111  10px,
          white 10px, white 12px,
          #111  12px, #111  14px,
          white 14px, white 17px,
          #111  17px, #111  18px,
          white 18px, white 21px,
          #111  21px, #111  24px,
          white 24px, white 25px
        )`,
        flexShrink: 0,
      }} />
      {id && (
        <div style={{
          fontFamily: "'Courier New', monospace",
          fontSize: 5.5,
          letterSpacing: 1.5,
          color: '#444',
          textAlign: 'center',
          lineHeight: 1,
        }}>
          *{id.padStart(7, '0')}*
        </div>
      )}
    </div>
  )
}

export default function ImprimirClient({ questoes, simulado }: Props) {
  const qs      = questoes as unknown as Questao[]
  const ano     = new Date().getFullYear()
  const data    = new Date(simulado.iniciado_em).toLocaleDateString('pt-BR')
  const frase   = FRASES[simulado.id % FRASES.length]
  const [baixando, setBaixando] = useState(false)
  const [erroDown, setErroDown] = useState('')

  async function baixarPDF() {
    setBaixando(true)
    setErroDown('')
    try {
      const res = await fetch(`/api/pdf/simulado/${simulado.id}`)
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.error || `HTTP ${res.status}`)
      }
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `simulado-${simulado.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erro ao baixar PDF'
      setErroDown(msg)
    } finally {
      setBaixando(false)
    }
  }

  /* Ordena por área (ordem ENEM) → ano → número */
  const sorted = [...qs].sort((a, b) => {
    const ia = AREA_ORDER.indexOf(a.area), ib = AREA_ORDER.indexOf(b.area)
    if (ia !== ib) return ia - ib
    if (a.ano !== b.ano) return a.ano - b.ano
    return a.numero - b.numero
  })

  /* Agrupa por área com numeração sequencial */
  type QN    = { q: Questao; num: number }
  type Grupo = { area: string; items: QN[] }
  const grupos: Grupo[] = []
  let counter = 1
  for (const q of sorted) {
    const last = grupos[grupos.length - 1]
    if (last && last.area === q.area) last.items.push({ q, num: counter++ })
    else grupos.push({ area: q.area, items: [{ q, num: counter++ }] })
  }

  useEffect(() => {
    /* ?view=1 → só visualiza sem disparar impressão (usado para inspeção) */
    const params = new URLSearchParams(window.location.search)
    if (params.get('view') === '1') return
    const t = setTimeout(() => window.print(), 900)
    return () => clearTimeout(t)
  }, [])

  return (
    <>
      {/* ─── BARRA DE CONTROLE (só na tela) ─── */}
      <div className="ctrl no-print">
        <div className="ctrl-info">
          <strong>Simulado #{simulado.id}</strong>&nbsp;·&nbsp;{qs.length} questões
        </div>
        <div className="ctrl-tip">
          ⚠️ No diálogo de impressão: desative <em>Cabeçalhos e rodapés</em> do navegador
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {erroDown && (
            <span style={{ fontSize: 11, color: '#f87171' }}>{erroDown}</span>
          )}
          <button
            className="btn-dl"
            onClick={baixarPDF}
            disabled={baixando}
            title="Gera o PDF no servidor (sem diálogo do navegador)"
          >
            {baixando ? '⏳ Gerando…' : '⬇️ Baixar PDF'}
          </button>
          <button className="btn-imp" onClick={() => window.print()}>🖨️ Imprimir / Salvar PDF</button>
          <button className="btn-fch" onClick={() => window.close()}>✕ Fechar</button>
        </div>
      </div>

      {/* ─── CABEÇALHO FIXO ───
           top: -14mm empurra o elemento para dentro do espaço físico da margem (@page margin-top: 14mm).
           Com top: 0, o elemento ficaria no TOPO da área de conteúdo e cobriria texto em todas as páginas.
           Com top: -14mm, o elemento ocupa exatamente o espaço da margem, sem nenhuma sobreposição. ── */}
      <div className="pg-head">
        <div className="ph-inner">
          <div className="ph-left">
            <Barcode width={150} height={8} id={String(simulado.id)} />
          </div>
          <div className="ph-right">
            <span className="ph-h">henryjr</span>
            <span className="ph-y">{ano}</span>
            <span className="ph-sub">Banco de Questões · Simulado ENEM</span>
          </div>
        </div>
        <div className="ph-dash" />
      </div>

      {/* ─── RODAPÉ FIXO ───
           bottom: -12mm empurra para o espaço físico da margem inferior (@page margin-bottom: 12mm). ── */}
      <div className="pg-foot">
        <div className="pf-dash" />
        <div className="pf-inner">
          <span>Simulado #{simulado.id} · {data}</span>
          <span className="pf-center">SIMULADO ENEM · HENRYJR · henryjr.vercel.app</span>
          <span className="pf-logo">henryjr{ano}</span>
        </div>
      </div>

      {/* ══════════ CADERNO ══════════ */}
      <div className="caderno">

        {/* ══ CAPA ══ */}
        <div className="capa">

          {/* Faixa azul */}
          <div className="capa-azul">
            <div className="ca-t1">BANCO DE QUESTÕES ENEM</div>
            <div className="ca-t2">SIMULADO PERSONALIZADO</div>
            <div className="ca-areas">
              {grupos.map(g => (
                <div key={g.area} className="ca-ar">{AREA_LABEL[g.area] ?? g.area}</div>
              ))}
            </div>
          </div>

          {/* Logo + número */}
          <div className="capa-mid">
            <div className="cm-logo">
              <span className="cm-h">henryjr</span>
              <span className="cm-y">{ano}</span>
            </div>
            <div className="cm-box">
              <div className="cm-label">SIMULADO</div>
              <div className="cm-num">#{simulado.id}</div>
              <div className="cm-qtd">{qs.length} QUESTÕES</div>
              <div className="cm-data">{data}</div>
            </div>
          </div>

          {/* Faixa de cores */}
          <div className="capa-strip">
            {Array.from({ length: 100 }).map((_, i) => (
              <div key={i} className="cs-c" style={{
                background: ['#0077B6','#009AC7','#00B4D8','#B45309','#166534','#5B21B6','#B8882A','#D4A853'][i % 8]
              }} />
            ))}
          </div>

          {/* Frase */}
          <div className="capa-frase">
            <div className="cf-label">
              ATENÇÃO: transcreva no espaço do seu CARTÃO-RESPOSTA, com sua caligrafia usual:
            </div>
            <div className="cf-box">
              <em className="cf-texto">{frase}</em>
            </div>
          </div>

          {/* Instruções */}
          <div className="capa-inst">
            <div className="ci-titulo">LEIA ATENTAMENTE AS INSTRUÇÕES SEGUINTES:</div>
            <ol className="ci-lista">
              <li>
                Este CADERNO DE QUESTÕES contém <strong>{qs.length} questões</strong> numeradas de 01 a{' '}
                {String(qs.length).padStart(2,'0')},{' '}
                {grupos.length > 1
                  ? `distribuídas em ${grupos.length} áreas de conhecimento`
                  : `pertencentes à área de ${AREA_LABEL[grupos[0]?.area]?.split(' e')[0] ?? 'conhecimento'}`}.
              </li>
              <li>Confira a quantidade e a ordem das questões antes de iniciar.</li>
              <li>
                Para cada questão são apresentadas <strong>5 alternativas</strong> (A, B, C, D, E).
                Apenas <strong>uma</strong> responde corretamente à questão proposta.
              </li>
              <li>
                Marque suas respostas na <strong>Folha de Respostas</strong> (última página),
                usando caneta <strong>azul ou preta</strong>.
              </li>
              <li>
                Preencha <strong>completamente</strong> o círculo. Não use lápis nem corretivo.
              </li>
              <li>
                Tempo sugerido: aproximadamente <strong>{Math.round(qs.length * 3)} minutos</strong>.
              </li>
              <li>Rascunhos neste caderno não serão considerados na correção.</li>
            </ol>
          </div>

          {/* Rodapé da capa */}
          <div className="capa-rod">
            <div className="cr-l">
              <span className="cr-marca">HENRYJR</span>
              <span className="cr-sub">Banco de Questões ENEM</span>
            </div>
            <div className="cr-c">henryjr.vercel.app</div>
            <div className="cr-r">
              <Barcode width={100} height={8} />
            </div>
          </div>

        </div>{/* /capa */}

        {/* ══ QUESTÕES por área ══
         *
         * ORDEM VERTICAL correta:
         *   col1 = primeiras ceil(n/2) questões → coluna ESQUERDA
         *   col2 = restantes                    → coluna DIREITA
         *
         *   Com um único questoes-wrap por área:
         *     col1 = [Q1, Q2, Q3]  col2 = [Q4, Q5, Q6]
         *     → Q1 e Q2 ficam ambas na coluna esquerda (vertical ✓)
         *
         *   A separação em dois questoes-wrap (area-start + rest) criava:
         *     linha 1: [Q1 esq | Q3 dir]   linha 2: [Q2 esq | Q4 dir]
         *     → leitura horizontal (Q1, Q3, Q2, Q4) ← BUG corrigido
         *
         * CABEÇALHO DE ÁREA não fica órfão:
         *   break-after: avoid em .area-head impede quebra de página logo após o título.
         *   Não usamos mais area-start com break-inside (era grande demais e ignorado pelo Chrome).
         ══*/}
        {grupos.map(({ area, items }) => {
          const cor   = AREA_COLOR[area] ?? '#333'
          const label = AREA_LABEL[area] ?? area
          const start = items[0].num
          const end   = items[items.length - 1].num

          /* ORDEM VERTICAL: col1 = primeiras ceil(n/2), col2 = restantes */
          const half = Math.ceil(items.length / 2)
          const col1 = items.slice(0, half)
          const col2 = items.slice(half)

          return (
            <div key={area} className="area-bloco">

              {/* Cabeçalho — break-after: avoid garante que nunca fica sozinho no fim da página */}
              <div className="area-head" style={{ borderBottomColor: cor }}>
                <div className="ah-nome" style={{ color: cor }}>{label.toUpperCase()}</div>
                <div className="ah-range">
                  Questões de {String(start).padStart(2,'0')} a {String(end).padStart(2,'0')}
                </div>
              </div>

              {/* UM único questoes-wrap: col1 inteira à esquerda, col2 inteira à direita */}
              <div className="questoes-wrap">
                <div className="coluna">
                  {col1.map(({ q, num }) => <QuestaoCard key={q.id} q={q} num={num} />)}
                </div>
                <div className="sep-v" />
                <div className="coluna">
                  {col2.map(({ q, num }) => <QuestaoCard key={q.id} q={q} num={num} />)}
                </div>
              </div>

            </div>
          )
        })}

        {/* ══ FOLHA DE RESPOSTAS ══ */}
        <div className="folha">

          <div className="fh-inner">
            <Barcode width={140} height={8} id={String(simulado.id)} />
            <div className="fh-right">
              <span className="fh-h">henryjr</span>
              <span className="fh-y">{ano}</span>
            </div>
          </div>
          <div className="fh-dash" />

          <div className="ft-wrap">
            <div className="ft-titulo">FOLHA DE RESPOSTAS</div>
            <div className="ft-sub">Preencha completamente o círculo · caneta azul ou preta</div>
          </div>

          <div className="fc-row">
            <div className="campo">
              <span className="cr-rot">CANDIDATO(A)</span>
              <span className="campo-linha" />
            </div>
            <div className="campo campo-sm">
              <span className="cr-rot">DATA</span>
              <span className="campo-linha" />
            </div>
          </div>

          <div className="fg-grid">
            {sorted.map((q, idx) => {
              const cor = AREA_COLOR[q.area] ?? '#333'
              return (
                <div key={q.id} className="fg-item">
                  <span className="fg-num" style={{ color: cor }}>
                    {String(idx + 1).padStart(2,'0')}
                  </span>
                  {['A','B','C','D','E'].map(l => (
                    <span key={l} className="fg-b" style={{ borderColor: cor, color: cor }}>{l}</span>
                  ))}
                </div>
              )
            })}
          </div>

          <div className="fr-rod">
            <div className="fr-dash" />
            <div className="fr-txt">
              <span className="fr-marca">HENRYJR</span>
              {' '}·{' '}Banco de Questões ENEM{' '}·{' '}henryjr.vercel.app
            </div>
          </div>

        </div>{/* /folha */}

      </div>{/* /caderno */}

      {/* ══════════ ESTILOS ══════════ */}
      <style>{`
        /* ─────────────────────────────────────────────────────────────────
         * @page: margens que definem o espaço físico das margens do papel.
         * A "área de conteúdo" começa DEPOIS dessas margens.
         * position: fixed com top: -14mm posiciona o elemento 14mm ACIMA
         * da área de conteúdo = exatamente no espaço da margem física.
         * ───────────────────────────────────────────────────────────────── */
        @page {
          size: A4;
          margin: 14mm 10mm 12mm 10mm;
        }

        @media print {
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          .no-print { display: none !important; }
          html, body { background: white !important; color: #111; }
          /* Sem !important no color: inline styles (cores de área) precisam vencer. */

          /* ── CRÍTICO: remove o grain/ruído animado do globals.css ──
           * body::before tem position: fixed + inset: -50% + z-index: 9999.
           * Em impressão, esse elemento aparece em todas as páginas como
           * um padrão de quadrados pretos ou manchas coloridas.          */
          body::before,
          body::after { display: none !important; }

          /* Oculta interface do site */
          header, nav, footer,
          [class*="NavBar"], [class*="MobileTab"],
          [class*="layout"] > *:not(.caderno) { display: none !important; }

          /* Caderno: sem padding extra — @page margin já cuida do espaçamento */
          .caderno {
            padding: 0 !important;
            max-width: 100% !important;
            box-shadow: none !important;
          }

          /* CAPA: sempre quebra após ela */
          .capa {
            page-break-after: always !important;
            break-after: page !important;
          }

          /* ── CABEÇALHO FIXO ──
           * top: -14mm (negativo igual ao @page margin-top) posiciona o elemento
           * no espaço físico da margem superior do papel, NÃO na área de conteúdo.
           * Com top: 0, o elemento ficaria no topo da área de conteúdo e cobriria
           * as primeiras 14mm de TODA página (2ª página em diante).            */
          .pg-head {
            display: flex !important;
            position: fixed;
            top: -14mm;
            left: -10mm;
            right: -10mm;
            height: 14mm;
            flex-direction: column;
            background: white;
            z-index: 9999;
          }

          /* ── RODAPÉ FIXO ──
           * bottom: -12mm (negativo igual ao @page margin-bottom).              */
          .pg-foot {
            display: flex !important;
            position: fixed;
            bottom: -12mm;
            left: -10mm;
            right: -10mm;
            height: 12mm;
            flex-direction: column;
            background: white;
            z-index: 9999;
          }

          /* ── CABEÇALHO DE ÁREA não fica órfão ──
           * break-after: avoid impede quebra de página LOGO APÓS o título da área.
           * O Chrome não ignora esta regra (ao contrário de break-inside em blocos
           * grandes), porque o elemento seguinte (questoes-wrap) não precisa caber
           * inteiro — apenas a primeira questão precisa aparecer junto.          */
          .area-head {
            break-after: avoid !important;
            page-break-after: avoid !important;
          }

          /* Questão individual não quebra no meio */
          .questao {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
          }

          /* Folha começa em nova página */
          .folha {
            page-break-before: always !important;
            break-before: page !important;
          }

          /* 2 colunas lado a lado.
           * break-before: avoid impede quebra de página ENTRE .area-head e
           * .questoes-wrap. Sozinho o break-after: avoid em .area-head não é
           * suficiente em Chrome/Puppeteer quando o bloco seguinte é um flex
           * muito alto; a combinação dos dois elimina o cabeçalho órfão.      */
          .questoes-wrap {
            display: flex !important;
            flex-direction: row !important;
            break-before: avoid !important;
            page-break-before: avoid !important;
          }

          /* Texto das instruções: forçar preto */
          .ci-lista, .ci-lista li, .ci-lista li strong { color: #111 !important; }
          .ci-titulo { color: #111 !important; }

          /* Garante que cores de área (azul, marrom, verde, roxo) chegam ao PDF.
           * O -webkit-print-color-adjust: exact já ativa cores de background;
           * aqui garantimos que o color do texto também não é suprimido.      */
          .ah-nome, .q-num, .q-barra, .q-letra, .fg-num, .fg-b {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
        }

        /* ── Reset ── */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #ccc; }

        /* ── Suprime grain do globals.css nesta página (tela + impressão) ──
         * body::before tem animation: grain infinite que impede document_idle
         * e aparece como padrão escuro em impressão. Removido aqui globalmente. */
        body::before, body::after { display: none !important; animation: none !important; }

        /* ── Barra de controle ── */
        .ctrl {
          position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          background: #0E0D0B; border-bottom: 1px solid #2C2820;
          padding: 8px 20px;
          font-family: Arial, sans-serif; font-size: 13px; color: rgba(255,255,255,0.7);
        }
        .ctrl-info { font-weight: bold; white-space: nowrap; }
        .ctrl-tip {
          flex: 1; text-align: center; font-size: 11px; color: #D4A853;
          background: rgba(212,168,83,0.1); border: 1px solid rgba(212,168,83,0.3);
          border-radius: 6px; padding: 4px 10px;
        }
        .btn-dl {
          background: #166534; color: #d1fae5; border: 1px solid #16a34a;
          border-radius: 8px; padding: 6px 14px; font-weight: 700; font-size: 12px; cursor: pointer; white-space: nowrap;
        }
        .btn-dl:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-imp {
          background: #D4A853; color: #0E0D0B; border: none;
          border-radius: 8px; padding: 6px 16px; font-weight: 700; font-size: 12px; cursor: pointer; white-space: nowrap;
        }
        .btn-fch {
          background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); border: none;
          border-radius: 8px; padding: 6px 12px; font-size: 12px; cursor: pointer;
        }

        /* ── Cabeçalho fixo das páginas (oculto na tela) ── */
        .pg-head { display: none; }
        .ph-inner {
          flex: 1;
          display: flex; align-items: center; justify-content: space-between;
          padding: 2.5mm 3mm 1mm;
        }
        .ph-left { display: flex; align-items: flex-start; }
        .ph-right { display: flex; align-items: baseline; gap: 2px; }
        .ph-h { font-family: Arial, sans-serif; font-size: 12pt; font-weight: 900; color: #0077B6; letter-spacing: -.5px; }
        .ph-y { font-family: Arial, sans-serif; font-size: 9pt; font-weight: 300; color: #B8882A; }
        .ph-sub { font-family: Arial, sans-serif; font-size: 5.5pt; color: #999; margin-left: 4px; align-self: flex-end; }
        .ph-dash { height: 0; border-top: 1px dashed #bbb; margin: 0 3mm; }

        /* ── Rodapé fixo das páginas (oculto na tela) ── */
        .pg-foot { display: none; }
        .pf-dash { height: 0; border-top: 1px dashed #bbb; margin: 0 3mm 1.5mm; }
        .pf-inner {
          flex: 1;
          display: flex; align-items: center; justify-content: space-between;
          padding: 0 3mm 2mm;
          font-family: Arial, sans-serif; font-size: 7pt; color: #666;
        }
        .pf-center { font-weight: bold; color: #333; letter-spacing: .3px; }
        .pf-logo { color: #0077B6; font-weight: 900; font-size: 7.5pt; }

        /* ── Caderno ── */
        .caderno {
          max-width: 210mm; margin: 0 auto; background: white;
          font-family: 'Times New Roman', Times, serif;
          font-size: 10.5pt; color: #111;
          padding-top: 52px;   /* espaço para barra ctrl na tela */
          box-shadow: 0 4px 32px rgba(0,0,0,.2);
        }

        /* ════ CAPA ════ */
        .capa-azul {
          background: linear-gradient(150deg, #004E89 0%, #0077B6 45%, #009AC7 100%);
          padding: 20px 20px 22px; color: white;
        }
        .ca-t1 { font-family: Arial, sans-serif; font-size: 14pt; font-weight: 900; letter-spacing: 1.5px; text-align: center; margin-bottom: 4px; }
        .ca-t2 { font-family: Arial, sans-serif; font-size: 9pt; font-weight: 400; letter-spacing: 1px; text-align: center; opacity: .85; margin-bottom: 14px; }
        .ca-areas { text-align: center; }
        .ca-ar { font-family: Arial, sans-serif; font-size: 8.5pt; font-weight: 600; letter-spacing: .4px; opacity: .9; line-height: 1.8; }

        .capa-mid { display: flex; align-items: stretch; justify-content: space-between; border-bottom: 1px solid #e0e0e0; }
        .cm-logo { flex: 1; display: flex; align-items: baseline; gap: 3px; padding: 12px 16px; border-right: 1px solid #eee; }
        .cm-h { font-family: Arial, sans-serif; font-size: 28pt; font-weight: 900; color: #0077B6; letter-spacing: -1px; line-height: 1; }
        .cm-y { font-family: Arial, sans-serif; font-size: 20pt; font-weight: 300; color: #B8882A; line-height: 1; }
        .cm-box { text-align: right; padding: 10px 16px; }
        .cm-label { font-family: Arial, sans-serif; font-size: 6.5pt; color: #999; letter-spacing: 3px; font-weight: bold; }
        .cm-num { font-family: Arial, sans-serif; font-size: 20pt; font-weight: 900; color: #B8882A; line-height: 1; }
        .cm-qtd { font-family: Arial, sans-serif; font-size: 8pt; color: #333; font-weight: bold; letter-spacing: .8px; }
        .cm-data { font-family: Arial, sans-serif; font-size: 7.5pt; color: #999; }

        .capa-strip { display: flex; height: 10px; overflow: hidden; }
        .cs-c { flex: 1; }

        .capa-frase { padding: 10px 16px 8px; background: #fffdf8; border-bottom: 1px solid #eee; }
        .cf-label { font-family: Arial, sans-serif; font-size: 7pt; font-weight: bold; letter-spacing: .4px; color: #555; text-align: center; text-transform: uppercase; margin-bottom: 5px; }
        .cf-box { border: 1.5px solid #B8882A; border-radius: 4px; padding: 6px 16px; background: white; text-align: center; }
        .cf-texto { font-family: 'Times New Roman', serif; font-size: 10.5pt; font-style: italic; color: #333; line-height: 1.5; }

        .capa-inst { padding: 10px 16px 10px; border-bottom: 1px solid #ddd; }
        .ci-titulo { font-family: Arial, sans-serif; font-size: 9pt; font-weight: 900; letter-spacing: .5px; text-align: center; color: #111; margin-bottom: 7px; }
        .ci-lista { padding-left: 16px; font-family: Arial, sans-serif; font-size: 8.5pt; color: #111; line-height: 1.65; list-style-type: decimal; }
        .ci-lista li { margin-bottom: 2px; text-align: justify; color: #111; }
        .ci-lista li strong { color: #111; }

        .capa-rod { display: flex; align-items: center; justify-content: space-between; padding: 7px 16px; border-top: 1px solid #ddd; }
        .cr-l { display: flex; flex-direction: column; }
        .cr-marca { font-family: Arial, sans-serif; font-size: 8.5pt; font-weight: 900; color: #B8882A; letter-spacing: 3px; }
        .cr-sub { font-family: Arial, sans-serif; font-size: 6.5pt; color: #999; }
        .cr-c { font-family: Arial, sans-serif; font-size: 7.5pt; color: #666; }

        /* ════ QUESTÕES ════ */
        .area-bloco { }

        .area-head {
          border-bottom: 2.5px solid;
          padding: 8px 12px 5px;
          background: white;
          /* break-after: avoid declarado aqui também (para screen, sem efeito) */
        }
        .ah-nome { font-family: Arial, sans-serif; font-size: 9.5pt; font-weight: 900; letter-spacing: .3px; }
        .ah-range { font-family: Arial, sans-serif; font-size: 8pt; color: #666; margin-top: 1px; }

        .questoes-wrap { display: flex; flex-direction: row; align-items: flex-start; }
        .coluna { flex: 1; padding: 8px 11px; }
        .sep-v { width: 1px; background: #c0c0c0; align-self: stretch; margin: 8px 0; }

        .questao { margin-bottom: 13px; padding-bottom: 11px; border-bottom: 1px solid #e0e0e0; }
        .questao:last-child { border-bottom: none; margin-bottom: 0; }

        .q-head { display: flex; align-items: center; gap: 7px; margin-bottom: 1px; }
        .q-num { font-family: Arial, sans-serif; font-size: 9.5pt; font-weight: 900; white-space: nowrap; letter-spacing: .3px; }
        .q-barra { flex: 1; height: 0; border-top: 2.5px solid; }
        .q-anulada { font-family: Arial, sans-serif; font-size: 6.5pt; font-weight: 900; color: #c00; border: 1.5px solid #c00; padding: 0 4px; border-radius: 2px; }

        .q-meta { font-family: Arial, sans-serif; font-size: 7.5pt; color: #888; margin-bottom: 4px; }

        .q-par  { font-size: 9.5pt; line-height: 1.55; color: #111; margin-bottom: 4px; text-align: justify; }
        .q-fonte { font-size: 8pt; color: #777; font-style: italic; text-align: right; margin-bottom: 3px; }
        .q-cmd  { font-size: 9.5pt; font-weight: bold; line-height: 1.5; color: #111; margin: 6px 0 5px; text-align: justify; border-top: 1px dashed #ccc; padding-top: 5px; }

        .q-alts { margin-top: 5px; }
        .q-alt  { display: flex; align-items: flex-start; gap: 5px; margin-bottom: 2px; font-size: 9.5pt; line-height: 1.4; }
        .q-letra { display: inline-flex; align-items: center; justify-content: center; width: 15px; height: 15px; border-radius: 50%; border: 1.5px solid; font-family: Arial, sans-serif; font-size: 7.5pt; font-weight: 900; flex-shrink: 0; margin-top: 1px; }
        .q-txt  { color: #111; text-align: justify; flex: 1; }

        /* ════ FOLHA DE RESPOSTAS ════ */
        .folha { background: white; }
        .fh-inner { display: flex; align-items: center; justify-content: space-between; padding: 5px 12px 3px; border-bottom: 1px solid #eee; }
        .fh-right { display: flex; align-items: baseline; gap: 2px; }
        .fh-h { font-family: Arial, sans-serif; font-size: 12pt; font-weight: 900; color: #0077B6; letter-spacing: -.5px; }
        .fh-y { font-family: Arial, sans-serif; font-size: 9pt; font-weight: 300; color: #B8882A; }
        .fh-dash { height: 0; border-top: 1px dashed #bbb; margin: 0 12px; }

        .ft-wrap { text-align: center; padding: 12px 16px 6px; border-bottom: 1px solid #eee; }
        .ft-titulo { font-family: Arial, sans-serif; font-size: 12pt; font-weight: 900; letter-spacing: 4px; color: #B8882A; border: 2.5px solid #B8882A; display: inline-block; padding: 4px 22px; margin-bottom: 4px; }
        .ft-sub { font-family: Arial, sans-serif; font-size: 7.5pt; color: #777; }

        .fc-row { display: flex; gap: 12px; padding: 8px 16px; border-bottom: 1px solid #eee; }
        .campo { flex: 1; display: flex; align-items: baseline; gap: 6px; border-bottom: 1.5px solid #444; padding-bottom: 2px; }
        .campo-sm { flex: 0 0 120px; }
        .cr-rot { font-family: Arial, sans-serif; font-size: 7pt; font-weight: 900; letter-spacing: .8px; color: #666; white-space: nowrap; }
        .campo-linha { flex: 1; min-height: 14px; }

        .fg-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px 6px; padding: 10px 16px 14px; }
        .fg-item { display: flex; align-items: center; gap: 3px; }
        .fg-num { font-family: Arial, sans-serif; font-size: 8.5pt; font-weight: 900; min-width: 20px; text-align: right; }
        .fg-b { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; border: 1.5px solid; font-family: Arial, sans-serif; font-size: 7pt; font-weight: 900; flex-shrink: 0; }

        .fr-rod { margin-top: 8px; }
        .fr-dash { height: 0; border-top: 1px dashed #bbb; margin: 0 16px 4px; }
        .fr-txt { text-align: center; font-family: Arial, sans-serif; font-size: 7.5pt; color: #aaa; padding-bottom: 12px; }
        .fr-marca { color: #B8882A; font-weight: 900; letter-spacing: 2px; }
      `}</style>
    </>
  )
}

/* ── Card de Questão ── */
function QuestaoCard({ q, num }: { q: Questao; num: number }) {
  const label = AREA_LABEL[q.area] ?? q.area
  const cor   = AREA_COLOR[q.area] ?? '#333'

  return (
    <div className="questao">
      <div className="q-head">
        <span className="q-num" style={{ color: cor }}>
          QUESTÃO {String(num).padStart(2, '0')}
        </span>
        <div className="q-barra" style={{ borderTopColor: cor }} />
        {q.anulada && <span className="q-anulada">ANULADA</span>}
      </div>
      <div className="q-meta">ENEM {q.ano}&nbsp;&nbsp;·&nbsp;&nbsp;{label}</div>
      {q.enunciado?.map((p, i) => {
        const isFonte = p.length < 120 && (
          p.includes('Disponível') || p.includes('Acesso em') ||
          /^[A-Z]{2,}[\.,]/.test(p) || p.startsWith('Fonte:')
        )
        return isFonte
          ? <p key={i} className="q-fonte">{p}</p>
          : <p key={i} className="q-par">{p}</p>
      })}
      {q.comando && <p className="q-cmd">{q.comando}</p>}
      <div className="q-alts">
        {(['A','B','C','D','E'] as const).map(letra =>
          q.alternativas?.[letra] ? (
            <div key={letra} className="q-alt">
              <span className="q-letra" style={{ color: cor, borderColor: cor }}>{letra}</span>
              <span className="q-txt">{q.alternativas[letra]}</span>
            </div>
          ) : null
        )}
      </div>
    </div>
  )
}
