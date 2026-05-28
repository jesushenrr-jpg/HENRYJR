"""
classificar_competencias_fontes.py
Classifica questões com habilidades H01–H30 via Groq e atualiza Supabase.
Suporta qualquer fonte: ENEM simulados, UFT, PAES.

Estratégia: batches de 20 questões por ÁREA — prompt ultra-curto (~50 tok/q).
Isso maximiza throughput dentro do limite de TPM do Groq free tier.

Uso:
    python classificar_competencias_fontes.py --fonte ENEM_SIM
    python classificar_competencias_fontes.py --fonte UFT
    python classificar_competencias_fontes.py --fonte PAES
    python classificar_competencias_fontes.py --fonte ENEM_SIM --batch 20
    python classificar_competencias_fontes.py --fonte ENEM_SIM --dry-run
    python classificar_competencias_fontes.py --fonte ENEM_SIM --reprocessar
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

GROQ_MODEL   = "llama-3.1-8b-instant"
DELAY_LOTE   = 2.0   # s após cada lote bem-sucedido

BASE = Path(r"C:\PROJETOS\HENRYJR\DADOS")

FONTES = {
    "ENEM_SIM": BASE / "json_enem_simulados",
    "UFT":      BASE / "json_uft",
    "PAES":     BASE / "json_paes",
}

# ── Mapeamento de área para faixa de habilidades ──────────────────────────────
AREA_FAIXA = {
    "linguagens": ("H01", "H10", "H01–H10"),
    "humanas":    ("H11", "H20", "H11–H20"),
    "natureza":   ("H21", "H30", "H21–H30"),
    "matematica": ("H21", "H30", "H21–H30"),
}

def faixa_da_area(area: str) -> tuple[str, str, str]:
    area_l = (area or "").lower()
    if "linguagen" in area_l or "codigo" in area_l or "artes" in area_l:
        return AREA_FAIXA["linguagens"]
    if "humana" in area_l:
        return AREA_FAIXA["humanas"]
    if "natureza" in area_l:
        return AREA_FAIXA["natureza"]
    if "matem" in area_l:
        return AREA_FAIXA["matematica"]
    return ("H01", "H30", "H01–H30")   # fallback: faixa completa


def montar_prompt_area_batch(questoes: list[dict], faixa_label: str) -> str:
    """Prompt ultra-curto: área já narrows down o espaço; só envia enunciado curto."""
    linhas = [
        f"Classifique as {len(questoes)} questões abaixo com habilidades ENEM na faixa {faixa_label}.",
        "Retorne APENAS um array JSON com os códigos, ex: [\"H05\",\"H12\",\"H08\"]",
        "",
    ]
    for i, q in enumerate(questoes, 1):
        trecho = " ".join(q.get("enunciado") or [])[:300]
        cmd    = (q.get("comando") or "")[:100]
        linhas.append(f"Q{i}: {trecho} {cmd}".strip())
    return "\n".join(linhas)


def chamar_groq(prompt: str, n_esperado: int, tentativas: int = 3) -> list[str] | None:
    if not GROQ_KEY:
        print("✗ GROQ_API_KEY não definida.")
        return None

    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": n_esperado * 8,
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
            texto = resp.json()["choices"][0]["message"]["content"].strip()
            return _parse_habs(texto, n_esperado)
        except requests.exceptions.RequestException as e:
            if t < tentativas - 1:
                espera = 10 * (t + 1)
                print(f"    ↩ Retry {t+1}/3 em {espera}s ({e.__class__.__name__})")
                time.sleep(espera)
            else:
                print(f"    ✗ Falha após {tentativas} tentativas: {e}")
    return None


def _parse_habs(texto: str, n_esperado: int) -> list[str] | None:
    try:
        dados = json.loads(texto)
        if isinstance(dados, list):
            habs = [str(h).upper().strip() for h in dados]
            if all(re.match(r'^H([0-2]\d|30)$', h) for h in habs) and len(habs) == n_esperado:
                return habs
    except Exception:
        pass
    habs = re.findall(r'H([0-2]\d|30)\b', texto.upper())
    habs = [f"H{n}" for n in habs]
    if len(habs) == n_esperado:
        return habs
    # Tenta pegar qualquer quantidade e completar com fallback se próximo
    if len(habs) >= n_esperado:
        return habs[:n_esperado]
    return None


def patch_supabase(q: dict, competencia: str) -> bool:
    params = {
        "fonte":   f"eq.{q['fonte']}",
        "dia":     f"eq.{q['dia']}",
        "numero":  f"eq.{q['numero']}",
    }
    params["ano"]     = f"eq.{q['ano']}"     if q.get("ano")     is not None else "is.null"
    params["evento"]  = f"eq.{q['evento']}"  if q.get("evento")  else "is.null"
    params["provedor"] = f"eq.{q['provedor']}" if q.get("provedor") else "is.null"
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
        print(f"    ⚠ PATCH falhou: {e}")
        return False


def patch_lote_supabase(questoes: list[dict], habs: list[str]) -> int:
    """Atualiza um lote de questões no Supabase. Retorna contagem de sucesso."""
    ok = 0
    for q, hab in zip(questoes, habs):
        if patch_supabase(q, hab):
            ok += 1
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonte",       required=True, choices=["ENEM_SIM", "UFT", "PAES"])
    parser.add_argument("--limite",      type=int, default=0, help="Max questoes (0=todas)")
    parser.add_argument("--batch",       type=int, default=20, help="Questoes por chamada Groq")
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--reprocessar", action="store_true")
    args = parser.parse_args()

    pasta = FONTES[args.fonte]
    if not pasta.exists():
        print(f"✗ Pasta nao encontrada: {pasta}")
        sys.exit(1)

    arquivos = sorted(pasta.glob("*.json"))
    print("=" * 60)
    print(f"CLASSIFICAR COMPETENCIAS — {args.fonte} (batch={args.batch})")
    print("=" * 60)

    total_ok = total_erros = 0
    inicio = time.time()

    for arq in arquivos:
        questoes = json.loads(arq.read_text(encoding="utf-8"))
        pendentes = [
            q for q in questoes
            if (args.reprocessar or not q.get("competencia"))
            and (q.get("enunciado") or q.get("comando"))
        ]

        if not pendentes:
            print(f"  ok {arq.name}")
            continue

        print(f"\n  {arq.name} — {len(pendentes)} pendentes")
        modificado = False

        # Agrupar por área para batch mais eficiente
        from collections import defaultdict
        por_area: dict[str, list[dict]] = defaultdict(list)
        for q in pendentes:
            por_area[q.get("area") or ""].append(q)

        for area, qs_area in por_area.items():
            h_min, h_max, faixa_label = faixa_da_area(area)

            i = 0
            while i < len(qs_area):
                if args.limite and total_ok >= args.limite:
                    break

                lote = qs_area[i:i + args.batch]

                if args.dry_run:
                    print(f"    [dry] {len(lote)}q de '{area[:30]}' -> faixa {faixa_label}")
                    total_ok += len(lote)
                    i += len(lote)
                    continue

                prompt = montar_prompt_area_batch(lote, faixa_label)
                habs = chamar_groq(prompt, len(lote))

                if habs is None:
                    # Reduz para metade e tenta de novo
                    if len(lote) > 1:
                        print(f"    ⚠ Batch de {len(lote)} falhou — reduzindo para {len(lote)//2}")
                        args.batch = max(1, args.batch // 2)
                        continue  # não avança i, tenta com batch menor
                    else:
                        total_erros += 1
                        print(f"    ✗ Q{lote[0].get('numero','?')} sem resposta")
                        i += 1
                        time.sleep(DELAY_LOTE)
                        continue

                # Aplicar resultado
                sb_ok = patch_lote_supabase(lote, habs)
                for q, hab in zip(lote, habs):
                    q["competencia"] = hab
                    modificado = True
                    total_ok += 1

                nums = [str(q.get('numero','?')) for q in lote]
                print(f"    {len(lote)}q [{faixa_label}] -> {habs[:3]}{'...' if len(habs)>3 else ''} (sb:{sb_ok}/{len(lote)})")

                i += len(lote)
                time.sleep(DELAY_LOTE)

            if args.limite and total_ok >= args.limite:
                break

        if modificado and not args.dry_run:
            arq.write_text(json.dumps(questoes, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"    salvo -> {arq.name}")

        if args.limite and total_ok >= args.limite:
            break

    duracao = time.time() - inicio
    print(f"\n{'='*60}")
    print(f"Classificadas: {total_ok}  |  Erros: {total_erros}  |  Tempo: {duracao/60:.1f} min")
    if total_ok and not args.dry_run:
        print(f"Media: {duracao/total_ok:.2f}s/questao")


if __name__ == "__main__":
    main()
