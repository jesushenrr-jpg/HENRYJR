/**
 * SimuladoPDF.tsx
 * Documento react-pdf para geração de simulados imprimíveis.
 * Layout inspirado no caderno do ENEM: 2 colunas, questões numeradas,
 * folha de respostas e gabarito final.
 */
import React from 'react'
import {
  Document, Page, View, Text, StyleSheet, Image,
  Font, Canvas,
} from '@react-pdf/renderer'

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface QuestaoSimulado {
  id:           number
  numero:       number
  ano:          number
  dia:          string
  area:         string
  competencia:  string | null
  enunciado:    string[]
  comando:      string | null
  alternativas: Record<string, string>
  gabarito:     string | null
  imagens?:     { supabase_url?: string; path?: string; posicao?: string }[]
  anulada?:     boolean
}

export interface SimuladoInfo {
  id:          number
  tipo:        string
  total:       number
  criado_em:   string
}

// ── Cores e tipografia ─────────────────────────────────────────────────────

const C = {
  black:   '#000000',
  dark:    '#1a1a1a',
  mid:     '#444444',
  light:   '#888888',
  border:  '#cccccc',
  bg:      '#f5f5f5',
  white:   '#ffffff',
  blue:    '#1a3a6b',   // cor cabeçalho / rótulos
  accent:  '#c8960c',   // dourado (marca HenryJr)
}

// ── Estilos ───────────────────────────────────────────────────────────────

const s = StyleSheet.create({
  // Páginas
  page: {
    fontFamily: 'Helvetica',
    fontSize: 8.5,
    color: C.dark,
    paddingTop: 30,
    paddingBottom: 40,
    paddingLeft: 28,
    paddingRight: 28,
    backgroundColor: C.white,
  },

  // Cabeçalho de página
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1.5,
    borderBottomColor: C.blue,
    paddingBottom: 5,
    marginBottom: 10,
  },
  headerTitle: {
    fontSize: 12,
    fontFamily: 'Helvetica-Bold',
    color: C.blue,
    letterSpacing: 0.5,
  },
  headerSub: {
    fontSize: 7,
    color: C.light,
    marginTop: 1,
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  headerPage: {
    fontSize: 7,
    color: C.light,
  },

  // Rodapé
  footer: {
    position: 'absolute',
    bottom: 16,
    left: 28,
    right: 28,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 0.5,
    borderTopColor: C.border,
    paddingTop: 4,
  },
  footerText: {
    fontSize: 6.5,
    color: C.light,
  },

  // Colunas
  cols: {
    flexDirection: 'row',
    gap: 10,
    flexGrow: 1,
  },
  col: {
    flex: 1,
  },

  // Questão
  questaoBox: {
    marginBottom: 10,
    borderLeftWidth: 2,
    borderLeftColor: C.blue,
    paddingLeft: 5,
  },
  questaoNum: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    color: C.blue,
    marginBottom: 2,
  },
  questaoMeta: {
    fontSize: 6.5,
    color: C.light,
    marginBottom: 3,
  },
  paragrafo: {
    fontSize: 7.5,
    color: C.dark,
    lineHeight: 1.35,
    marginBottom: 2,
  },
  comando: {
    fontSize: 7.5,
    fontFamily: 'Helvetica-Bold',
    color: C.dark,
    lineHeight: 1.35,
    marginBottom: 3,
    marginTop: 1,
  },
  alt: {
    flexDirection: 'row',
    marginBottom: 1.5,
    alignItems: 'flex-start',
  },
  altLetra: {
    fontSize: 7.5,
    fontFamily: 'Helvetica-Bold',
    color: C.blue,
    width: 12,
    flexShrink: 0,
  },
  altTexto: {
    fontSize: 7.5,
    color: C.dark,
    lineHeight: 1.3,
    flex: 1,
  },
  separador: {
    borderBottomWidth: 0.5,
    borderBottomColor: C.border,
    marginVertical: 6,
  },

  // Área badge
  areaBadge: {
    fontSize: 6,
    color: C.white,
    backgroundColor: C.blue,
    paddingHorizontal: 3,
    paddingVertical: 1,
    borderRadius: 2,
    marginBottom: 2,
    alignSelf: 'flex-start',
  },

  // Imagem
  imgBox: {
    marginVertical: 3,
    alignItems: 'center',
  },
  img: {
    maxWidth: '100%',
    maxHeight: 80,
    objectFit: 'contain',
  },
})

// ── Helpers ───────────────────────────────────────────────────────────────

const AREA_SHORT: Record<string, string> = {
  'Linguagens, Codigos e suas Tecnologias':   'Linguagens',
  'Ciencias Humanas e suas Tecnologias':       'Humanas',
  'Ciencias da Natureza e suas Tecnologias':   'C. Natureza',
  'Matematica e suas Tecnologias':             'Matemática',
}

function fmtData(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('pt-BR')
  } catch {
    return iso
  }
}

// ── Componente de questão ──────────────────────────────────────────────────

function Questao({ q, seq }: { q: QuestaoSimulado; seq: number }) {
  const imgAntes = (q.imagens ?? []).filter(i => i.posicao?.startsWith('antes'))
  const imgDepois = (q.imagens ?? []).filter(i => i.posicao?.startsWith('depois'))

  return (
    <View style={s.questaoBox} wrap={false}>
      <Text style={s.questaoNum}>QUESTÃO {seq}</Text>
      <Text style={s.questaoMeta}>
        ENEM {q.ano} · Q.{q.numero} · {AREA_SHORT[q.area] ?? q.area}
        {q.competencia ? ` · ${q.competencia}` : ''}
      </Text>

      {/* Imagens antes do enunciado */}
      {imgAntes.map((img, i) => {
        const url = img.supabase_url ?? ''
        if (!url) return null
        return (
          <View key={i} style={s.imgBox}>
            <Image src={url} style={s.img} />
          </View>
        )
      })}

      {/* Parágrafos do enunciado */}
      {(q.enunciado ?? []).map((p, i) => (
        <Text key={i} style={s.paragrafo}>{p}</Text>
      ))}

      {/* Imagens após enunciado */}
      {imgDepois.map((img, i) => {
        const url = img.supabase_url ?? ''
        if (!url) return null
        return (
          <View key={i} style={s.imgBox}>
            <Image src={url} style={s.img} />
          </View>
        )
      })}

      {/* Comando */}
      {q.comando && (
        <Text style={s.comando}>{q.comando}</Text>
      )}

      {/* Alternativas */}
      {Object.entries(q.alternativas ?? {}).map(([letra, txt]) => (
        <View key={letra} style={s.alt}>
          <Text style={s.altLetra}>{letra})</Text>
          <Text style={s.altTexto}>{txt}</Text>
        </View>
      ))}

      {q.anulada && (
        <Text style={{ fontSize: 6.5, color: '#cc0000', marginTop: 2 }}>
          ⚠ Questão oficialmente anulada
        </Text>
      )}
    </View>
  )
}

// ── Cabeçalho de página ────────────────────────────────────────────────────

function CabecalhoPagina({ titulo, data, tipo }: { titulo: string; data: string; tipo: string }) {
  return (
    <View style={s.header} fixed>
      <View>
        <Text style={s.headerTitle}>{titulo}</Text>
        <Text style={s.headerSub}>{tipo} · {data} · henryjr.vercel.app</Text>
      </View>
      <View style={s.headerRight}>
        <Text style={s.headerPage} render={({ pageNumber, totalPages }) =>
          `Pág. ${pageNumber} / ${totalPages}`
        } />
      </View>
    </View>
  )
}

// ── Folha de respostas ─────────────────────────────────────────────────────

const FR_COLS = 5   // questões por linha na folha de respostas
const MARKER  = 8   // tamanho dos marcadores de canto em pt

const fsStyles = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 8,
    color: '#1a1a1a',
    paddingTop: 28,
    paddingBottom: 28,
    paddingLeft: 28,
    paddingRight: 28,
    backgroundColor: '#ffffff',
  },
  titulo: {
    fontSize: 11,
    fontFamily: 'Helvetica-Bold',
    color: C.blue,
    textAlign: 'center',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  subtitulo: {
    fontSize: 7,
    color: C.light,
    textAlign: 'center',
    marginBottom: 10,
  },
  camposLinha: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  campoBox: {
    flex: 1,
  },
  campoLabel: {
    fontSize: 6.5,
    color: C.light,
    marginBottom: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  campoLinhaInput: {
    borderBottomWidth: 0.8,
    borderBottomColor: C.border,
    height: 14,
  },
  instrucoes: {
    fontSize: 6.5,
    color: C.mid,
    marginBottom: 8,
    backgroundColor: '#f0f4ff',
    padding: 5,
    borderRadius: 3,
  },
  gridRow: {
    flexDirection: 'row',
    marginBottom: 2,
  },
  celula: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 1,
  },
  celulaNum: {
    fontSize: 6.5,
    color: C.dark,
    marginBottom: 1.5,
    fontFamily: 'Helvetica-Bold',
  },
  celulaOpcoes: {
    flexDirection: 'row',
    gap: 2,
  },
  bolinha: {
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 0.8,
    borderColor: C.mid,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bolinhaLetra: {
    fontSize: 5.5,
    color: C.mid,
  },
  separadorLinha: {
    borderTopWidth: 0.4,
    borderTopColor: C.border,
    marginVertical: 2,
  },
  gabarito: {
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: C.blue,
    paddingTop: 6,
  },
  gabTitulo: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    color: C.blue,
    marginBottom: 4,
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  gabRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  gabCell: {
    width: '10%',
    alignItems: 'center',
    paddingVertical: 1.5,
    borderWidth: 0.3,
    borderColor: C.border,
  },
  gabNum: {
    fontSize: 6,
    color: C.light,
  },
  gabLetra: {
    fontSize: 7.5,
    fontFamily: 'Helvetica-Bold',
    color: C.dark,
  },
})

// ── Marcadores de canto (para scanning) ───────────────────────────────────

function MarkerCanto({ top, left, right, bottom }: {
  top?: number; left?: number; right?: number; bottom?: number
}) {
  return (
    <View style={{
      position: 'absolute',
      top, left, right, bottom,
      width: MARKER,
      height: MARKER,
    }}>
      <Canvas
        paint={(painter) => {
          // Quadrado preto sólido (marcador de canto)
          painter.rect(0, 0, MARKER, MARKER).fill('#000000')
          // Mini quadrado branco interior (para reconhecimento único)
          painter.rect(2, 2, MARKER - 4, MARKER - 4).fill('#ffffff')
          return null
        }}
        style={{ width: MARKER, height: MARKER }}
      />
    </View>
  )
}

// ── Página de folha de respostas ───────────────────────────────────────────

function FolhaRespostas({
  questoes, simuladoId, data, incluirGabarito
}: {
  questoes: QuestaoSimulado[]
  simuladoId: number
  data: string
  incluirGabarito: boolean
}) {
  // Organiza em grupos de FR_COLS por linha
  const grupos: QuestaoSimulado[][] = []
  for (let i = 0; i < questoes.length; i += FR_COLS) {
    grupos.push(questoes.slice(i, i + FR_COLS))
  }

  return (
    <Page size="A4" style={fsStyles.page}>
      {/* Marcadores de canto para detecção de perspectiva */}
      <MarkerCanto top={14} left={14} />
      <MarkerCanto top={14} right={14} />
      <MarkerCanto bottom={14} left={14} />
      <MarkerCanto bottom={14} right={14} />

      <Text style={fsStyles.titulo}>FOLHA DE RESPOSTAS</Text>
      <Text style={fsStyles.subtitulo}>
        Simulado #{simuladoId} · {questoes.length} questões · {data} · henryjr.vercel.app
      </Text>

      {/* Campos do candidato */}
      <View style={fsStyles.camposLinha}>
        <View style={[fsStyles.campoBox, { flex: 2 }]}>
          <Text style={fsStyles.campoLabel}>Nome completo</Text>
          <View style={fsStyles.campoLinhaInput} />
        </View>
        <View style={fsStyles.campoBox}>
          <Text style={fsStyles.campoLabel}>Data</Text>
          <View style={fsStyles.campoLinhaInput} />
        </View>
        <View style={fsStyles.campoBox}>
          <Text style={fsStyles.campoLabel}>Turma</Text>
          <View style={fsStyles.campoLinhaInput} />
        </View>
      </View>

      <Text style={fsStyles.instrucoes}>
        Instruções: Use caneta azul ou preta. Preencha completamente a bolinha correspondente à sua resposta.
        Não use corretivo. Rasuras invalidam a questão.
      </Text>

      {/* Grid de bolinhas */}
      {grupos.map((grupo, gi) => (
        <View key={gi}>
          <View style={fsStyles.gridRow}>
            {grupo.map((q, qi) => (
              <View key={qi} style={fsStyles.celula}>
                <Text style={fsStyles.celulaNum}>{gi * FR_COLS + qi + 1}</Text>
                <View style={fsStyles.celulaOpcoes}>
                  {['A', 'B', 'C', 'D', 'E'].map(l => (
                    <View key={l} style={fsStyles.bolinha}>
                      <Text style={fsStyles.bolinhaLetra}>{l}</Text>
                    </View>
                  ))}
                </View>
              </View>
            ))}
            {/* Preenche células vazias na última linha */}
            {Array.from({ length: FR_COLS - grupo.length }).map((_, i) => (
              <View key={`empty-${i}`} style={[fsStyles.celula]} />
            ))}
          </View>
          {gi % 4 === 3 && <View style={fsStyles.separadorLinha} />}
        </View>
      ))}

      {/* Gabarito (opcional — incluso apenas no exemplar do professor) */}
      {incluirGabarito && (
        <View style={fsStyles.gabarito}>
          <Text style={fsStyles.gabTitulo}>Gabarito</Text>
          <View style={fsStyles.gabRow}>
            {questoes.map((q, i) => (
              <View key={i} style={fsStyles.gabCell}>
                <Text style={fsStyles.gabNum}>{i + 1}</Text>
                <Text style={fsStyles.gabLetra}>
                  {q.anulada ? '—' : (q.gabarito ?? '?')}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </Page>
  )
}

// ── Documento principal ───────────────────────────────────────────────────

interface SimuladoPDFProps {
  questoes:        QuestaoSimulado[]
  simulado:        SimuladoInfo
  incluirGabarito: boolean
}

export function SimuladoPDF({ questoes, simulado, incluirGabarito }: SimuladoPDFProps) {
  const titulo = `SIMULADO HenryJr #${simulado.id}`
  const data   = fmtData(simulado.criado_em)
  const tipo   = simulado.tipo === 'completo'
    ? 'Simulado Completo ENEM'
    : simulado.tipo === 'tira-teima'
      ? 'Tira Teima'
      : `Simulado — ${simulado.tipo}`

  // Divide questões em 2 colunas por página
  // ~8 questões por coluna, ~16 por página (estimativa conservadora)
  const QUESTOES_POR_PAGINA = 10
  const paginas: QuestaoSimulado[][] = []
  for (let i = 0; i < questoes.length; i += QUESTOES_POR_PAGINA) {
    paginas.push(questoes.slice(i, i + QUESTOES_POR_PAGINA))
  }
  const metade = Math.ceil(questoes.length / 2)
  const colEsq = questoes.slice(0, metade)
  const colDir  = questoes.slice(metade)

  return (
    <Document
      title={titulo}
      author="HenryJr — Banco de Questões ENEM"
      subject={tipo}
    >
      {/* Página de questões (2 colunas, paginação automática) */}
      <Page size="A4" style={s.page}>
        <CabecalhoPagina titulo={titulo} data={data} tipo={tipo} />

        <View style={s.cols}>
          {/* Coluna esquerda */}
          <View style={s.col}>
            {colEsq.map((q, i) => (
              <Questao key={q.id} q={q} seq={i + 1} />
            ))}
          </View>

          {/* Divisória central */}
          <View style={{ width: 0.5, backgroundColor: C.border }} />

          {/* Coluna direita */}
          <View style={s.col}>
            {colDir.map((q, i) => (
              <Questao key={q.id} q={q} seq={metade + i + 1} />
            ))}
          </View>
        </View>

        {/* Rodapé */}
        <View style={s.footer} fixed>
          <Text style={s.footerText}>{titulo} · {data}</Text>
          <Text style={s.footerText}>henryjr.vercel.app</Text>
        </View>
      </Page>

      {/* Folha de respostas (página separada) */}
      <FolhaRespostas
        questoes={questoes}
        simuladoId={simulado.id}
        data={data}
        incluirGabarito={incluirGabarito}
      />
    </Document>
  )
}
