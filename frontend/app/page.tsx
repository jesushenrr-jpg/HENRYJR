import Link from 'next/link'
import { Suspense } from 'react'
import { createClient } from '@/lib/supabase/server'
import { FRASES_CAPA } from '@/lib/frases-capa'
import TipoToggle from '@/components/TipoToggle'

const FEATURES = [
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3l1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2z"/>
      </svg>
    ),
    title: 'Busca por IA',
    desc: 'Encontre questões por tema com linguagem natural.',
    tag: 'IA',
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="20" x2="12" y2="10"/>
        <line x1="18" y1="20" x2="18" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="16"/>
      </svg>
    ),
    title: 'Progresso por competência',
    desc: 'H01–H30 acompanhados de perto.',
    tag: null,
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
    ),
    title: 'Tira Teima',
    desc: 'Caderno de erros automático — repita até zerar.',
    tag: null,
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 8v4l3 3"/>
      </svg>
    ),
    title: 'Simulado cronometrado',
    desc: 'Condições reais com correção automática.',
    tag: null,
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    title: 'Explicação com IA',
    desc: 'Gabarito comentado em tempo real pelo LLaMA 3.',
    tag: 'IA',
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
      </svg>
    ),
    title: 'PDF original',
    desc: 'Questão direto no PDF oficial hospedado.',
    tag: null,
  },
]

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ tipo?: string }>
}) {
  const { tipo } = await searchParams
  const supabase = await createClient()
  const frase = FRASES_CAPA[new Date().getFullYear() % FRASES_CAPA.length]

  // Conta questões por fonte com filtro de tipo opcional
  function buildCount(fonte: string) {
    let q = supabase
      .from('questoes')
      .select('*', { count: 'exact', head: true })
      .eq('fonte', fonte)
    if (tipo) q = q.eq('tipo', tipo)
    return q
  }

  const [
    { count: totalEnem },
    { count: totalExato },
  ] = await Promise.all([
    buildCount('ENEM'),
    buildCount('EXATO'),
  ])

  const nEnem  = (totalEnem  ?? 0).toLocaleString('pt-BR')
  const nExato = (totalExato ?? 0).toLocaleString('pt-BR')

  // Links dos cards incluem tipo quando ativo
  const hrefEnem  = tipo ? `/questoes?fonte=ENEM&tipo=${tipo}`  : '/questoes?fonte=ENEM'
  const hrefExato = tipo ? `/questoes?fonte=EXATO&tipo=${tipo}` : '/questoes?fonte=EXATO'

  return (
    <main className="anim-fade">

      {/* ── HERO ── */}
      <section className="relative overflow-hidden border-b border-[#2C2820]">
        {/* Glows quentes */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 w-[500px] h-[500px] rounded-full bg-[#D4A853]/8 blur-[140px] pulse-glow" />
          <div
            className="absolute bottom-0 right-1/4 w-[380px] h-[380px] rounded-full bg-[#D4A853]/5 blur-[120px] pulse-glow"
            style={{ animationDelay: '1.5s' }}
          />
        </div>

        <div className="relative max-w-5xl mx-auto px-6 pt-16 sm:pt-24 pb-14 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-[#D4A853]/10 border border-[#D4A853]/20 text-[#D4A853] text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4A853] pulse-glow" />
            Plataforma gratuita · Sem propaganda
          </div>

          {/* H1 com fonte editorial */}
          <h1 className="font-display text-4xl sm:text-6xl font-bold tracking-tight leading-[1.1] mb-5 text-[#F2EDE4]">
            Estude como se a aprovação<br />
            <span className="italic text-[#D4A853]">já fosse certa.</span>
          </h1>

          <p className="text-base sm:text-lg text-[#9E9589] max-w-xl mx-auto mb-9 leading-relaxed">
            Banco completo de questões ENEM e simulados EXATO com IA, progresso por competência e Tira Teima.
          </p>

          {/* Frase da capa */}
          <blockquote className="max-w-lg mx-auto mb-8 px-5 py-3.5 rounded-xl bg-[#161411] border border-[#2C2820]">
            <p className="font-serif text-[13px] italic text-[#9E9589] leading-relaxed">
              &ldquo;{frase.frase}&rdquo;
            </p>
            {frase.autor && (
              <footer className="text-[11px] text-[#635D56] mt-1.5 not-italic">— {frase.autor}</footer>
            )}
          </blockquote>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/questoes?fonte=ENEM"
              className="px-5 py-3 rounded-xl bg-[#D4A853] hover:bg-[#B8882A] text-[#0E0D0B] font-semibold text-sm shadow-lg shadow-[#D4A853]/20 transition flex items-center gap-2"
            >
              Começar a praticar
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </Link>
            <Link
              href="/progresso"
              className="px-5 py-3 rounded-xl bg-[#161411] hover:bg-[#1E1B17] border border-[#2C2820] hover:border-[#4A3F2F] text-[#9E9589] font-semibold text-sm transition"
            >
              Ver meu progresso
            </Link>
          </div>
        </div>
      </section>

      {/* ── ESCOLHA SUA PROVA ── */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="mb-8 text-center">
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-[#F2EDE4] mb-2">Escolha sua prova</h2>
          <p className="text-sm text-[#635D56]">Cada banco tem filtros, estilo e contexto próprios</p>
          {/* Toggle de tipo */}
          <div className="flex justify-center mt-4">
            <Suspense fallback={null}>
              <TipoToggle />
            </Suspense>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

          {/* Card ENEM */}
          {(totalEnem ?? 0) > 0 && (
            <Link
              href={hrefEnem}
              className="group relative overflow-hidden rounded-2xl border border-blue-500/20 bg-[#161411] hover:border-blue-500/40 p-7 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/8 to-blue-500/0 opacity-60 group-hover:opacity-100 transition pointer-events-none" />
              <div className="relative">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-blue-500/15 border border-blue-500/25 text-blue-300 text-[11px] font-bold uppercase tracking-wider mb-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  ENEM
                </div>

                <h3 className="font-display text-xl font-bold text-[#F2EDE4] mb-1 leading-tight">
                  Exame Nacional<br />do Ensino Médio
                </h3>
                <p className="text-[13px] text-[#635D56] mb-5 leading-relaxed">
                  {nEnem} questões · 2009–2024 · 4 áreas · 30 competências
                </p>

                <div className="grid grid-cols-2 gap-2 mb-5">
                  {['Linguagens', 'Humanas', 'C. Natureza', 'Matemática'].map(a => (
                    <div key={a} className="text-[11px] text-blue-300/70 bg-blue-500/8 rounded-md px-2.5 py-1.5 border border-blue-500/15">
                      {a}
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-blue-300">Estudar ENEM</span>
                  <span className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-blue-300 group-hover:translate-x-0.5 transition">
                    →
                  </span>
                </div>
              </div>
            </Link>
          )}

          {/* Card EXATO */}
          {(totalExato ?? 0) > 0 && (
            <Link
              href={hrefExato}
              className="group relative overflow-hidden rounded-2xl border border-amber-500/20 bg-[#161411] hover:border-amber-500/40 p-7 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/8 to-amber-500/0 opacity-60 group-hover:opacity-100 transition pointer-events-none" />
              <div className="relative">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/25 text-amber-300 text-[11px] font-bold uppercase tracking-wider mb-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  EXATO
                </div>

                <h3 className="font-display text-xl font-bold text-[#F2EDE4] mb-1 leading-tight">
                  Simulados<br />TESSAT / EXATO
                </h3>
                <p className="text-[13px] text-[#635D56] mb-5 leading-relaxed">
                  {nExato} questões · 12 simulados · Ciclo Zero ao Abril 2026
                </p>

                <div className="grid grid-cols-2 gap-2 mb-5">
                  {['Ciclo Zero', '1º Simulado', '2º Simulado', 'Outubro 2025'].map(e => (
                    <div key={e} className="text-[11px] text-amber-300/70 bg-amber-500/8 rounded-md px-2.5 py-1.5 border border-amber-500/15">
                      {e}
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-amber-300">Estudar EXATO</span>
                  <span className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-300 group-hover:translate-x-0.5 transition">
                    →
                  </span>
                </div>
              </div>
            </Link>
          )}
        </div>
      </section>

      {/* ── RECURSOS ── */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="border-t border-[#2C2820] pt-12">
          <h2 className="font-display text-xl font-bold text-[#F2EDE4] mb-6">Recursos da plataforma</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {FEATURES.map(f => (
              <div
                key={f.title}
                className="rounded-xl bg-[#161411] border border-[#2C2820] p-4 hover:border-[#4A3F2F] transition"
              >
                <div className="flex items-start gap-3">
                  <div className="shrink-0 w-8 h-8 rounded-lg bg-[#D4A853]/10 text-[#D4A853] flex items-center justify-center">
                    {f.icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <p className="text-[13px] font-semibold text-[#F2EDE4]">{f.title}</p>
                      {f.tag && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-[#D4A853]/15 text-[#D4A853] font-bold border border-[#D4A853]/20">
                          {f.tag}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-[#635D56] leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

    </main>
  )
}
