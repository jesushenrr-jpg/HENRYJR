export interface Prova {
  id: string          // 'ENEM' | 'EXATO' | futuras
  nome: string
  descricao: string
  cor: string         // CSS color
  corDark: string
  bg: string          // classe tailwind bg
  text: string        // classe tailwind text
  border: string
  anos?: number[]     // só ENEM usa anos
  eventos?: string[]  // só EXATO usa eventos
}

export const PROVAS: Prova[] = [
  {
    id: 'ENEM',
    nome: 'ENEM',
    descricao: 'Exame Nacional do Ensino Médio',
    cor: '#3B82F6',
    corDark: '#1D4ED8',
    bg: 'bg-blue-500/15',
    text: 'text-blue-300',
    border: 'border-blue-500/30',
    anos: Array.from({ length: 16 }, (_, i) => 2024 - i),
  },
  {
    id: 'EXATO',
    nome: 'EXATO',
    descricao: 'Simulados TESSAT/EXATO',
    cor: '#F59E0B',
    corDark: '#B45309',
    bg: 'bg-amber-500/15',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    eventos: ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS'],
  },
]

export const PROVA_MAP = Object.fromEntries(PROVAS.map(p => [p.id, p]))

// Label amigável para eventos EXATO
export const EVENTO_LABEL: Record<string, string> = {
  'CICLO_ZERO':          'Ciclo Zero',
  '1_SIMULADO_TESSAT':   '1º Simulado',
  '2_SIMULADO_TESSAT':   '2º Simulado',
  'OUTUBRO_2025':        'Outubro 2025',
  'ABRIL_2026':          'Abril 2026',
  'NATUREZAS_TESSAT':    'Naturezas',
  'TRADICIONAIS':        'Tradicionais',
}
