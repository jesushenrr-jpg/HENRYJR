"""
Gera demo_questoes.html com imagens embutidas em base64.
"""
import base64, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'C:/PROJETOS/HENRYJR/dados/imagens/2010'
OUT  = r'C:/PROJETOS/HENRYJR/demo_questoes.html'

def b64(dia, nome):
    with open(f'{BASE}/{dia}/{nome}.jpg', 'rb') as f:
        return 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode()

print('Carregando imagens...')
I = {}
for dia, nome in [
    ('dia1','q080_alt_A'),('dia1','q080_alt_B'),('dia1','q080_alt_C'),
    ('dia1','q080_alt_D'),('dia1','q080_alt_E'),
    ('dia1','q084_alt_A'),('dia1','q084_alt_B'),('dia1','q084_alt_C'),
    ('dia1','q084_alt_D'),('dia1','q084_alt_E'),
    ('dia2','q102_alt_A'),('dia2','q102_alt_B'),('dia2','q102_alt_C'),
    ('dia2','q102_alt_D'),('dia2','q102_alt_E'),
    ('dia2','q136_alt_A'),('dia2','q136_alt_B'),('dia2','q136_alt_C'),
    ('dia2','q136_alt_D'),('dia2','q136_alt_E'),
    ('dia2','q137_fig'),
    ('dia2','q137_alt_A'),('dia2','q137_alt_B'),('dia2','q137_alt_C'),
    ('dia2','q137_alt_D'),('dia2','q137_alt_E'),
    ('dia2','q142_alt_A'),('dia2','q142_alt_B'),('dia2','q142_alt_C'),
    ('dia2','q142_alt_D'),('dia2','q142_alt_E'),
]:
    I[nome] = b64(dia, nome)
    print(f'  {nome}')

q = "'"

def btn_img(num, letra, gab, key):
    return (
        f'<button onclick="responder({num},{q}{letra}{q},{q}{gab}{q})" '
        f'class="img-alt-btn alt-btn w-full flex items-center gap-2 px-3 py-2 rounded-xl">'
        f'<span class="font-bold text-gray-500 shrink-0 w-8 text-lg text-center">{letra}</span>'
        f'<div style="flex:1;min-width:0;">'
        f'<img src="{I[key]}" style="width:100%;height:auto;display:block;" />'
        f'</div>'
        f'</button>\n'
    )

def btn_txt(num, letra, gab, txt):
    return (
        f'<button onclick="responder({num},{q}{letra}{q},{q}{gab}{q})" '
        f'class="alt-btn w-full text-left flex gap-3 px-4 py-3 rounded-xl border border-gray-200 '
        f'hover:border-blue-300 hover:bg-blue-50 text-sm">'
        f'<span class="font-bold text-gray-400 shrink-0 w-5">{letra}</span>'
        f'<span>{txt}</span>'
        f'</button>\n'
    )

def fb(num, gab, txt):
    return (
        f'<div id="feedback-{num}" class="hidden px-6 pb-5">'
        f'<div class="rounded-xl bg-gray-50 border border-gray-200 px-4 py-3 text-sm text-gray-600">'
        f'<p class="font-semibold text-gray-800 mb-1">Gabarito: {gab}</p>'
        f'<p>{txt}</p></div></div>\n'
    )

def card_header(num, area, cor, dia_label):
    return (
        f'<div id="card-{num}" class="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">\n'
        f'<div class="px-6 pt-5 pb-1 flex items-start justify-between">'
        f'<div class="flex gap-2 flex-wrap">'
        f'<span class="badge bg-indigo-100 text-indigo-700">Questao {num}</span>'
        f'<span class="badge bg-gray-100 text-gray-600">ENEM 2010</span>'
        f'<span class="badge bg-{cor}-100 text-{cor}-700">{area}</span>'
        f'</div>'
        f'<span class="text-xs text-gray-400">{dia_label}</span>'
        f'</div>\n'
    )

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
body { font-family: 'Inter', sans-serif; }
.alt-btn { transition: all .15s ease; }
.alt-btn:hover:not(.disabled) { transform: translateX(3px); }
.alt-btn.selected-correct, .alt-btn.reveal-correct { background:#d1fae5 !important; border-color:#10b981 !important; }
.alt-btn.selected-wrong { background:#fee2e2 !important; border-color:#ef4444 !important; }
.alt-btn.disabled { cursor: default; }
.img-alt-btn { border-bottom: 1px solid #f3f4f6; }
.img-alt-btn:last-child { border-bottom: none; }
.img-alt-btn:hover:not(.disabled) { background:#eff6ff; }
.badge { display:inline-block; font-size:.65rem; font-weight:600; letter-spacing:.05em;
         text-transform:uppercase; padding:2px 8px; border-radius:9999px; }
</style>
"""

JS = """
<script>
const answered = {};
function responder(num, escolha, gabarito) {
  if (answered[num]) return;
  answered[num] = true;
  const acertou = escolha === gabarito;
  const alts = document.getElementById('alts-' + num);
  if (alts) {
    alts.querySelectorAll('.alt-btn').forEach(btn => {
      btn.classList.add('disabled');
      btn.onclick = null;
      const letra = btn.querySelector('span').textContent.trim();
      if (letra === escolha) btn.classList.add(acertou ? 'selected-correct' : 'selected-wrong');
      else if (letra === gabarito && !acertou) btn.classList.add('reveal-correct');
    });
  }
  const fb = document.getElementById('feedback-' + num);
  if (fb) { fb.classList.remove('hidden'); fb.scrollIntoView({behavior:'smooth',block:'nearest'}); }
}
</script>
"""

parts = []
parts.append(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>HenryJr - Demo ENEM 2010</title>
<script src="https://cdn.tailwindcss.com"></script>
{STYLE}
</head>
<body class="bg-gray-50 min-h-screen">
<header class="bg-white border-b border-gray-200 sticky top-0 z-10">
  <div class="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="text-xl font-bold text-blue-600">henry<span class="text-gray-800">jr</span></span>
      <span class="badge bg-blue-100 text-blue-700">beta</span>
    </div>
    <span class="text-sm font-medium text-gray-700">ENEM 2010 — Demonstracao</span>
  </div>
</header>
<main class="max-w-3xl mx-auto px-4 py-8 space-y-8">

<div class="bg-white rounded-xl border border-gray-200 p-4 text-sm text-gray-600">
  <p class="font-semibold text-gray-800 mb-2">Questoes nesta demo:</p>
  <ul class="list-disc list-inside space-y-1">
    <li><strong>Q50</strong> — alternativas textuais (padrao normal)</li>
    <li><strong>Q80</strong> — diagramas de fisica (refracao da luz)</li>
    <li><strong>Q84</strong> — formulas estruturais de quimica</li>
    <li><strong>Q102</strong> — obras de arte</li>
    <li><strong>Q136</strong> — diagramas de lousa (matematica)</li>
    <li><strong>Q137</strong> — enunciado com figura + planificacoes geometricas</li>
    <li><strong>Q142</strong> — graficos de funcao</li>
  </ul>
  <p class="mt-2 text-xs text-gray-400">Clique em uma alternativa para ver o gabarito.</p>
</div>
""")

# Q50
parts.append(card_header(50, 'Ciencias Humanas', 'amber', 'Dia 1'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>A vacina, o soro e os antibioticos submetem os organismos a processos biologicos diferentes. Pessoas que viajam para regioes com alta incidencia de febre amarela, picadas de cobras peconhentas e leptospirose devem seguir orientacoes medicas.</p>
<p>Um viajante deveria ser orientado a tomar preventivamente ou como tratamento:</p>
</div>
<div id="alts-50" class="px-6 pb-5 space-y-2">\n""")
parts.append(btn_txt(50,'A','B','antibiotico contra o virus da febre amarela, soro antiofidico caso seja picado por cobra e vacina contra leptospirose.'))
parts.append(btn_txt(50,'B','B','vacina contra o virus da febre amarela, soro antiofidico caso seja picado por cobra e antibiotico caso entre em contato com Leptospira sp.'))
parts.append(btn_txt(50,'C','B','soro contra o virus da febre amarela, antibiotico caso seja picado por cobra e soro contra toxinas bacterianas.'))
parts.append(btn_txt(50,'D','B','antibiotico ou soro contra febre amarela e veneno de cobras, e vacina contra leptospirose.'))
parts.append(btn_txt(50,'E','B','soro antiofidico e antibiotico contra Leptospira sp e vacina contra febre amarela.'))
parts.append('</div>\n')
parts.append(fb(50,'B','Febre amarela = vacina. Picada de cobra = soro antiofidico. Leptospirose (bacteria) = antibiotico.'))
parts.append('</div>\n')

# Q80
parts.append(card_header(80, 'Ciencias da Natureza', 'orange', 'Dia 1'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>Um grupo de cientistas construiu o primeiro metamaterial com valor negativo do indice de refracao para a luz visivel. Esse material tem sido chamado de "canhoto".</p>
<p>Qual figura representa a refracao da luz ao passar do ar para esse metamaterial?</p>
</div>
<div id="alts-80" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(80, l, 'D', f'q080_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(80,'D','Em metamateriais com indice de refracao negativo, a luz refratada se curva para o mesmo lado da normal que a luz incidente (refracao "canhota").'))
parts.append('</div>\n')

# Q84
parts.append(card_header(84, 'Ciencias da Natureza', 'orange', 'Dia 1'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>Os organofosforados sao divididos em: <strong>Tipo A</strong> (sem enxofre); <strong>Tipo B</strong> (oxigenio P=O substituido por enxofre); <strong>Tipo C</strong> (dois oxigenios substituidos por enxofre).</p>
<p>Um pesticida organofosforado <strong>Tipo B</strong> com grupo etoxi em sua formula estrutural esta representado em:</p>
</div>
<div id="alts-84" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(84, l, 'E', f'q084_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(84,'E','O Tipo B tem P=S (enxofre na dupla ligacao) e grupos etoxi (-OCH2CH3) intactos. A alternativa E apresenta essa estrutura.'))
parts.append('</div>\n')

# Q102
parts.append(card_header(102, 'Ciencias da Natureza', 'teal', 'Dia 2'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>Atualmente, artistas apropriam-se de personagens de diferentes epocas para criar obras que misturam estilos e referencias culturais. Qual das imagens abaixo exemplifica melhor esse estilo contemporaneo?</p>
</div>
<div id="alts-102" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(102, l, 'C', f'q102_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(102,'C','Funny Filez, "Monabean": mistura a Mona Lisa com personagens pop modernos, exemplificando a apropriacao e fusao de referencias de diferentes epocas.'))
parts.append('</div>\n')

# Q136
parts.append(card_header(136, 'Matematica', 'violet', 'Dia 2'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>Um professor dividiu a lousa em 4 partes iguais e preencheu 75% dela. Depois apagou tudo e voltou a preenche-la usando 40% do espaco. Qual diagrama representa corretamente essa segunda situacao?</p>
</div>
<div id="alts-136" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(136, l, 'A', f'q136_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(136,'A','40% de 4 partes = 1,6 parte. A alternativa A e a unica que representa corretamente essa proporcao.'))
parts.append('</div>\n')

# Q137
parts.append(card_header(137, 'Matematica', 'violet', 'Dia 2'))
parts.append(f"""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>O bebedouro 3 e um semicilindro com 30 cm de altura, 100 cm de comprimento e 60 cm de largura. Os tres recipientes estao ilustrados na figura abaixo.</p>
<p>Considerando que nenhum tenha tampa, qual figura representa uma planificacao para o bebedouro 3?</p>
</div>
<div class="px-6 pb-3">
<img src="{I['q137_fig']}" style="width:100%;height:auto;border-radius:0.75rem;border:1px solid #e5e7eb;display:block" />
</div>
<div id="alts-137" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(137, l, 'E', f'q137_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(137,'E','A planificacao do semicilindro: retangulo 100x30 cm + duas meias-circunferencias de 60 cm de diametro nas extremidades.'))
parts.append('</div>\n')

# Q142
parts.append(card_header(142, 'Matematica', 'violet', 'Dia 2'))
parts.append("""<div class="px-6 pt-4 pb-3 text-gray-700 text-[15px] leading-relaxed space-y-2">
<p>Um casal acompanhou o crescimento do filho e percebeu: de 0 a 10 anos a altura variava rapidamente; dos 10 aos 17 anos a variacao era mais lenta; apos 17 anos tornava-se imperceptivel.</p>
<p>Qual grafico representa melhor a altura desse filho em funcao da idade?</p>
</div>
<div id="alts-142" class="px-6 pb-5 space-y-2">\n""")
for l in 'ABCDE':
    parts.append(btn_img(142, l, 'A', f'q142_alt_{l}'))
parts.append('</div>\n')
parts.append(fb(142,'A','O grafico A mostra crescimento rapido de 0-10 anos com desaceleracao progressiva ate estabilizar apos 17 anos — compativel com o enunciado.'))
parts.append('</div>\n')

parts.append('<div class="text-center text-xs text-gray-400 pb-8">HenryJr — Banco de Questoes ENEM 2009-2024</div>\n')
parts.append('</main>\n')
parts.append(JS)
parts.append('</body>\n</html>')

html = ''.join(parts)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Gerado: {len(html)//1024} KB -> {OUT}')
