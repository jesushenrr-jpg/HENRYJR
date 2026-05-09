import Link from 'next/link'

const STATS = [
  { label: 'Questões', valor: '2.890' },
  { label: 'Anos', valor: '2009–2024' },
  { label: 'Áreas', valor: '4' },
  { label: 'Com imagem', valor: '569+' },
]

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#1e1e2e] flex flex-col items-center justify-center px-4 py-16">
      <div className="max-w-2xl w-full text-center space-y-8">
        {/* Hero */}
        <div>
          <h1 className="text-5xl font-bold text-white mb-3">
            Henry<span className="text-[#7c6af7]">Jr</span>
          </h1>
          <p className="text-[#a6adc8] text-lg">
            Banco completo de questões do ENEM · 2009–2024
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {STATS.map(s => (
            <div key={s.label} className="bg-[#2a2a3e] rounded-2xl p-4">
              <p className="text-2xl font-bold text-[#7c6af7]">{s.valor}</p>
              <p className="text-[#585b70] text-sm">{s.label}</p>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/questoes"
            className="bg-[#7c6af7] hover:bg-[#9580ff] text-white font-bold px-8 py-4 rounded-2xl text-lg transition"
          >
            Explorar questões →
          </Link>
          <Link
            href="/auth/login"
            className="bg-[#2a2a3e] hover:bg-[#313244] border border-[#45475a] text-[#a6adc8] font-bold px-8 py-4 rounded-2xl text-lg transition"
          >
            Criar conta grátis
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          {[
            { icon: '🎯', titulo: 'Simulados', desc: 'Crie simulados por área, ano ou competência' },
            { icon: '✨', titulo: 'Explicação IA', desc: 'Gabarito comentado com LLaMA 3 via Groq' },
            { icon: '📓', titulo: 'Tira Teima', desc: 'Caderno de erros automático até zerar' },
          ].map(f => (
            <div key={f.titulo} className="bg-[#2a2a3e] rounded-2xl p-5 border border-[#45475a]">
              <p className="text-2xl mb-2">{f.icon}</p>
              <p className="text-white font-bold mb-1">{f.titulo}</p>
              <p className="text-[#585b70] text-sm">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
