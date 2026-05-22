export interface ImagemQuestao {
  path: string
  posicao: string
  supabase_url?: string
}

export interface Questao {
  id: number
  numero: number
  ano: number
  dia: 'dia1' | 'dia2'
  area: string
  competencia: string | null
  enunciado: string[]
  comando: string | null
  alternativas: Record<string, string>
  gabarito: string | null
  confianca: number | null
  revisado: boolean
  anulada: boolean
  tem_imagem: boolean
  pagina_pdf: number | null
  imagens: ImagemQuestao[]
  imagens_alternativas: Record<string, string> | null
}

export type LetraAlternativa = 'A' | 'B' | 'C' | 'D' | 'E'

export interface FiltroQuestoes {
  ano?: number
  dia?: 'dia1' | 'dia2'
  area?: string
  competencia?: string
  tem_imagem?: boolean
  anulada?: boolean
}

export const AREAS = [
  'Linguagens, Codigos e suas Tecnologias',
  'Ciencias Humanas e suas Tecnologias',
  'Ciencias da Natureza e suas Tecnologias',
  'Matematica e suas Tecnologias',
] as const

export const ANOS = Array.from({ length: 16 }, (_, i) => 2009 + i)

export function urlPdf(ano: number, dia: string, pagina?: number | null): string {
  const base = `https://bmhudlpihwxvaelokugh.supabase.co/storage/v1/object/public/provas-pdf/${ano}/${dia}.pdf`
  return pagina != null ? `${base}#page=${pagina + 1}` : base
}
