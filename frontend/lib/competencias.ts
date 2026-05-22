export interface Competencia {
  codigo: string
  descricao: string
  area: string
}

export const COMPETENCIAS: Record<string, Competencia> = {
  H01: { codigo: 'H01', area: 'Linguagens', descricao: 'Identificar as diferentes linguagens e seus recursos expressivos como elementos de caracterização dos campos de atividade humana.' },
  H02: { codigo: 'H02', area: 'Linguagens', descricao: 'Reconhecer e usar língua(s) e linguagem(ns) em diferentes situações e contextos de produção.' },
  H03: { codigo: 'H03', area: 'Linguagens', descricao: 'Relacionar informações geradas nos sistemas de comunicação e informação, considerando a função social dos processos comunicativos.' },
  H04: { codigo: 'H04', area: 'Linguagens', descricao: 'Reconhecer a língua portuguesa como representação histórica e social da realidade.' },
  H05: { codigo: 'H05', area: 'Linguagens', descricao: 'Analisar e interpretar criticamente a linguagem das mídias levando em conta seus sistemas de comunicação e as condições de produção e recepção das mensagens.' },
  H06: { codigo: 'H06', area: 'Linguagens', descricao: 'Aplicar tecnologias da comunicação e da informação em situações relevantes.' },
  H07: { codigo: 'H07', area: 'Linguagens', descricao: 'Confrontar opiniões e pontos de vista sobre as diferentes linguagens e suas manifestações específicas.' },
  H08: { codigo: 'H08', area: 'Linguagens', descricao: 'Compreender e usar a língua portuguesa como língua materna, geradora de significação e integradora da organização do mundo e da própria identidade.' },
  H09: { codigo: 'H09', area: 'Linguagens', descricao: 'Entender os princípios das tecnologias associadas à linguagem.' },
  H10: { codigo: 'H10', area: 'Linguagens', descricao: 'Entender a natureza da linguagem como fenômeno humano.' },
  H11: { codigo: 'H11', area: 'Humanas', descricao: 'Reconstituir a trajetória histórica e espacial da humanidade em suas múltiplas dimensões.' },
  H12: { codigo: 'H12', area: 'Humanas', descricao: 'Contextualizar e comparar diferentes épocas e civilizações.' },
  H13: { codigo: 'H13', area: 'Humanas', descricao: 'Reconhecer e relativizar as concepções de espaço, tempo e cultura.' },
  H14: { codigo: 'H14', area: 'Humanas', descricao: 'Analisar situações problematizadoras envolvendo aspectos sociais, econômicos, políticos e culturais.' },
  H15: { codigo: 'H15', area: 'Humanas', descricao: 'Dominar os princípios de pesquisa em Ciências Humanas.' },
  H16: { codigo: 'H16', area: 'Humanas', descricao: 'Utilizar os conhecimentos históricos, geográficos e sociais para compreender o mundo.' },
  H17: { codigo: 'H17', area: 'Humanas', descricao: 'Compreender a organização do espaço geográfico e as transformações do território.' },
  H18: { codigo: 'H18', area: 'Humanas', descricao: 'Identificar e analisar as relações de poder nos processos históricos e sociais.' },
  H19: { codigo: 'H19', area: 'Humanas', descricao: 'Analisar as relações entre ética, cidadania e democracia.' },
  H20: { codigo: 'H20', area: 'Humanas', descricao: 'Compreender fenômenos socioculturais e a diversidade das formas de vida.' },
  H21: { codigo: 'H21', area: 'Natureza', descricao: 'Reconhecer mecanismos e fenômenos de natureza físico-química e biológica.' },
  H22: { codigo: 'H22', area: 'Natureza', descricao: 'Associar intervenções humanas ao impacto sobre o ambiente.' },
  H23: { codigo: 'H23', area: 'Natureza', descricao: 'Aplicar conhecimentos físicos, químicos e biológicos para análise de situações práticas.' },
  H24: { codigo: 'H24', area: 'Natureza', descricao: 'Relacionar informações para interpretar experimentos e dados científicos.' },
  H25: { codigo: 'H25', area: 'Natureza', descricao: 'Avaliar propostas de intervenção no ambiente com base em conhecimentos científicos.' },
  H26: { codigo: 'H26', area: 'Natureza', descricao: 'Compreender a interação entre ciência, tecnologia e sociedade.' },
  H27: { codigo: 'H27', area: 'Natureza', descricao: 'Entender as bases biológicas da hereditariedade e evolução.' },
  H28: { codigo: 'H28', area: 'Natureza', descricao: 'Aplicar princípios de química e física a substâncias e reações do cotidiano.' },
  H29: { codigo: 'H29', area: 'Natureza', descricao: 'Reconhecer os princípios de saúde, saneamento e qualidade de vida.' },
  H30: { codigo: 'H30', area: 'Natureza', descricao: 'Compreender fenômenos energéticos, elétricos, magnéticos e ondas.' },
}

export const TODAS_HABILIDADES = Object.keys(COMPETENCIAS) as (keyof typeof COMPETENCIAS)[]
