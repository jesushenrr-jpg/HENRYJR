# PROVA × SIMULADO — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `tipo TEXT` column to `questoes` distinguishing `'PROVA'` (official past exams) from `'SIMULADO'` (predictive originals), expose a "Todos · Provas · Simulados" toggle on the home page, questões listing, and simulado creation, and add a parallel TIPO combobox to the CORRETOR.

**Architecture:** `tipo` is a per-question field, orthogonal to `fonte`. ENEM and EXATO may both contain questions of either type. URL search param `?tipo=PROVA|SIMULADO` (absent = all) drives the toggle on the web; local dropdown state drives the CORRETOR. No changes to `lib/provas.ts` — fontes and tipos are independent axes.

**Tech Stack:** PostgreSQL/Supabase REST, Next.js 14 App Router (Server Components + Client Components), React hooks (`useRouter`, `useSearchParams`, `usePathname`), Python/tkinter (CORRETOR), PyInstaller.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `migracao_tipo.sql` | Create | One-time SQL migration for Supabase |
| `frontend/components/TipoToggle.tsx` | Create | Shared "Todos · Provas · Simulados" pill toggle (Client Component, URL-driven) |
| `frontend/components/FiltroSidebar.tsx` | Modify | Add `tipoAtivo` prop, render TipoToggle, preserve `tipo` in all filter URLs |
| `frontend/app/questoes/page.tsx` | Modify | Read `tipo` from searchParams, filter Supabase query, pass to sidebar |
| `frontend/app/page.tsx` | Modify | Read `tipo`, filter card counts, render TipoToggle in Suspense |
| `frontend/app/simulado/page.tsx` | Modify | Add local `tipo` state, render inline pills, pass to API |
| `frontend/app/api/simulado/criar/route.ts` | Modify | Accept `tipo` body param, filter questões pool |
| `data_layer.py` | Modify | `buscar_questoes()` gains optional `tipo` param |
| `ui_questoes.py` | Modify | Add TIPO combobox in header, pass tipo to `buscar_questoes()` |

---

## Task 1: SQL migration file

**Files:**
- Create: `migracao_tipo.sql` (project root `C:\PROJETOS\HENRYJR\`)

- [ ] **Step 1: Create the migration file**

```sql
-- migracao_tipo.sql
-- Execução: Supabase Dashboard → SQL Editor → Run
-- Todos os comandos são idempotentes (podem ser re-executados sem efeito colateral).

-- 1. Adiciona coluna tipo
ALTER TABLE questoes
  ADD COLUMN IF NOT EXISTS tipo TEXT NOT NULL DEFAULT 'PROVA';

-- 2. Backfill: ENEM = provas passadas, EXATO = simulados preditivos
UPDATE questoes SET tipo = 'PROVA'    WHERE fonte = 'ENEM';
UPDATE questoes SET tipo = 'SIMULADO' WHERE fonte = 'EXATO';

-- 3. Índice para filtros rápidos
CREATE INDEX IF NOT EXISTS idx_questoes_tipo ON questoes(tipo);
```

- [ ] **Step 2: Execute no Supabase Dashboard**

Acesse **https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh** → SQL Editor → cole o conteúdo acima → clique em **Run**.

Resultado esperado:
```
ALTER TABLE
UPDATE 2880
UPDATE 460
CREATE INDEX
```

- [ ] **Step 3: Verificar**

No SQL Editor, rode:
```sql
SELECT tipo, COUNT(*) FROM questoes GROUP BY tipo;
```
Resultado esperado:
```
 tipo     | count
----------+-------
 PROVA    |  2880
 SIMULADO |   460
```

- [ ] **Step 4: Commit do arquivo SQL**

```bash
git add migracao_tipo.sql
git commit -m "feat: adiciona migration tipo PROVA/SIMULADO na tabela questoes"
```

---

## Task 2: TipoToggle component

**Files:**
- Create: `frontend/components/TipoToggle.tsx`

- [ ] **Step 1: Criar o componente**

```tsx
// frontend/components/TipoToggle.tsx
'use client'

import { useRouter, useSearchParams, usePathname } from 'next/navigation'

const OPCOES = [
  { label: 'Todos',     value: '' },
  { label: 'Provas',    value: 'PROVA' },
  { label: 'Simulados', value: 'SIMULADO' },
]

export default function TipoToggle() {
  const router    = useRouter()
  const pathname  = usePathname()
  const sp        = useSearchParams()
  const tipoAtivo = sp.get('tipo') ?? ''

  function setTipo(value: string) {
    const params = new URLSearchParams(sp.toString())
    if (value) params.set('tipo', value)
    else       params.delete('tipo')
    router.push(`${pathname}?${params}`)
  }

  return (
    <div className="inline-flex rounded-lg border border-[#2C2820] overflow-hidden bg-[#161411]">
      {OPCOES.map(({ label, value }) => {
        const ativo = tipoAtivo === value
        return (
          <button
            key={value || 'todos'}
            onClick={() => setTipo(value)}
            className={`px-4 py-2 text-[12px] font-semibold uppercase tracking-wider transition ${
              ativo
                ? 'bg-[#D4A853]/15 text-[#D4A853] border-b-2 border-[#D4A853]/50'
                : 'text-[#635D56] hover:text-[#9E9589]'
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/TipoToggle.tsx
git commit -m "feat: cria componente TipoToggle (Todos/Provas/Simulados)"
```

---

## Task 3: FiltroSidebar — adicionar suporte a tipo

**Files:**
- Modify: `frontend/components/FiltroSidebar.tsx`

Alterações:
1. Importar `TipoToggle`
2. Adicionar `tipoAtivo?: string` na interface Props
3. Preservar `tipo` na função `url()`
4. Incluir `tipoAtivo` no `hasFilter`
5. Renderizar `TipoToggle` acima das tabs de fonte

- [ ] **Step 1: Atualizar FiltroSidebar.tsx**

```tsx
// frontend/components/FiltroSidebar.tsx
'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useTransition } from 'react'
import { COMPETENCIAS, TODAS_HABILIDADES } from '@/lib/competencias'
import { EVENTO_LABEL } from '@/lib/provas'
import TipoToggle from '@/components/TipoToggle'

interface Props {
  anos: number[]
  areas: string[]
  anoAtivo?: number
  diaAtivo?: string
  areaAtiva?: string
  competenciaAtiva?: string
  fonteAtiva?: string
  eventoAtivo?: string
  turnoAtivo?: string
  tipoAtivo?: string          // ← novo
}

const AREA_META: Record<string, { label: string; bg: string; text: string; border: string }> = {
  'Linguagens, Codigos e suas Tecnologias':   { label: 'Linguagens',  bg: 'bg-sky-500/15',     text: 'text-sky-300',     border: 'border-sky-500/30' },
  'Ciencias Humanas e suas Tecnologias':      { label: 'Humanas',     bg: 'bg-amber-500/15',   text: 'text-amber-300',   border: 'border-amber-500/30' },
  'Ciencias da Natureza e suas Tecnologias':  { label: 'C. Natureza', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  'Matematica e suas Tecnologias':            { label: 'Matemática',  bg: 'bg-violet-500/15',  text: 'text-violet-300',  border: 'border-violet-500/30' },
}

const EVENTOS_EXATO = ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS']

export default function FiltroSidebar({
  anos, areas, anoAtivo, diaAtivo, areaAtiva, competenciaAtiva,
  fonteAtiva = 'ENEM', eventoAtivo, turnoAtivo, tipoAtivo,  // ← tipoAtivo adicionado
}: Props) {
  const [anosExpandido, setAnosExpandido] = useState(false)
  const [compExpandido,  setCompExpandido] = useState(false)
  const pathname = usePathname()
  const router   = useRouter()
  const [, startTransition] = useTransition()

  const isExato = fonteAtiva === 'EXATO'

  function url(overrides: Record<string, string | undefined>) {
    const p: Record<string, string> = {}
    if (fonteAtiva)       p.fonte       = fonteAtiva
    if (anoAtivo)         p.ano         = String(anoAtivo)
    if (diaAtivo)         p.dia         = diaAtivo
    if (areaAtiva)        p.area        = areaAtiva
    if (competenciaAtiva) p.competencia = competenciaAtiva
    if (eventoAtivo)      p.evento      = eventoAtivo
    if (turnoAtivo)       p.turno       = turnoAtivo
    if (tipoAtivo)        p.tipo        = tipoAtivo    // ← preserva tipo
    for (const [k, v] of Object.entries(overrides)) {
      if (v === undefined) delete p[k]
      else p[k] = v
    }
    return `${pathname}?${new URLSearchParams(p)}`
  }

  function nav(href: string) {
    startTransition(() => router.push(href))
  }

  function switchFonte(fonte: string) {
    // Mantém tipo ao trocar fonte, limpa outros filtros
    const params: Record<string, string> = { fonte }
    if (tipoAtivo) params.tipo = tipoAtivo
    startTransition(() => router.push(`${pathname}?${new URLSearchParams(params)}`))
  }

  const anosVisiveis = anosExpandido ? anos : anos.slice(0, 8)
  const habilidades  = compExpandido ? TODAS_HABILIDADES : TODAS_HABILIDADES.slice(0, 15)

  const hasFilter = isExato
    ? (eventoAtivo || turnoAtivo || areaAtiva || tipoAtivo)
    : (anoAtivo || diaAtivo || areaAtiva || competenciaAtiva || tipoAtivo)

  return (
    <div className="space-y-3">

      {/* Toggle Tipo — acima das tabs de fonte */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#635D56]">Tipo</span>
        <TipoToggle />
      </div>

      {/* Tabs de prova */}
      <div className="flex rounded-xl overflow-hidden border border-[#2C2820] bg-[#161411]">
        <button
          onClick={() => switchFonte('ENEM')}
          className={`flex-1 py-2.5 text-[12px] font-bold uppercase tracking-wider transition ${
            !isExato
              ? 'bg-blue-500/15 text-blue-300 border-b-2 border-blue-500/50'
              : 'text-[#635D56] hover:text-[#9E9589]'
          }`}
        >
          ENEM
        </button>
        <button
          onClick={() => switchFonte('EXATO')}
          className={`flex-1 py-2.5 text-[12px] font-bold uppercase tracking-wider transition ${
            isExato
              ? 'bg-amber-500/15 text-amber-300 border-b-2 border-amber-500/50'
              : 'text-[#635D56] hover:text-[#9E9589]'
          }`}
        >
          EXATO
        </button>
      </div>

      <div className="rounded-xl bg-[#161411] border border-[#2C2820] divide-y divide-[#2C2820]">

        {/* ── Filtros EXATO ── */}
        {isExato && (
          <>
            {/* Evento */}
            <FilterGroup title="Evento">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!eventoAtivo} onClick={() => nav(url({ evento: undefined }))}>
                  Todos
                </Chip>
                {EVENTOS_EXATO.map(e => (
                  <Chip
                    key={e}
                    active={eventoAtivo === e}
                    onClick={() => nav(url({ evento: eventoAtivo === e ? undefined : e }))}
                    colorClass={eventoAtivo === e ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : ''}
                  >
                    {EVENTO_LABEL[e] ?? e}
                  </Chip>
                ))}
              </div>
            </FilterGroup>

            {/* Turno */}
            <FilterGroup title="Turno">
              <div className="flex gap-1.5">
                <Chip active={!turnoAtivo}            onClick={() => nav(url({ turno: undefined }))}>Todos</Chip>
                <Chip active={turnoAtivo === 'MANHA'} onClick={() => nav(url({ turno: turnoAtivo === 'MANHA' ? undefined : 'MANHA' }))}>Manhã</Chip>
                <Chip active={turnoAtivo === 'TARDE'} onClick={() => nav(url({ turno: turnoAtivo === 'TARDE' ? undefined : 'TARDE' }))}>Tarde</Chip>
              </div>
            </FilterGroup>

            {/* Área (EXATO) */}
            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined }))}>Todas</Chip>
                {areas.map(a => {
                  const m = AREA_META[a]
                  const ativo = areaAtiva === a
                  return (
                    <Chip
                      key={a}
                      active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}
                    >
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>
          </>
        )}

        {/* ── Filtros ENEM ── */}
        {!isExato && (
          <>
            {/* Área */}
            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined, competencia: undefined }))}>
                  Todas
                </Chip>
                {areas.map(a => {
                  const m = AREA_META[a]
                  const ativo = areaAtiva === a
                  return (
                    <Chip
                      key={a}
                      active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a, competencia: undefined }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}
                    >
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>

            {/* Ano */}
            <FilterGroup title="Ano">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!anoAtivo} onClick={() => nav(url({ ano: undefined }))}>Todos</Chip>
                {anosVisiveis.map(y => (
                  <Chip
                    key={y}
                    active={anoAtivo === y}
                    onClick={() => nav(url({ ano: anoAtivo === y ? undefined : String(y) }))}
                  >
                    {y}
                  </Chip>
                ))}
              </div>
              {anos.length > 8 && (
                <button
                  onClick={() => setAnosExpandido(v => !v)}
                  className="mt-2 text-[10px] text-[#635D56] hover:text-[#9E9589] transition"
                >
                  {anosExpandido ? '▲ menos' : `▼ +${anos.length - 8} anos`}
                </button>
              )}
            </FilterGroup>

            {/* Dia */}
            <FilterGroup title="Dia">
              <div className="flex gap-1.5">
                <Chip active={!diaAtivo}           onClick={() => nav(url({ dia: undefined }))}>Todos</Chip>
                <Chip active={diaAtivo === 'dia1'} onClick={() => nav(url({ dia: diaAtivo === 'dia1' ? undefined : 'dia1' }))}>1º Dia</Chip>
                <Chip active={diaAtivo === 'dia2'} onClick={() => nav(url({ dia: diaAtivo === 'dia2' ? undefined : 'dia2' }))}>2º Dia</Chip>
              </div>
            </FilterGroup>

            {/* Competência */}
            <FilterGroup title="Competência H01–H30">
              <div className="flex flex-wrap gap-1">
                <Chip small active={!competenciaAtiva} onClick={() => nav(url({ competencia: undefined }))}>Todas</Chip>
                {habilidades.map(h => (
                  <Chip
                    key={h}
                    small
                    active={competenciaAtiva === h}
                    onClick={() => nav(url({ competencia: competenciaAtiva === h ? undefined : h }))}
                    title={COMPETENCIAS[h]?.descricao}
                  >
                    {h}
                  </Chip>
                ))}
              </div>
              <button
                onClick={() => setCompExpandido(v => !v)}
                className="mt-2 text-[10px] text-[#635D56] hover:text-[#9E9589] transition"
              >
                {compExpandido ? '▲ menos' : `▼ ver H16–H30`}
              </button>
            </FilterGroup>
          </>
        )}
      </div>

      {/* Atalho limpar */}
      {hasFilter && (
        <Link
          href={`${pathname}?fonte=${fonteAtiva}`}
          className="block text-center text-[11px] text-[#635D56] hover:text-rose-400 transition py-1"
        >
          ✕ Limpar filtros
        </Link>
      )}
    </div>
  )
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="p-3.5">
      <div className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#635D56] mb-2.5">{title}</div>
      {children}
    </div>
  )
}

function Chip({
  active, onClick, children, colorClass = '', small = false, title,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
  colorClass?: string
  small?: boolean
  title?: string
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`${small ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-[11px]'} rounded-md font-medium transition border ${
        active
          ? (colorClass || 'bg-[#D4A853]/15 text-[#D4A853] border-[#D4A853]/30')
          : 'bg-[#1E1B17] text-[#9E9589] border-transparent hover:bg-[#2C2820] hover:text-[#F2EDE4]'
      }`}
    >
      {children}
    </button>
  )
}
```

- [ ] **Step 2: Verificar que o arquivo não tem erros de TypeScript**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Esperado: sem erros relacionados a FiltroSidebar ou TipoToggle.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/FiltroSidebar.tsx
git commit -m "feat: FiltroSidebar recebe tipoAtivo, preserva tipo na URL, renderiza TipoToggle"
```

---

## Task 4: questoes/page.tsx — filtro de tipo

**Files:**
- Modify: `frontend/app/questoes/page.tsx`

Alterações: adicionar `tipo` a SearchParams, filtrar query, passar para FiltroSidebar, preservar em paginaUrl e formulário de busca.

- [ ] **Step 1: Atualizar questoes/page.tsx**

Localizar e atualizar cada trecho conforme abaixo:

**1.1 — SearchParams (linhas 8-19):** adicionar `tipo?: string`

```tsx
interface SearchParams {
  ano?: string
  dia?: string
  area?: string
  competencia?: string
  busca?: string
  ia?: string
  pagina?: string
  fonte?: string
  evento?: string
  turno?: string
  tipo?: string           // ← novo
}
```

**1.2 — Extração de parâmetros (após linha 55):** adicionar extração de tipo

```tsx
const tipo        = params.tipo as 'PROVA' | 'SIMULADO' | undefined
```

**1.3 — Query principal:** adicionar filtro de tipo após o filtro de área (após `if (area) query = query.eq('area', area)`)

```tsx
// Filtro de tipo (PROVA | SIMULADO)
if (tipo) query = query.eq('tipo', tipo)
```

**1.4 — Função paginaUrl:** preservar tipo na paginação

```tsx
function paginaUrl(p: number) {
  const sp = new URLSearchParams()
  sp.set('fonte', fonte)
  if (!isExato) {
    if (ano)         sp.set('ano', String(ano))
    if (dia)         sp.set('dia', dia)
    if (competencia) sp.set('competencia', competencia)
  } else {
    if (evento) sp.set('evento', evento)
    if (turno)  sp.set('turno', turno)
  }
  if (area)          sp.set('area', area)
  if (buscaRaw)      sp.set('busca', buscaRaw)
  if (isIA)          sp.set('ia', '1')
  if (tipo)          sp.set('tipo', tipo)    // ← novo
  if (p > 1)         sp.set('pagina', String(p))
  return `/questoes?${sp}`
}
```

**1.5 — FiltroSidebar no JSX:** passar tipoAtivo

```tsx
<FiltroSidebar
  anos={ANOS}
  areas={AREAS}
  anoAtivo={ano}
  diaAtivo={dia}
  areaAtiva={area}
  competenciaAtiva={competencia}
  fonteAtiva={fonte}
  eventoAtivo={evento}
  turnoAtivo={turno}
  tipoAtivo={tipo}          // ← novo
/>
```

**1.6 — Formulário de busca textual:** adicionar hidden input de tipo

Dentro do `<form method="get" action="/questoes">`, após os outros hidden inputs:

```tsx
{tipo && <input type="hidden" name="tipo" value={tipo} />}
```

**1.7 — Botão "limpar filtros":** incluir tipo na condição

```tsx
{!isIA && (ano || dia || area || competencia || buscaRaw || evento || turno || tipo) && (
  <Link href={`/questoes?fonte=${fonte}`} className="text-[11px] text-[#635D56] hover:text-[#F2EDE4] transition">
    limpar filtros
  </Link>
)}
```

- [ ] **Step 2: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/questoes/page.tsx
git commit -m "feat: questoes/page filtra por tipo na query e passa tipoAtivo para sidebar"
```

---

## Task 5: Home page — TipoToggle e filtro de cards

**Files:**
- Modify: `frontend/app/page.tsx`

Alterações: adicionar `searchParams` ao componente, filtrar contagens por tipo, mostrar TipoToggle acima dos cards, ocultar cards com 0 questões quando tipo é filtrado.

- [ ] **Step 1: Atualizar frontend/app/page.tsx**

```tsx
import { Suspense } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { FRASES_CAPA } from '@/lib/frases-capa'
import TipoToggle from '@/components/TipoToggle'

const FEATURES = [
  // ... (inalterado — manter como está)
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

  // Links das cards incluem tipo quando ativo
  const hrefEnem  = tipo ? `/questoes?fonte=ENEM&tipo=${tipo}`  : '/questoes?fonte=ENEM'
  const hrefExato = tipo ? `/questoes?fonte=EXATO&tipo=${tipo}` : '/questoes?fonte=EXATO'

  return (
    <main className="anim-fade">

      {/* ── HERO ── */}
      {/* ... (manter inalterado até a section "ESCOLHA SUA PROVA") */}

      {/* ── ESCOLHA SUA PROVA ── */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="mb-8 text-center">
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-[#F2EDE4] mb-2">Escolha sua prova</h2>
          <p className="text-sm text-[#635D56]">Cada banco tem filtros, estilo e contexto próprios</p>

          {/* Toggle de tipo acima dos cards */}
          <div className="flex justify-center mt-4">
            <Suspense fallback={null}>
              <TipoToggle />
            </Suspense>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">

          {/* Card ENEM — oculto quando tipo='SIMULADO' e count=0 */}
          {(totalEnem ?? 0) > 0 && (
            <Link
              href={hrefEnem}
              className="group relative overflow-hidden rounded-2xl border border-blue-500/20 bg-[#161411] hover:border-blue-500/40 p-7 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              {/* ... conteúdo interno ENEM inalterado, exceto {nEnem} que agora reflete o count filtrado */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/8 to-blue-500/0 opacity-60 group-hover:opacity-100 transition pointer-events-none" />
              <div className="relative">
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
                  <span className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-blue-300 group-hover:translate-x-0.5 transition">→</span>
                </div>
              </div>
            </Link>
          )}

          {/* Card EXATO — oculto quando tipo='PROVA' e count=0 */}
          {(totalExato ?? 0) > 0 && (
            <Link
              href={hrefExato}
              className="group relative overflow-hidden rounded-2xl border border-amber-500/20 bg-[#161411] hover:border-amber-500/40 p-7 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-amber-500/8 to-amber-500/0 opacity-60 group-hover:opacity-100 transition pointer-events-none" />
              <div className="relative">
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
                  <span className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-300 group-hover:translate-x-0.5 transition">→</span>
                </div>
              </div>
            </Link>
          )}
        </div>
      </section>

      {/* ── RECURSOS ── */}
      {/* ... (inalterado) */}
    </main>
  )
}
```

> **Atenção:** A home page atual tem todos os detalhes inline. Reescreva o arquivo completo preservando o conteúdo das seções HERO e RECURSOS sem alteração — apenas a seção "ESCOLHA SUA PROVA" muda estruturalmente (searchParams + buildCount + Suspense + condicional).

- [ ] **Step 2: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Esperado: sem erros.

- [ ] **Step 3: Testar localmente**

```bash
cd frontend && npm run dev
```

Acesse `http://localhost:3000`. Clique em "Provas" → deve ocultar o card EXATO. Clique em "Simulados" → deve ocultar o card ENEM. Clique em "Todos" → ambos aparecem.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "feat: home filtra cards por tipo com TipoToggle acima da seção"
```

---

## Task 6: simulado/page.tsx — filtro de tipo

**Files:**
- Modify: `frontend/app/simulado/page.tsx`
- Modify: `frontend/app/api/simulado/criar/route.ts`

A página de simulado é Client Component e já usa estado local para todos os filtros. Adicionamos `tipo` como estado local (mesmo padrão de `area`, `prova`, etc.) e passamos para a API.

- [ ] **Step 1: Atualizar simulado/page.tsx**

Adicionar estado `tipo` e pills de seleção antes do bloco de configuração de prova:

**1.1 — Adicionar estado:**

```tsx
const [tipo, setTipo] = useState<'' | 'PROVA' | 'SIMULADO'>('')
```

**1.2 — Adicionar pills de tipo** (inserir antes do bloco de seleção de prova, após o h1/header da página):

```tsx
{/* Tipo de questão */}
<div className="mb-6">
  <p className="text-[12px] font-bold uppercase tracking-wider text-[#635D56] mb-3">Tipo de questão</p>
  <div className="inline-flex rounded-lg border border-[#2C2820] overflow-hidden bg-[#161411]">
    {([
      { label: 'Todos',     value: '' as const },
      { label: 'Provas',    value: 'PROVA' as const },
      { label: 'Simulados', value: 'SIMULADO' as const },
    ] as const).map(({ label, value }) => (
      <button
        key={value || 'todos'}
        onClick={() => setTipo(value)}
        className={`px-4 py-2 text-[12px] font-semibold uppercase tracking-wider transition ${
          tipo === value
            ? 'bg-[#D4A853]/15 text-[#D4A853] border-b-2 border-[#D4A853]/50'
            : 'text-[#635D56] hover:text-[#9E9589]'
        }`}
      >
        {label}
      </button>
    ))}
  </div>
</div>
```

**1.3 — Passar tipo para a API** na função `criar()`:

```tsx
async function criar() {
  setErro('')
  setLoading(true)
  try {
    const res = await fetch('/api/simulado/criar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        area:       area || undefined,
        ano_inicio: anoInicio,
        ano_fim:    anoFim,
        quantidade,
        tipo:       tipo || undefined,    // ← novo: undefined = todos
      }),
    })
    // ... resto inalterado
  }
}
```

- [ ] **Step 2: Atualizar a API route**

```ts
// frontend/app/api/simulado/criar/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export const runtime = 'edge'

export async function POST(req: NextRequest) {
  try {
    const { area, ano_inicio, ano_fim, competencia, quantidade, tipo } = await req.json()

    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return NextResponse.json({ error: 'Não autenticado' }, { status: 401 })

    await supabase.from('usuarios').upsert({ id: user.id }, { onConflict: 'id' })

    let query = supabase
      .from('questoes')
      .select('id')
      .eq('anulada', false)

    if (area)        query = query.eq('area', area)
    if (competencia) query = query.eq('competencia', competencia)
    if (ano_inicio)  query = query.gte('ano', Number(ano_inicio))
    if (ano_fim)     query = query.lte('ano', Number(ano_fim))
    if (tipo)        query = query.eq('tipo', tipo)    // ← novo

    const { data: pool, error: poolErr } = await query
    if (poolErr) return NextResponse.json({ error: poolErr.message }, { status: 500 })
    if (!pool || pool.length === 0) {
      return NextResponse.json({ error: 'Nenhuma questão encontrada com esses filtros.' }, { status: 404 })
    }

    const n = Math.min(Number(quantidade) || 10, pool.length)
    const shuffled = pool.sort(() => Math.random() - 0.5).slice(0, n)
    const ids = shuffled.map(q => q.id)

    const { data: sim, error: simErr } = await supabase
      .from('simulados')
      .insert({
        usuario_id:     user.id,
        tipo:           'online',
        filtros:        { area, ano_inicio, ano_fim, competencia, tipo_questao: tipo },  // ← salva tipo_questao para não conflitar com campo tipo
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
```

> **Nota:** O campo `tipo` na tabela `simulados` já existe com valor `'online'` e é diferente do `tipo` da questão. No payload de inserção do simulado, o tipo de questão é salvo dentro de `filtros.tipo_questao` para não conflitar.

- [ ] **Step 3: Verificar TypeScript**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/simulado/page.tsx frontend/app/api/simulado/criar/route.ts
git commit -m "feat: simulado/page adiciona filtro de tipo; API filtra pool por tipo"
```

---

## Task 7: data_layer.py — parâmetro tipo em buscar_questoes

**Files:**
- Modify: `C:\PROJETOS\HENRYJR\data_layer.py`

- [ ] **Step 1: Atualizar assinatura e corpo de `buscar_questoes()`**

Localizar a função `buscar_questoes` (linha 111) e substituir:

```python
def buscar_questoes(fonte: str, filtros: dict) -> list[dict]:
```

por:

```python
def buscar_questoes(fonte: str, filtros: dict, tipo: str | None = None) -> list[dict]:
    """
    Retorna lista leve de questões (sem enunciado/alternativas) para navegação.
    filtros para ENEM:  {"ano": 2023, "dia": "dia1"}
    filtros para EXATO: {"evento": "CICLO_ZERO", "turno": "MANHA"}
    tipo: 'PROVA' | 'SIMULADO' | None (todos)
    """
    params: dict[str, Any] = {
        "select": "id,numero,area,competencia,tem_imagem,gabarito,anulada",
        "fonte": f"eq.{fonte}",
        "order": "numero.asc",
        "limit": 500,
    }
    if fonte == "ENEM":
        params["ano"] = f"eq.{filtros.get('ano')}"
        params["dia"] = f"eq.{filtros.get('dia')}"
    else:
        if filtros.get("evento"):
            params["evento"] = f"eq.{filtros['evento']}"
        if filtros.get("turno"):
            params["turno"] = f"eq.{filtros['turno']}"

    if tipo:                                          # ← novo
        params["tipo"] = f"eq.{tipo}"

    r = requests.get(_rest("questoes"), headers=_headers(), params=params, timeout=15)
    return r.json() if r.ok else []
```

- [ ] **Step 2: Verificar sintaxe**

```bash
cd C:\PROJETOS\HENRYJR && python -c "import data_layer; print('OK')"
```

Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add data_layer.py
git commit -m "feat: buscar_questoes() aceita parâmetro opcional tipo='PROVA'|'SIMULADO'"
```

---

## Task 8: ui_questoes.py — combobox TIPO no cabeçalho

**Files:**
- Modify: `C:\PROJETOS\HENRYJR\ui_questoes.py`

Alterações:
1. Adicionar combobox TIPO no cabeçalho após o DIA
2. Passar tipo para `buscar_questoes()` em `_load_questoes()`

- [ ] **Step 1: Adicionar combobox TIPO no cabeçalho**

Localizar o bloco que termina em (linha ~622-623):
```python
        self._cb_f2.pack(side="left", padx=(0, 6))
        self._cb_f2.bind("<<ComboboxSelected>>", self._load_questoes)
```

Inserir logo após:

```python
        tk.Label(hdr_inner, text="│", bg=C.CARD, fg=C.CARD[:-2]+"20",
                 font=("Segoe UI", 14)).pack(side="left", padx=2)

        tk.Label(hdr_inner, text="TIPO", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(4, 3))
        self._var_tipo = tk.StringVar(value="Todos")
        self._cb_tipo  = ttk.Combobox(hdr_inner, textvariable=self._var_tipo,
                                      state="readonly", width=10,
                                      font=("Segoe UI", 9))
        self._cb_tipo["values"] = ["Todos", "PROVA", "SIMULADO"]
        self._cb_tipo.pack(side="left", padx=(0, 6))
        self._cb_tipo.bind("<<ComboboxSelected>>", self._load_questoes)
```

- [ ] **Step 2: Atualizar _load_questoes para passar tipo**

Localizar a função `_load_questoes` (linha ~997) e o trecho onde chama `dl.buscar_questoes`:

```python
    def _load_questoes(self, _=None):
        cat = self._cat_atual
        f1  = self._var_f1.get()
```

Dentro dessa função, antes da chamada a `dl.buscar_questoes`, adicionar a extração do tipo:

```python
        tipo_sel = self._var_tipo.get()
        tipo = None if tipo_sel == "Todos" else tipo_sel
```

E atualizar a chamada de `buscar_questoes`:

```python
        questoes = dl.buscar_questoes(cat, filtros, tipo=tipo)
```

> A chamada atual provavelmente usa `filtros` como segundo argumento. Adicione `tipo=tipo` como terceiro argumento.

- [ ] **Step 3: Verificar sintaxe**

```bash
cd C:\PROJETOS\HENRYJR && python -c "import ui_questoes; print('OK')"
```

Esperado: `OK` (pode falhar se tkinter não tiver display disponível — nesse caso, erro de display é aceitável, erro de sintaxe não é).

- [ ] **Step 4: Commit**

```bash
git add ui_questoes.py
git commit -m "feat: ui_questoes adiciona combobox TIPO paralelo ao DIA; passa tipo para buscar_questoes"
```

---

## Task 9: CORRETOR — rebuild do .exe

**Files:**
- `C:\PROJETOS\HENRYJR\dist\corretor\` (regenerado)

- [ ] **Step 1: Matar o processo do CORRETOR se estiver rodando**

```powershell
Stop-Process -Name "corretor" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
```

- [ ] **Step 2: Remover dist e build anteriores**

```powershell
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
```

- [ ] **Step 3: Rebuild**

```powershell
python -m PyInstaller corretor.spec
```

Aguardar conclusão (~2-4 minutos). Esperado: `Building EXE from EXE-00.toc completed successfully.`

- [ ] **Step 4: Testar o executável**

```powershell
.\dist\corretor\corretor.exe
```

Verificar:
- A janela abre corretamente
- Na aba Questões, o cabeçalho mostra: `QUESTÕES | PROVA: [ENEM] | ANO: [...] | DIA: [...] | TIPO: [Todos]`
- Selecionar "PROVA" no combobox TIPO e carregar questões — deve funcionar normalmente
- Selecionar "SIMULADO" e trocar para EXATO — deve retornar questões EXATO

- [ ] **Step 5: Commit do spec (se o spec foi alterado)**

Se `corretor.spec` não foi alterado nesta sessão, este step é desnecessário. Se foi, commitar:

```bash
git add corretor.spec
git commit -m "chore: corretor.spec atualizado para rebuild com tipo combobox"
```

---

## Checklist de auto-revisão

### Cobertura do spec

| Requisito do spec | Tarefa que implementa |
|---|---|
| Migration `ALTER TABLE questoes ADD COLUMN tipo` | Task 1 |
| Backfill ENEM→PROVA, EXATO→SIMULADO | Task 1 |
| Índice em `tipo` | Task 1 |
| `provas.ts` sem alteração | ✓ não tocado |
| Componente `TipoToggle` com pills Todos/Provas/Simulados | Task 2 |
| URL como fonte de verdade; preserva outros params | Task 2, Task 3 |
| Paleta Biblioteca Cálida; pill ativo = dourado | Task 2 |
| Home: TipoToggle acima dos cards | Task 5 |
| Home: cards sem questões do tipo ficam ocultos | Task 5 |
| Questões: TipoToggle no topo da sidebar | Task 3 |
| Questões: `tipo` adicionado ao query Supabase | Task 4 |
| Questões: tabs de fonte permanecem visíveis | Task 3 (tabs mantidas) |
| Questões: tipo preservado na paginação | Task 4 |
| Simulado: TipoToggle no topo do formulário | Task 6 |
| Simulado: API filtra pool por tipo | Task 6 |
| CORRETOR: `buscar_questoes()` aceita `tipo` opcional | Task 7 |
| CORRETOR: combobox TIPO paralelo no cabeçalho | Task 8 |
| CORRETOR: rebuild do .exe | Task 9 |

### Consistência de tipos

- `tipo: str | None` em `data_layer.py:buscar_questoes()` — consistente com `"Todos"→None, "PROVA"→"PROVA"` em `ui_questoes.py`
- `tipo?: 'PROVA' | 'SIMULADO' | undefined` nos componentes React — consistente entre `questoes/page.tsx`, `FiltroSidebar.tsx` (prop), `TipoToggle.tsx` (URL lida como string)
- `tipo` no body da API `/api/simulado/criar` → `if (tipo) query.eq('tipo', tipo)` — consistente com o que o cliente envia

### Fora do escopo (não implementado aqui)

- Edição do `tipo` de questões já existentes via CORRETOR
- Filtro de `tipo` no Tira Teima e no Progresso
- Constraint `CHECK` no banco
