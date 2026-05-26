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
