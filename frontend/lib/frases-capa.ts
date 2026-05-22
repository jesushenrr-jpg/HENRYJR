export interface FraseCapa {
  ano: number
  frase: string
  autor?: string
}

export const FRASES_CAPA: FraseCapa[] = [
  { ano: 2009, frase: 'A educação é a arma mais poderosa que você pode usar para mudar o mundo.', autor: 'Nelson Mandela' },
  { ano: 2010, frase: 'A maior recompensa para o trabalho do homem não é o que ele ganha com isso, mas o que ele se torna com isso.', autor: 'John Ruskin' },
  { ano: 2011, frase: 'O analfabeto do século XXI não será aquele que não consegue ler e escrever, mas aquele que não consegue aprender, desaprender e reaprender.', autor: 'Alvin Toffler' },
  { ano: 2012, frase: 'Ninguém ignora tudo. Ninguém sabe tudo. Todos nós sabemos alguma coisa. Todos nós ignoramos alguma coisa.', autor: 'Paulo Freire' },
  { ano: 2013, frase: 'A única maneira de fazer um excelente trabalho é amar o que você faz.', autor: 'Steve Jobs' },
  { ano: 2014, frase: 'O sucesso é a soma de pequenos esforços repetidos dia após dia.', autor: 'Robert Collier' },
  { ano: 2015, frase: 'A imaginação é mais importante que o conhecimento.', autor: 'Albert Einstein' },
  { ano: 2016, frase: 'Cada dia é uma nova oportunidade para aprender algo novo e mudar sua perspectiva.', autor: 'Provérbio' },
  { ano: 2017, frase: 'O conhecimento é o único bem que se multiplica quando dividido.', autor: 'Provérbio' },
  { ano: 2018, frase: 'Estude como se você fosse viver para sempre; viva como se você fosse morrer amanhã.', autor: 'Mahatma Gandhi' },
  { ano: 2019, frase: 'O segredo do sucesso é a constância do propósito.', autor: 'Benjamin Disraeli' },
  { ano: 2020, frase: 'A persistência é o caminho do êxito.', autor: 'Charles Chaplin' },
  { ano: 2021, frase: 'O presente é o resultado de todas as nossas escolhas passadas. O futuro é construído pelas escolhas que faremos agora.', autor: 'Provérbio' },
  { ano: 2022, frase: 'Não existe um caminho para a felicidade. A felicidade é o caminho.', autor: 'Mahatma Gandhi' },
  { ano: 2023, frase: 'A educação não muda o mundo, a educação muda as pessoas que vão mudar o mundo.', autor: 'Paulo Freire' },
  { ano: 2024, frase: 'Aqueles que não conseguem lembrar o passado estão condenados a repeti-lo.', autor: 'George Santayana' },
]

export function getFraseAleatoria(): FraseCapa {
  return FRASES_CAPA[Math.floor(Math.random() * FRASES_CAPA.length)]
}

export function getFrasePorAno(ano: number): FraseCapa | undefined {
  return FRASES_CAPA.find(f => f.ano === ano)
}
