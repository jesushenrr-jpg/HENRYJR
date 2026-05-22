import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  try {
    const { questao_id, ano, dia, numero, tipo_erro, descricao } = await req.json()

    if (!ano || !dia || !numero || !tipo_erro) {
      return NextResponse.json({ error: 'Campos obrigatórios ausentes' }, { status: 400 })
    }

    const supabase = await createClient()

    const { error } = await supabase.from('relatorios_erros').insert({
      questao_id: questao_id ?? null,
      ano,
      dia,
      numero,
      tipo_erro,
      descricao: descricao?.trim() || null,
      status: 'pendente',
    })

    if (error) {
      console.error('Supabase insert error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    return NextResponse.json({ ok: true })
  } catch (e) {
    console.error('reportar route error:', e)
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
