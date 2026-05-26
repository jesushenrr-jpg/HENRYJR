'use client'

import { useRouter, useSearchParams, usePathname } from 'next/navigation'

const OPCOES = [
  { label: 'Todos',     value: '' },
  { label: 'Provas',    value: 'PROVA' },
  { label: 'Simulados', value: 'SIMULADO' },
]

/**
 * full=true  → ocupa 100% do container (sidebar), botões com flex-1
 * full=false → inline-flex auto-sizing (home page, uso centralizado)
 */
export default function TipoToggle({ full = false }: { full?: boolean }) {
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
    <div className={`${full ? 'flex w-full' : 'inline-flex'} rounded-xl border border-[#2C2820] overflow-hidden bg-[#161411]`}>
      {OPCOES.map(({ label, value }) => {
        const ativo = tipoAtivo === value
        return (
          <button
            key={value || 'todos'}
            onClick={() => setTipo(value)}
            className={`${full ? 'flex-1' : ''} px-3 py-2.5 text-[11px] font-bold uppercase tracking-wider whitespace-nowrap transition ${
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
