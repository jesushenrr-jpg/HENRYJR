import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'edge'

// POST /api/simulado/submeter
// Body: { simulado_id, respostas: { [questao_id]: 'A'|'B'|'C'|'D'|'E'|null } }
export async function POST(req: NextRequest) {
  try {
    const { simulado_id, respostas } = await req.json()
    if (!simulado_id || !respostas) {
      return NextResponse.json({ error: 'Parâmetros inválidos' }, { status: 400 })
    }

    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })

    // Verifica que o simulado pertence ao usuário
    const { data: sim } = await supabase
      .from('simulados')
      .select('id, questoes_ids, status')
      .eq('id', simulado_id)
      .eq('usuario_id', user.id)
      .single()

    if (!sim) return NextResponse.json({ error: 'Simulado não encontrado' }, { status: 404 })
    if (sim.status === 'concluido') {
      return NextResponse.json({ error: 'Simulado já concluído' }, { status: 400 })
    }

    // Busca as questões para checar gabaritos
    const ids: number[] = sim.questoes_ids
    const { data: questoes } = await supabase
      .from('questoes')
      .select('id, questao_id:id, gabarito, ano, dia, numero, area')
      .in('id', ids)

    if (!questoes) return NextResponse.json({ error: 'Erro ao buscar questões' }, { status: 500 })

    // Monta respostas_simulado
    const registros = questoes.map(q => ({
      simulado_id: simulado_id,
      questao_id:  q.id,
      resposta:    respostas[q.id] ?? null,
      correta:     respostas[q.id] != null && respostas[q.id] === q.gabarito,
    }))

    const { error: rErr } = await supabase
      .from('respostas_simulado')
      .upsert(registros, { onConflict: 'simulado_id,questao_id' })

    if (rErr) return NextResponse.json({ error: rErr.message }, { status: 500 })

    const acertos = registros.filter(r => r.correta).length

    // Atualiza simulado
    await supabase
      .from('simulados')
      .update({
        acertos,
        status:       'concluido',
        concluido_em: new Date().toISOString(),
      })
      .eq('id', simulado_id)

    // Atualiza questoes_erradas com cada questão respondida
    // Tenta o schema novo; se falhar, tenta o schema antigo
    for (const q of questoes) {
      const resposta = respostas[q.id] ?? null
      const acertou  = resposta != null && resposta === q.gabarito

      const payload = {
        usuario_id:      user.id,
        questao_id:      q.id,
        simulado_id:     simulado_id,
        ano:             q.ano,
        dia:             q.dia,
        numero:          q.numero,
        area:            q.area,
        resposta_usuario: resposta,
        gabarito:        q.gabarito,
        acertou,
        respondido_em:   new Date().toISOString(),
      }

      const { error: eErr } = await supabase
        .from('questoes_erradas')
        .upsert(payload, { onConflict: 'usuario_id,ano,dia,numero' })

      if (eErr && eErr.code === '42703') {
        // Schema antigo: usa resposta_dada
        await supabase.from('questoes_erradas').upsert(
          { usuario_id: user.id, questao_id: q.id, simulado_id, resposta_dada: resposta },
          { onConflict: 'questao_id,usuario_id' }
        )
      }
    }

    const total = questoes.length
    const pct   = total > 0 ? Math.round((acertos / total) * 100) : 0

    return NextResponse.json({ ok: true, acertos, total, pct, simulado_id })
  } catch (e) {
    console.error(e)
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
