import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const questaoId = Number(body.questao_id)
    const respostaUsuario = String(body.resposta_usuario ?? '').toUpperCase()

    if (!Number.isInteger(questaoId) || questaoId <= 0 || !/^[A-E]$/.test(respostaUsuario)) {
      return NextResponse.json({ error: 'Resposta inválida' }, { status: 400 })
    }

    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    // Sem usuário logado: ignora silenciosamente (guest mode)
    if (!user) return NextResponse.json({ ok: true, guest: true })

    // Dados canônicos vêm do banco; o cliente não pode declarar o gabarito.
    const { data: questao, error: questaoError } = await supabase
      .from('questoes')
      .select('id, ano, dia, numero, area, gabarito, anulada')
      .eq('id', questaoId)
      .single()

    if (questaoError || !questao || questao.anulada || !questao.gabarito) {
      return NextResponse.json({ error: 'Questão inválida' }, { status: 404 })
    }

    const acertou = respostaUsuario === questao.gabarito

    // Upsert: se respondeu a mesma questão antes, atualiza
    const { error } = await supabase.from('questoes_erradas').upsert({
      usuario_id:      user.id,
      questao_id:       questao.id,
      ano:              questao.ano,
      dia:              questao.dia,
      numero:           questao.numero,
      area:             questao.area,
      resposta_usuario: respostaUsuario,
      gabarito:         questao.gabarito,
      acertou,
      respondido_em:   new Date().toISOString(),
    }, {
      onConflict: 'usuario_id,ano,dia,numero',
    })

    if (error) {
      console.error('resposta upsert error:', error)
      return NextResponse.json({ error: 'Não foi possível salvar a resposta' }, { status: 500 })
    }

    return NextResponse.json({ ok: true, acertou })
  } catch (e) {
    console.error('resposta route error:', e)
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
