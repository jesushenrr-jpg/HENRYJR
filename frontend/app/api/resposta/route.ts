import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  try {
    const { questao_id, ano, dia, numero, area, resposta_usuario, gabarito } = await req.json()

    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    // Sem usuário logado: ignora silenciosamente (guest mode)
    if (!user) return NextResponse.json({ ok: true, guest: true })

    const acertou = resposta_usuario === gabarito

    // Upsert: se respondeu a mesma questão antes, atualiza
    const { error } = await supabase.from('questoes_erradas').upsert({
      usuario_id:      user.id,
      questao_id:      questao_id ?? null,
      ano,
      dia,
      numero,
      area,
      resposta_usuario,
      gabarito,
      acertou,
      respondido_em:   new Date().toISOString(),
    }, {
      onConflict: 'usuario_id,ano,dia,numero',
    })

    if (error) {
      console.error('resposta upsert error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    return NextResponse.json({ ok: true, acertou })
  } catch (e) {
    console.error('resposta route error:', e)
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
