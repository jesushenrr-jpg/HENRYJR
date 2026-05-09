import { createClient } from '@/lib/supabase/server'
import CardQuestao from '@/components/CardQuestao'
import FiltroQuestoes from '@/components/FiltroQuestoes'
import type { Questao } from '@/lib/types'
import { AREAS, ANOS } from '@/lib/types'

interface SearchParams {
  ano?: string
  dia?: string
  area?: string
  pagina?: string
}

const POR_PAGINA = 10

export default async function QuestoesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>
}) {
  const params = await searchParams
  const supabase = await createClient()

  const ano = params.ano ? parseInt(params.ano) : undefined
  const dia = params.dia as 'dia1' | 'dia2' | undefined
  const area = params.area
  const pagina = params.pagina ? parseInt(params.pagina) : 1
  const offset = (pagina - 1) * POR_PAGINA

  let query = supabase
    .from('questoes')
    .select('*', { count: 'exact' })
    .eq('anulada', false)
    .order('ano', { ascending: false })
    .order('numero', { ascending: true })
    .range(offset, offset + POR_PAGINA - 1)

  if (ano) query = query.eq('ano', ano)
  if (dia) query = query.eq('dia', dia)
  if (area) query = query.eq('area', area)

  const { data: questoes, count } = await query
  const total = count ?? 0
  const totalPaginas = Math.ceil(total / POR_PAGINA)

  return (
    <main className="min-h-screen bg-[#1e1e2e] text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-[#7c6af7] mb-2">Banco de Questões</h1>
        <p className="text-[#a6adc8] mb-8">
          {total.toLocaleString('pt-BR')} questão{total !== 1 ? 'ões' : ''} encontrada{total !== 1 ? 's' : ''}
        </p>

        <FiltroQuestoes anos={ANOS} areas={AREAS as unknown as string[]} />

        <div className="space-y-6 mt-8">
          {questoes?.map(q => (
            <CardQuestao key={q.id} questao={q as Questao} />
          ))}
        </div>

        {/* Paginação */}
        {totalPaginas > 1 && (
          <div className="flex justify-center gap-2 mt-10">
            {Array.from({ length: Math.min(totalPaginas, 10) }, (_, i) => {
              const p = i + 1
              const sp = new URLSearchParams()
              if (ano) sp.set('ano', String(ano))
              if (dia) sp.set('dia', dia)
              if (area) sp.set('area', area)
              sp.set('pagina', String(p))
              return (
                <a
                  key={p}
                  href={`/questoes?${sp}`}
                  className={`w-9 h-9 flex items-center justify-center rounded-lg text-sm font-bold transition ${
                    p === pagina
                      ? 'bg-[#7c6af7] text-white'
                      : 'bg-[#313244] text-[#a6adc8] hover:bg-[#45475a]'
                  }`}
                >
                  {p}
                </a>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
