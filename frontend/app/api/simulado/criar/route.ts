import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'edge'

export async function POST(req: NextRequest) {
  try {
    const { area, ano_inicio, ano_fim, competencia, quantidade } = await req.json()

    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })

    // Garante perfil do usuário
    await supabase.from('usuarios').upsert({ id: user.id }, { onConflict: 'id' })

    // Monta query
    let query = supabase
      .from('questoes')
      .select('id')
      .eq('anulada', false)

    if (area)       query = query.eq('area', area)
    if (competencia) query = query.eq('competencia', competencia)
    if (ano_inicio)  query = query.gte('ano', Number(ano_inicio))
    if (ano_fim)     query = query.lte('ano', Number(ano_fim))

    const { data: pool, error: poolErr } = await query
    if (poolErr) return NextResponse.json({ error: poolErr.message }, { status: 500 })
    if (!pool || pool.length === 0) {
      return NextResponse.json({ error: 'Nenhuma questão encontrada com esses filtros.' }, { status: 404 })
    }

    // Embaralha e pega N questões
    const n = Math.min(Number(quantidade) || 10, pool.length)
    const shuffled = pool.sort(() => Math.random() - 0.5).slice(0, n)
    const ids = shuffled.map(q => q.id)

    // Cria simulado
    const { data: sim, error: simErr } = await supabase
      .from('simulados')
      .insert({
        usuario_id:     user.id,
        tipo:           'online',
        filtros:        { area, ano_inicio, ano_fim, competencia },
        questoes_ids:   ids,
        total_questoes: ids.length,
        status:         'em_andamento',
      })
      .select('id')
      .single()

    if (simErr) return NextResponse.json({ error: simErr.message }, { status: 500 })

    return NextResponse.json({ simulado_id: sim.id, questoes_ids: ids })
  } catch (e) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
