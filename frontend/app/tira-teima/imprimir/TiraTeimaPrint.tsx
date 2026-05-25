'use client'

const AREAS: Record<string, { label: string; cor: string }> = {
  'Linguagens, Codigos e suas Tecnologias':    { label: 'Linguagens',  cor: '#38bdf8' },
  'Ciencias Humanas e suas Tecnologias':       { label: 'Humanas',     cor: '#fbbf24' },
  'Ciencias da Natureza e suas Tecnologias':   { label: 'C. Natureza', cor: '#34d399' },
  'Matematica e suas Tecnologias':             { label: 'Matemática',  cor: '#a78bfa' },
}

interface Questao {
  id: number; ano: number; numero: number; dia: string; area: string
  competencia: string | null; enunciado: string[]; comando: string
  alternativas: Record<string, string>; gabarito: string | null
  tem_imagem: boolean
  imagens: Array<{ path: string; posicao: string; supabase_url?: string }>
}

interface Props {
  questoes: Questao[]
  incluirGabarito: boolean
  usuario: string
  dataGeracao: string
}

function Img({ imagens }: { imagens: Questao['imagens'] }) {
  const antes = imagens.filter(img => img.posicao === 'antes_1')
  if (!antes.length) return null
  return (
    <div style={{ margin: '6px 0' }}>
      {antes.map((img, i) => (
        <img
          key={i}
          src={img.supabase_url ?? ''}
          alt="imagem da questão"
          style={{ maxWidth: '100%', maxHeight: 180, display: 'block', borderRadius: 4 }}
        />
      ))}
    </div>
  )
}

function CardQ({ q, idx, incluirGabarito }: { q: Questao; idx: number; incluirGabarito: boolean }) {
  const area = AREAS[q.area] ?? { label: q.area, cor: '#888' }
  return (
    <div style={{
      breakInside: 'avoid',
      border: '1px solid #2C2820',
      borderRadius: 10,
      padding: '10px 12px',
      marginBottom: 10,
      background: '#161411',
    }}>
      {/* Header da questão */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
        <span style={{
          background: '#0E0D0B', border: `1px solid ${area.cor}50`,
          color: area.cor, fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 999,
          textTransform: 'uppercase', letterSpacing: '0.06em'
        }}>
          {area.label}
        </span>
        <span style={{ fontSize: 9, color: '#ffffff50' }}>
          ENEM {q.ano} — Q.{q.numero}
        </span>
        {q.competencia && (
          <span style={{ fontSize: 9, color: '#D4A85360' }}>{q.competencia}</span>
        )}
        {incluirGabarito && q.gabarito && (
          <span style={{
            marginLeft: 'auto', fontSize: 9, color: '#4ade80',
            background: '#4ade8015', border: '1px solid #4ade8030',
            padding: '1px 6px', borderRadius: 999
          }}>
            Gabarito: {q.gabarito}
          </span>
        )}
      </div>

      {/* Imagens antes do enunciado */}
      {q.tem_imagem && <Img imagens={q.imagens ?? []} />}

      {/* Enunciado */}
      {q.enunciado.map((p, i) => (
        <p key={i} style={{ fontSize: 11, color: '#ffffffcc', lineHeight: 1.6, marginBottom: 4, fontFamily: 'Georgia, serif' }}>
          {p}
        </p>
      ))}
      {q.comando && (
        <p style={{ fontSize: 11, color: '#ffffffaa', lineHeight: 1.6, marginBottom: 8, fontStyle: 'italic', fontFamily: 'Georgia, serif' }}>
          {q.comando}
        </p>
      )}

      {/* Alternativas */}
      {Object.entries(q.alternativas ?? {}).map(([letra, texto]) => (
        <div key={letra} style={{
          display: 'flex', gap: 6, marginBottom: 3,
          padding: '3px 6px', borderRadius: 5,
          background: incluirGabarito && letra === q.gabarito ? '#4ade8012' : 'transparent',
          border: incluirGabarito && letra === q.gabarito ? '1px solid #4ade8030' : '1px solid transparent',
        }}>
          <span style={{ fontWeight: 700, fontSize: 10, color: incluirGabarito && letra === q.gabarito ? '#4ade80' : '#D4A853', minWidth: 14 }}>
            {letra}
          </span>
          <span style={{ fontSize: 10, color: '#ffffffaa', lineHeight: 1.5, fontFamily: 'Georgia, serif' }}>{texto}</span>
        </div>
      ))}
    </div>
  )
}

export default function TiraTeimaPrint({ questoes, incluirGabarito, usuario, dataGeracao }: Props) {
  if (!questoes.length) {
    return (
      <div className="sem-questoes" style={{ padding: 40, textAlign: 'center', color: '#ffffff50', fontFamily: 'sans-serif' }}>
        <p>Nenhuma questão no Tira Teima.</p>
      </div>
    )
  }

  // Agrupar por área
  const porArea: Record<string, Questao[]> = {}
  for (const q of questoes) {
    if (!porArea[q.area]) porArea[q.area] = []
    porArea[q.area].push(q)
  }

  return (
    <>
      <style>{`
        @page { margin: 14mm 10mm 12mm 10mm; size: A4; }
        @media print {
          html, body { background: #0E0D0B !important; }
          * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        }
        body { background: #0E0D0B; font-family: -apple-system, sans-serif; }
      `}</style>

      {/* Cabeçalho fixo */}
      <div style={{
        position: 'fixed', top: -14, left: 0, right: 0, height: 14,
        background: '#161411', borderBottom: '1px solid #2C2820',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 10mm', fontSize: 8, color: '#ffffff40'
      }}>
        <span style={{ fontWeight: 700, color: '#D4A853' }}>📓 TIRA TEIMA — HenryJr</span>
        <span>{usuario} · {dataGeracao}</span>
      </div>

      {/* Rodapé fixo */}
      <div style={{
        position: 'fixed', bottom: -12, left: 0, right: 0, height: 12,
        background: '#161411', borderTop: '1px solid #2C2820',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 7, color: '#ffffff25'
      }}>
        Gerado em {dataGeracao} · henryjr.vercel.app
      </div>

      {/* Conteúdo */}
      <div style={{ padding: '0 0 20px 0', color: '#ffffff' }} className="area-bloco">

        {/* Capa */}
        <div style={{
          breakAfter: 'page', minHeight: '100vh',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', textAlign: 'center'
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📓</div>
          <h1 style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, marginBottom: 8, color: '#D4A853' }}>
            TIRA TEIMA
          </h1>
          <p style={{ fontSize: 13, color: '#ffffff60', marginBottom: 4 }}>Caderno de Revisão</p>
          <p style={{ fontSize: 13, color: '#ffffff40' }}>{questoes.length} questões · Gerado em {dataGeracao}</p>
          <div style={{ marginTop: 32, borderTop: '1px solid #2C2820', paddingTop: 16, width: 200 }}>
            <p style={{ fontSize: 10, color: '#ffffff30' }}>Aluno: {usuario}</p>
          </div>
        </div>

        {/* Questões por área */}
        {Object.entries(porArea).map(([areaNome, qs]) => {
          const area = AREAS[areaNome] ?? { label: areaNome, cor: '#888' }
          return (
            <div key={areaNome} style={{ marginBottom: 24 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                marginBottom: 10, breakAfter: 'avoid',
                borderBottom: `2px solid ${area.cor}40`, paddingBottom: 6
              }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, color: area.cor }}>
                  {area.label}
                </h2>
                <span style={{
                  fontSize: 9, background: `${area.cor}15`, border: `1px solid ${area.cor}30`,
                  color: area.cor, padding: '1px 6px', borderRadius: 999
                }}>
                  {qs.length} questões
                </span>
              </div>
              {qs.map((q, idx) => (
                <CardQ key={q.id} q={q} idx={idx} incluirGabarito={incluirGabarito} />
              ))}
            </div>
          )
        })}

        {/* Gabarito final (se solicitado) */}
        {incluirGabarito && (
          <div style={{ breakBefore: 'page', paddingTop: 20 }}>
            <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: '#D4A853' }}>
              Gabarito
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 6 }}>
              {questoes.map(q => (
                <div key={q.id} style={{
                  border: '1px solid #2C2820', borderRadius: 6,
                  padding: '4px 6px', textAlign: 'center', background: '#161411'
                }}>
                  <div style={{ fontSize: 9, color: '#ffffff40' }}>
                    ENEM {q.ano} Q{q.numero}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#4ade80' }}>
                    {q.gabarito ?? '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
