export interface Prova {
  id: string          // 'ENEM' | 'EXATO' | 'UFT' | futuras
  nome: string
  descricao: string
  cor: string         // CSS color
  corDark: string
  bg: string          // classe tailwind bg
  text: string        // classe tailwind text
  border: string
  anos?: number[]     // só ENEM e UFT usam anos
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
