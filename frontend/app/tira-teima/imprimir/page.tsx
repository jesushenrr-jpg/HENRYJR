import { createClient } from '@/lib/supabase/server'
import { redirect }     from 'next/navigation'
import TiraTeimaPrint  from './TiraTeimaPrint'

interface Props { searchParams: Promise<{ view?: string; gabarito?: string }> }

export default async function TiraTeimaImprimirPage({ searchParams }: Props) {
  const { view, gabarito } = await searchParams
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user && view !== '1') redirect('/auth/login')
  if (!user) return <div className="nao-implementado p-8 text-center text-white/40">Sessão expirada. Faça login novamente.</div>

  const incluirGabarito = gabarito === 'true'

  // Busca questões erradas com dados completos
  const { data: erradas } = await supabase
    .from('questoes_erradas')
    .select(`
      questao_id, acertou, respondido_em,
      questoes ( id, ano, numero, dia, area, competencia, enunciado, comando, alternativas, gabarito, tem_imagem, imagens )
    `)
    .eq('usuario_id', user.id)
    .order('respondido_em', { ascending: false })

  type QuestaoErrada = {
    questao_id: number
    acertou: boolean | null
    respondido_em: string
    questoes: {
      id: number; ano: number; numero: number; dia: string; area: string
      competencia: string | null; enunciado: string[]; comando: string
      alternativas: Record<string, string>; gabarito: string | null
      tem_imagem: boolean
      imagens: Array<{ path: string; posicao: string; supabase_url?: string }>
    } | null
  }

  const lista = ((erradas ?? []) as unknown as QuestaoErrada[])
    .filter(r => r.acertou === false || r.acertou === null)
    .filter(r => r.questoes !== null)

  const questoes = lista.map(r => r.questoes!).filter(Boolean)

  return (
    <TiraTeimaPrint
      questoes={questoes}
      incluirGabarito={incluirGabarito}
      usuario={user.email ?? 'Aluno'}
      dataGeracao={new Date().toLocaleDateString('pt-BR')}
    />
  )
}
