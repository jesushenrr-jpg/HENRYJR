'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useTransition } from 'react'
import { COMPETENCIAS, TODAS_HABILIDADES } from '@/lib/competencias'
import { EVENTO_LABEL, PROVA_MAP, PROVEDOR_LABEL } from '@/lib/provas'
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
  tipoAtivo?: string
  provedorAtivo?: string
}

const AREA_META: Record<string, { label: string; bg: string; text: string; border: string }> = {
  'Linguagens, Codigos e suas Tecnologias':   { label: 'Linguagens',  bg: 'bg-sky-500/15',     text: 'text-sky-300',     border: 'border-sky-500/30' },
  'Ciencias Humanas e suas Tecnologias':      { label: 'Humanas',     bg: 'bg-amber-500/15',   text: 'text-amber-300',   border: 'border-amber-500/30' },
  'Ciencias da Natureza e suas Tecnologias':  { label: 'C. Natureza', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  'Matematica e suas Tecnologias':            { label: 'Matemática',  bg: 'bg-violet-500/15',  text: 'text-violet-300',  border: 'border-violet-500/30' },
}

const EVENTOS_EXATO = ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS']
const PROVEDORES     = ['BERNOULLI', 'SAS', 'POLIEDRO', 'FARIAS_BRITO', 'SOMOS']
const EDICOES_UFT    = ['1_EDICAO', '2_EDICAO']

export default function FiltroSidebar({
  anos, areas, anoAtivo, diaAtivo, areaAtiva, competenciaAtiva,
  fonteAtiva = 'ENEM', eventoAtivo, turnoAtivo, tipoAtivo, provedorAtivo,
}: Props) {
  const [anosExpandido, setAnosExpandido] = useState(false)
  const [compExpandido,  setCompExpandido] = useState(false)
  const pathname = usePathname()
  const router   = useRouter()
  const [, startTransition] = useTransition()

  const isExato    = fonteAtiva === 'EXATO'
  const isUFT      = fonteAtiva === 'UFT'
  const isEnem     = fonteAtiva === 'ENEM'
  const isSimulado = tipoAtivo === 'SIMULADO'

  function url(overrides: Record<string, string | undefined>) {
    const p: Record<string, string> = {}
    if (fonteAtiva)       p.fonte       = fonteAtiva
    if (anoAtivo)         p.ano         = String(anoAtivo)
    if (diaAtivo)         p.dia         = diaAtivo
    if (areaAtiva)        p.area        = areaAtiva
    if (competenciaAtiva) p.competencia = competenciaAtiva
    if (eventoAtivo)      p.evento      = eventoAtivo
    if (turnoAtivo)       p.turno       = turnoAtivo
    if (tipoAtivo)        p.tipo        = tipoAtivo
    if (provedorAtivo)    p.provedor    = provedorAtivo
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
    const params: Record<string, string> = { fonte }
    if (tipoAtivo) params.tipo = tipoAtivo
    startTransition(() => router.push(`${pathname}?${new URLSearchParams(params)}`))
  }

  const anosParaExibir = isUFT ? (PROVA_MAP['UFT']?.anos ?? []) : anos
  const anosVisiveis   = anosExpandido ? anosParaExibir : anosParaExibir.slice(0, 8)
  const habilidades    = compExpandido ? TODAS_HABILIDADES : TODAS_HABILIDADES.slice(0, 15)

  const hasFilter = isExato
    ? (eventoAtivo || turnoAtivo || areaAtiva || tipoAtivo)
    : isUFT
    ? (anoAtivo || eventoAtivo || turnoAtivo || areaAtiva || tipoAtivo)
    : (anoAtivo || diaAtivo || areaAtiva || competenciaAtiva || tipoAtivo || provedorAtivo)

  return (
    <div className="space-y-3">

      {/* Toggle Tipo — full width, acima das chips de fonte */}
      <TipoToggle full />

      {/* Chips de fonte */}
      <div className="rounded-xl bg-[#161411] border border-[#2C2820] p-3">
        <div className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#635D56] mb-2">Prova</div>
        <div className="flex flex-wrap gap-1.5">
          {(['ENEM', 'EXATO', 'UFT'] as const).map(f => {
            const prova = PROVA_MAP[f]
            const ativo = fonteAtiva === f
            return (
              <button
                key={f}
                onClick={() => switchFonte(f)}
                className={`px-2.5 py-1 text-[11px] rounded-md font-bold uppercase tracking-wider transition border ${
                  ativo
                    ? `${prova.bg} ${prova.text} ${prova.border}`
                    : 'bg-[#1E1B17] text-[#9E9589] border-transparent hover:bg-[#2C2820] hover:text-[#F2EDE4]'
                }`}
              >
                {f}
              </button>
            )
          })}
        </div>
      </div>

      <div className="rounded-xl bg-[#161411] border border-[#2C2820] divide-y divide-[#2C2820]">

        {/* ── Filtros EXATO ── */}
        {isExato && (
          <>
            <FilterGroup title="Evento">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!eventoAtivo} onClick={() => nav(url({ evento: undefined }))}>Todos</Chip>
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

            <FilterGroup title="Turno">
              <div className="flex gap-1.5">
                <Chip active={!turnoAtivo}            onClick={() => nav(url({ turno: undefined }))}>Todos</Chip>
                <Chip active={turnoAtivo === 'MANHA'} onClick={() => nav(url({ turno: turnoAtivo === 'MANHA' ? undefined : 'MANHA' }))}>Manhã</Chip>
                <Chip active={turnoAtivo === 'TARDE'} onClick={() => nav(url({ turno: turnoAtivo === 'TARDE' ? undefined : 'TARDE' }))}>Tarde</Chip>
              </div>
            </FilterGroup>

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

        {/* ── Filtros UFT ── */}
        {isUFT && (
          <>
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
            </FilterGroup>

            <FilterGroup title="Turno">
              <div className="flex gap-1.5">
                <Chip active={!turnoAtivo}            onClick={() => nav(url({ turno: undefined }))}>Todos</Chip>
                <Chip active={turnoAtivo === 'MANHA'} onClick={() => nav(url({ turno: turnoAtivo === 'MANHA' ? undefined : 'MANHA' }))}>Manhã</Chip>
                <Chip active={turnoAtivo === 'TARDE'} onClick={() => nav(url({ turno: turnoAtivo === 'TARDE' ? undefined : 'TARDE' }))}>Tarde</Chip>
              </div>
            </FilterGroup>

            <FilterGroup title="Edição">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!eventoAtivo} onClick={() => nav(url({ evento: undefined }))}>Todas</Chip>
                {EDICOES_UFT.map(e => (
                  <Chip
                    key={e}
                    active={eventoAtivo === e}
                    onClick={() => nav(url({ evento: eventoAtivo === e ? undefined : e }))}
                    colorClass={eventoAtivo === e ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' : ''}
                  >
                    {EVENTO_LABEL[e] ?? e}
                  </Chip>
                ))}
              </div>
            </FilterGroup>
          </>
        )}

        {/* ── Filtros ENEM ── */}
        {isEnem && (
          <>
            {/* Elaborador — só quando tipo=SIMULADO */}
            {isSimulado && (
              <FilterGroup title="Elaborador">
                <div className="flex flex-wrap gap-1.5">
                  <Chip active={!provedorAtivo} onClick={() => nav(url({ provedor: undefined }))}>Todos</Chip>
                  {PROVEDORES.map(p => (
                    <Chip
                      key={p}
                      active={provedorAtivo === p}
                      onClick={() => nav(url({ provedor: provedorAtivo === p ? undefined : p }))}
                      colorClass={provedorAtivo === p ? 'bg-blue-500/15 text-blue-300 border-blue-500/30' : ''}
                    >
                      {PROVEDOR_LABEL[p] ?? p}
                    </Chip>
                  ))}
                </div>
              </FilterGroup>
            )}

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
              {anosParaExibir.length > 8 && (
                <button
                  onClick={() => setAnosExpandido(v => !v)}
                  className="mt-2 text-[10px] text-[#635D56] hover:text-[#9E9589] transition"
                >
                  {anosExpandido ? '▲ menos' : `▼ +${anosParaExibir.length - 8} anos`}
                </button>
              )}
            </FilterGroup>

            {/* Dia */}
            <FilterGroup title="Dia">
              <div className="flex gap-1.5">
                <Chip active={!diaAtivo} onClick={() => nav(url({ dia: undefined }))}>Todos</Chip>
                {isSimulado ? (
                  <>
                    <Chip active={diaAtivo === 'simu_dia1'} onClick={() => nav(url({ dia: diaAtivo === 'simu_dia1' ? undefined : 'simu_dia1' }))}>1º Dia</Chip>
                    <Chip active={diaAtivo === 'simu_dia2'} onClick={() => nav(url({ dia: diaAtivo === 'simu_dia2' ? undefined : 'simu_dia2' }))}>2º Dia</Chip>
                  </>
                ) : (
                  <>
                    <Chip active={diaAtivo === 'dia1'} onClick={() => nav(url({ dia: diaAtivo === 'dia1' ? undefined : 'dia1' }))}>1º Dia</Chip>
                    <Chip active={diaAtivo === 'dia2'} onClick={() => nav(url({ dia: diaAtivo === 'dia2' ? undefined : 'dia2' }))}>2º Dia</Chip>
                  </>
                )}
              </div>
            </FilterGroup>

            {/* Competência — só para PROVA (ENEM real) */}
            {!isSimulado && (
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
            )}
          </>
        )}
      </div>

      {/* Atalho limpar */}
      {hasFilter && (
        <Link
          href={`${pathname}?fonte=${fonteAtiva}${tipoAtivo ? `&tipo=${tipoAtivo}` : ''}`}
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
