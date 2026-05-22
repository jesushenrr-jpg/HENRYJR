"""
classificar_competencias.py
Classifica cada questão com uma habilidade H01–H30 do ENEM via Groq (LLaMA 3).
Salva no JSON local e faz upsert no Supabase.

Uso:
    python classificar_competencias.py              # todas sem competência
    python classificar_competencias.py --ano 2023   # só um ano
    python classificar_competencias.py --limite 100 # máx 100 questões
    python classificar_competencias.py --reprocessar # reprocessa mesmo as que já têm
"""

import json, glob, time, sys, argparse, os, traceback
from pathlib import Path

# Fix encoding no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Configuração ────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # definir via variável de ambiente
GROQ_MODEL   = "llama-3.1-8b-instant"   # 14.400 req/dia (free) — suficiente para 2890 questões
PASTA_JSON   = Path("dados/json_v2")
DELAY_ENTRE_CHAMADAS = 2.5  # segundos (~24 req/min, abaixo do limite de 30 RPM)

# ── Mapeamento oficial ENEM H01–H30 ─────────────────────────────────────────
HABILIDADES = {
    # Linguagens, Códigos e suas Tecnologias
    "H01": "Identificar as diferentes linguagens e seus recursos expressivos como elementos de caracterização dos campos de atividade humana.",
    "H02": "Reconhecer e usar língua(s) e linguagem(ns) em diferentes situações e contextos de produção.",
    "H03": "Relacionar informações geradas nos sistemas de comunicação e informação, considerando a função social dos processos comunicativos.",
    "H04": "Reconhecer a língua portuguesa como representação histórica e social da realidade.",
    "H05": "Analisar e interpretar criticamente a linguagem das mídias levando em conta seus sistemas de comunicação e as condições de produção e recepção das mensagens.",
    "H06": "Aplicar tecnologias da comunicação e da informação em situações relevantes.",
    "H07": "Confrontar opiniões e pontos de vista sobre as diferentes linguagens e suas manifestações específicas.",
    "H08": "Compreender e usar a língua portuguesa como língua materna, geradora de significação e integradora da organização do mundo e da própria identidade.",
    "H09": "Entender os princípios das tecnologias associadas à linguagem.",
    "H10": "Entender a natureza da linguagem como fenômeno humano.",
    # Ciências Humanas e suas Tecnologias
    "H11": "Reconstituir a trajetória histórica e espacial da humanidade em suas múltiplas dimensões.",
    "H12": "Contextualizar e comparar diferentes épocas e civilizações.",
    "H13": "Reconhecer e relativizar as concepções de espaço, tempo e cultura.",
    "H14": "Analisar situações problematizadoras envolvendo aspectos sociais, econômicos, políticos e culturais.",
    "H15": "Dominar os princípios de pesquisa em Ciências Humanas.",
    "H16": "Utilizar os conhecimentos históricos, geográficos e sociais para compreender o mundo.",
    "H17": "Compreender a organização do espaço geográfico e as transformações do território.",
    "H18": "Identificar e analisar as relações de poder nos processos históricos e sociais.",
    "H19": "Analisar as relações entre ética, cidadania e democracia.",
    "H20": "Compreender fenômenos socioculturais e a diversidade das formas de vida.",
    # Ciências da Natureza e suas Tecnologias
    "H21": "Reconhecer mecanismos e fenômenos de natureza físico-química e biológica.",
    "H22": "Associar intervenções humanas ao impacto sobre o ambiente.",
    "H23": "Aplicar conhecimentos físicos, químicos e biológicos para análise de situações práticas.",
    "H24": "Relacionar informações para interpretar experimentos e dados científicos.",
    "H25": "Avaliar propostas de intervenção no ambiente com base em conhecimentos científicos.",
    "H26": "Compreender a interação entre ciência, tecnologia e sociedade.",
    "H27": "Entender as bases biológicas da hereditariedade e evolução.",
    "H28": "Aplicar princípios de química e física a substâncias e reações do cotidiano.",
    "H29": "Reconhecer os princípios de saúde, saneamento e qualidade de vida.",
    "H30": "Compreender fenômenos energéticos, elétricos, magnéticos e ondas.",
    # Matemática e suas Tecnologias
    # (reutilizamos H01–H10 com outro contexto; na prática o ENEM usa as mesmas siglas)
    # Deixamos o modelo escolher H01–H30 livremente; a área já está no JSON.
}

HABILIDADES_LISTA = "\n".join(f"{k}: {v}" for k, v in HABILIDADES.items())

# ── Supabase client ──────────────────────────────────────────────────────────
try:
    import supabase_client as _sb
    SUPABASE_OK = True
except Exception as e:
    print(f"⚠ Supabase não disponível ({e}). Salvando só nos JSONs.")
    SUPABASE_OK = False

# ── Groq HTTP ────────────────────────────────────────────────────────────────
import urllib.request

def chamar_groq(prompt: str, tentativas: int = 3) -> str | None:
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20,
        "temperature": 0,
    }).encode()

    for t in range(tentativas):
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "python-httpx/0.27.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Rate limit: espera longa para resetar a janela da Groq
                espera = 65 if t == 0 else 120
                print(f"    ↩ Rate limit 429 — aguardando {espera}s...")
                time.sleep(espera)
            elif t < tentativas - 1:
                espera = 10 * (t + 1)
                print(f"    ↩ Retry {t+1} em {espera}s (HTTP {e.code})")
                time.sleep(espera)
            else:
                print(f"    ✗ Falha após {tentativas} tentativas: HTTP {e.code}")
                return None
        except Exception as e:
            if t < tentativas - 1:
                espera = 10 * (t + 1)
                print(f"    ↩ Retry {t+1} em {espera}s ({e})")
                time.sleep(espera)
            else:
                print(f"    ✗ Falha após {tentativas} tentativas: {e}")
                return None

def extrair_habilidade(texto: str) -> str | None:
    """Extrai 'H01'–'H30' da resposta do modelo."""
    import re
    m = re.search(r'\bH([0-2]\d|30)\b', texto.upper())
    return m.group(0) if m else None

def montar_prompt(q: dict) -> str:
    enunciado = " ".join(q.get("enunciado", []))[:600]
    comando   = q.get("comando", "")[:200]
    area      = q.get("area", "")

    return f"""Você é um especialista no ENEM. Classifique a questão abaixo com UMA habilidade (H01 a H30).

Área: {area}
Enunciado: {enunciado}
Comando: {comando}

Habilidades disponíveis:
{HABILIDADES_LISTA}

Responda APENAS com o código da habilidade, por exemplo: H15
Não escreva mais nada."""

# ── Carga e salvamento dos JSONs ─────────────────────────────────────────────
def carregar_json(arquivo: Path) -> list:
    return json.loads(arquivo.read_text(encoding="utf-8"))

def salvar_json(arquivo: Path, questoes: list):
    arquivo.write_text(json.dumps(questoes, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Principal ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano",         type=int,  help="Processar só este ano")
    parser.add_argument("--limite",      type=int,  default=0, help="Máx de questões (0=todas)")
    parser.add_argument("--reprocessar", action="store_true", help="Reprocessa questões que já têm competência")
    args = parser.parse_args()

    arquivos = sorted(PASTA_JSON.glob("enem_*.json"))
    if args.ano:
        arquivos = [f for f in arquivos if f"enem_{args.ano}" in f.name]

    if not arquivos:
        print("Nenhum arquivo encontrado.")
        return

    total_classificadas = 0
    total_erros         = 0
    inicio              = time.time()

    for arquivo in arquivos:
        questoes = carregar_json(arquivo)
        modificado = False
        ano = arquivo.stem.replace("enem_", "")

        pendentes = [
            q for q in questoes
            if args.reprocessar or not q.get("competencia")
        ]

        if not pendentes:
            print(f"✓ {arquivo.name}: todas já classificadas")
            continue

        print(f"\n📄 {arquivo.name} — {len(pendentes)} questões a classificar")

        for q in pendentes:
            if args.limite and total_classificadas >= args.limite:
                print(f"\n⏹ Limite de {args.limite} questões atingido.")
                break

            num = q.get("numero", "?")
            area_short = q.get("area", "")[:20]

            prompt = montar_prompt(q)
            resposta = chamar_groq(prompt)

            if resposta is None:
                total_erros += 1
                print(f"  Q{num:03} [{area_short}] ✗ sem resposta")
                time.sleep(DELAY_ENTRE_CHAMADAS)
                continue

            hab = extrair_habilidade(resposta)
            if not hab:
                total_erros += 1
                print(f"  Q{num:03} [{area_short}] ✗ resposta inválida: '{resposta}'")
                time.sleep(DELAY_ENTRE_CHAMADAS)
                continue

            q["competencia"] = hab
            modificado = True
            total_classificadas += 1
            print(f"  Q{num:03} [{area_short}] → {hab}")

            # Upsert Supabase
            if SUPABASE_OK:
                try:
                    _sb.upsert_questao(q)
                except Exception as e:
                    print(f"    ⚠ Supabase: {e}")

            time.sleep(DELAY_ENTRE_CHAMADAS)

        if modificado:
            salvar_json(arquivo, questoes)
            print(f"  💾 {arquivo.name} salvo")

        if args.limite and total_classificadas >= args.limite:
            break

    duracao = time.time() - inicio
    print(f"\n{'='*50}")
    print(f"✅ Classificadas: {total_classificadas}")
    print(f"✗  Erros:         {total_erros}")
    print(f"⏱  Tempo:         {duracao/60:.1f} min")
    if total_classificadas:
        print(f"⚡ Média:         {duracao/total_classificadas:.1f}s/questão")

if __name__ == "__main__":
    main()
