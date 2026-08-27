export interface Prova {
  id: string          // 'ENEM' | 'EXATO' | 'UFT' | 'PAES' | 'UNICAMP' | 'FUVEST' | 'UNESP'
  nome: string
  descricao: string
  cor: string         // CSS color
  corDark: string
  bg: string          // classe tailwind bg
  text: string        // classe tailwind text
  border: string
  anos?: number[]     // anos disponíveis (ENEM, UFT, PAES, UNICAMP, FUVEST, UNESP)
  eventos?: string[]  // eventos disponíveis (EXATO)
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
    descricao: 'Simulados e Provas TESSAT/EXATO',
    cor: '#F59E0B',
    corDark: '#B45309',
    bg: 'bg-amber-500/15',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    eventos: ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS'],
  },
  {
    id: 'UFT',
    nome: 'UFT',
    descricao: 'Vestibular da UFT (2018–2024)',
    cor: '#10B981',
    corDark: '#059669',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-300',
    border: 'border-emerald-500/30',
    anos: Array.from({ length: 7 }, (_, i) => 2018 + i),
  },
  {
    id: 'PAES',
    nome: 'PAES',
    descricao: 'Vestibular da UEMA (2020–2025)',
    cor: '#F43F5E',
    corDark: '#BE123C',
    bg: 'bg-rose-500/15',
    text: 'text-rose-300',
    border: 'border-rose-500/30',
    anos: [2020, 2021, 2022, 2023, 2024, 2025],
  },
  {
    id: 'UNICAMP',
    nome: 'UNICAMP',
    descricao: '1ª Fase UNICAMP (2023–2026)',
    cor: '#8B5CF6',
    corDark: '#6D28D9',
    bg: 'bg-violet-500/15',
    text: 'text-violet-300',
    border: 'border-violet-500/30',
    anos: [2023, 2024, 2026],
  },
  {
    id: 'FUVEST',
    nome: 'FUVEST',
    descricao: '1ª Fase FUVEST (2023–2026)',
    cor: '#0EA5E9',
    corDark: '#0369A1',
    bg: 'bg-sky-500/15',
    text: 'text-sky-300',
    border: 'border-sky-500/30',
    anos: [2023, 2024, 2025, 2026],
  },
  {
    id: 'UNESP',
    nome: 'UNESP',
    descricao: '1ª Fase UNESP (2017–2026)',
    cor: '#F97316',
    corDark: '#C2410C',
    bg: 'bg-orange-500/15',
    text: 'text-orange-300',
    border: 'border-orange-500/30',
    anos: [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
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
  // ENEM simulados
  'SIM_00': 'Sim. 00', 'SIM_01': 'Sim. 01', 'SIM_02': 'Sim. 02',
  'SIM_03': 'Sim. 03', 'SIM_04': 'Sim. 04', 'SIM_05': 'Sim. 05',
  'SIM_06': 'Sim. 06', 'SIM_07': 'Sim. 07', 'SIM_08': 'Sim. 08',
  // UFT edições
  '1_EDICAO': '1ª Edição', '2_EDICAO': '2ª Edição',
}

// Label para campo 'dia' (inclui simu_dia1/simu_dia2 de ENEM simulados)
export const DIA_LABEL: Record<string, string> = {
  'dia1':      '1º Dia',
  'dia2':      '2º Dia',
  'simu_dia1': '1º Dia',
  'simu_dia2': '2º Dia',
}

// Label para provedores de simulados ENEM
export const PROVEDOR_LABEL: Record<string, string> = {
  'BERNOULLI':    'Bernoulli',
  'SAS':          'SAS',
  'POLIEDRO':     'Poliedro',
  'FARIAS_BRITO': 'Farias Brito',
  'SOMOS':        'Somos',
}
