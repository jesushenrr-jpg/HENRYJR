"""
classificar_competencias_fontes.py
Classifica questões com habilidades H01–H30 via Groq e atualiza Supabase.
Suporta qualquer fonte: ENEM simulados, UFT, PAES, EXATO.

Uso:
    python classificar_competencias_fontes.py --fonte ENEM_SIM
    python classificar_competencias_fontes.py --fonte UFT
    python classificar_competencias_fontes.py --fonte PAES
    python classificar_competencias_fontes.py --fonte ENEM_SIM --limite 200
    python classificar_competencias_fontes.py --fonte ENEM_SIM --dry-run
"""

import json
import os
import re
import sys
import time
import argparse
import socket
from pathlib import Path

import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── DNS patch ────────────────────────────────────────────────────────────────
_HOST = "bmhudlpihwxvaelokugh.supabase.co"
_orig = socket.getaddrinfo
def _patch(host, port, *a, **k):
    if host == _HOST:
        host = "172.64.149.246"
    return _orig(host, port, *a, **k)
socket.getaddrinfo = _patch

# ── Credenciais ───────────────────────────────────────────────────────────────
import config as _cfg
_c = _cfg.carregar()
SUPABASE_URL = _c.get("url", "").rstrip("/")
SERVICE_KEY  = _c.get("key", "")
GROQ_KEY     = os.environ.get("GROQ_API_KEY", "")

HDR_SB = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
}

GROQ_MODEL = "llama-3.1-8b-instant"
DELAY      = 2.5   # s entre chamadas (~24 RPM, abaixo do limite 30 RPM)

BASE = Path(r"C:\PROJETOS\HENRYJR\DADOS")

FONTES = {
    "ENEM_SIM": BASE / "json_enem_simulados",
    "UFT":      BASE / "json_uft",
    "PAES":     BASE / "json_paes",
}

# ── Mapeamento H01–H30 ────────────────────────────────────────────────────────
HABILIDADES = {
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
}

HABILIDADES_LISTA = "\n".join(f"{k}: {v}" for k, v in HABILIDADES.items())


def montar_prompt(q: dict) -> str:
    enunciado = " ".join(q.get("enunciado") or [])[:600]
    comando   = (q.get("comando") or "")[:200]
    area      = q.get("area") or ""
    return f"""Você é um especialista no ENEM. Classifique a questão abaixo com UMA habilidade (H01 a H30).

Área: {area}
Enunciado: {enunciado}
Comando: {comando}

Habilidades disponíveis:
{HABILIDADES_LISTA}

Responda APENAS com o código da habilidade, por exemplo: H15
Não escreva mais nada."""


def chamar_groq(prompt: str, tentativas: int = 3) -> str | None:
    if not GROQ_KEY:
        print("✗ GROQ_API_KEY não definida.")
        return None
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20,
        "temperature": 0,
    }).encode()
    for t in range(tentativas):
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {GROQ_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "python-httpx/0.27.0",
                },
                timeout=30,
            )
            if resp.status_code == 429:
                espera = 65 if t == 0 else 120
                print(f"    ↩ Rate limit 429 — aguardando {espera}s...")
                time.sleep(espera)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            if t < tentativas - 1:
                print(f"    ↩ Retry {t+1}/3 ({e.__class__.__name__}), aguardando 10s...")
                time.sleep(10)
            else:
                print(f"    ✗ Falha após {tentativas} tentativas: {e}")
    return None


def extrair_habilidade(texto: str) -> str | None:
    m = re.search(r'\bH([0-2]\d|30)\b', texto.upper())
    return m.group(0) if m else None


def patch_supabase(q: dict, competencia: str) -> bool:
    """Atualiza competência no Supabase via PATCH com filtro nos 6 campos únicos."""
    params = {
        "fonte":   f"eq.{q['fonte']}",
        "dia":     f"eq.{q['dia']}",
        "numero":  f"eq.{q['numero']}",
    }
    if q.get("ano") is not None:
        params["ano"] = f"eq.{q['ano']}"
    else:
        params["ano"] = "is.null"

    if q.get("evento"):
        params["evento"] = f"eq.{q['evento']}"
    else:
        params["evento"] = "is.null"

    if q.get("provedor"):
        params["provedor"] = f"eq.{q['provedor']}"
    else:
        params["provedor"] = "is.null"

    try:
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/questoes",
            params=params,
            json={"competencia": competencia},
            headers={**HDR_SB, "Prefer": "return=minimal"},
            timeout=10,
        )
        return r.status_code in (200, 204)
    except Exception as e:
        print(f"    ⚠ Supabase PATCH falhou: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonte", required=True, choices=["ENEM_SIM", "UFT", "PAES"],
                        help="Fonte a processar")
    parser.add_argument("--limite", type=int, default=0,
                        help="Máx de questões a classificar (0=todas)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria feito sem chamar Groq ou Supabase")
    parser.add_argument("--reprocessar", action="store_true",
                        help="Reprocessa questões que já têm competência")
    args = parser.parse_args()

    pasta = FONTES[args.fonte]
    if not pasta.exists():
        print(f"✗ Pasta não encontrada: {pasta}")
        sys.exit(1)

    arquivos = sorted(pasta.glob("*.json"))
    if not arquivos:
        print(f"✗ Nenhum JSON em {pasta}")
        sys.exit(1)

    print("=" * 60)
    print(f"CLASSIFICAR COMPETÊNCIAS — {args.fonte}")
    print("=" * 60)

    total_ok = total_erros = total_puladas = 0
    inicio = time.time()

    for arq in arquivos:
        questoes = json.loads(arq.read_text(encoding="utf-8"))
        pendentes = [
            q for q in questoes
            if args.reprocessar or not q.get("competencia")
        ]
        # Pular questões sem enunciado (nada para classificar)
        pendentes = [q for q in pendentes if q.get("enunciado") or q.get("comando")]

        if not pendentes:
            print(f"  ✓ {arq.name}: sem pendências")
            continue

        print(f"\n📄 {arq.name} — {len(pendentes)} questões a classificar")
        modificado = False

        for q in pendentes:
            if args.limite and total_ok >= args.limite:
                print(f"\n⏹ Limite de {args.limite} atingido.")
                break

            num = q.get("numero", "?")
            area = (q.get("area") or "")[:20]

            if args.dry_run:
                print(f"  [dry] Q{num:03} [{area}]")
                total_ok += 1
                continue

            prompt = montar_prompt(q)
            resposta = chamar_groq(prompt)

            if resposta is None:
                total_erros += 1
                print(f"  ✗ Q{num:03} [{area}] sem resposta")
                time.sleep(DELAY)
                continue

            hab = extrair_habilidade(resposta)
            if not hab:
                total_erros += 1
                print(f"  ✗ Q{num:03} [{area}] resposta inválida: '{resposta}'")
                time.sleep(DELAY)
                continue

            q["competencia"] = hab
            modificado = True
            total_ok += 1

            # Atualiza Supabase via PATCH com filtro nos 6 campos únicos
            ok_sb = patch_supabase(q, hab)
            sb_tag = "✓" if ok_sb else "⚠sb"
            print(f"  Q{num:03} [{area}] → {hab} {sb_tag}")

            time.sleep(DELAY)

        if modificado and not args.dry_run:
            arq.write_text(
                json.dumps(questoes, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  💾 {arq.name} salvo")

        if args.limite and total_ok >= args.limite:
            break

    duracao = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"✅  Classificadas: {total_ok}")
    print(f"✗   Erros:        {total_erros}")
    print(f"⏱   Tempo:        {duracao / 60:.1f} min")
    if total_ok and not args.dry_run:
        print(f"⚡  Média:        {duracao / total_ok:.1f}s/questão")
    if args.dry_run:
        print("(dry-run: nada foi realmente feito)")


if __name__ == "__main__":
    main()
