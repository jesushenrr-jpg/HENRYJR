"""
classificar_competencias_fontes.py
Classifica questões com habilidades H01–H30 via Groq e atualiza Supabase.
Suporta qualquer fonte: ENEM simulados, UFT, PAES, EXATO.

Usa batch de N questões por chamada para minimizar tokens e contornar rate limits.

Uso:
    python classificar_competencias_fontes.py --fonte ENEM_SIM
    python classificar_competencias_fontes.py --fonte UFT
    python classificar_competencias_fontes.py --fonte PAES
    python classificar_competencias_fontes.py --fonte ENEM_SIM --limite 200
    python classificar_competencias_fontes.py --fonte ENEM_SIM --dry-run
    python classificar_competencias_fontes.py --fonte ENEM_SIM --batch 10
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
DELAY_APOS_LOTE = 3.0   # s após cada lote (evita burst)

BASE = Path(r"C:\PROJETOS\HENRYJR\DADOS")

FONTES = {
    "ENEM_SIM": BASE / "json_enem_simulados",
    "UFT":      BASE / "json_uft",
    "PAES":     BASE / "json_paes",
}

# ── Prompt curto — sem lista completa de habilidades para economizar tokens ───
# H01-H10 = Linguagens | H11-H20 = Ciências Humanas | H21-H30 = Natureza/Matemática
PROMPT_SISTEMA = """Você classifica questões do ENEM com habilidades H01–H30.
Regra rápida de área:
- H01–H10: Linguagens, Códigos e Artes
- H11–H20: Ciências Humanas (História, Geografia, Filosofia, Sociologia)
- H21–H30: Ciências da Natureza (Física, Química, Biologia) e Matemática

Retorne APENAS um array JSON com as habilidades na mesma ordem das questões.
Exemplo para 3 questões: ["H05","H14","H23"]"""


def montar_prompt_batch(questoes_batch: list[dict]) -> str:
    partes = [PROMPT_SISTEMA, ""]
    for i, q in enumerate(questoes_batch, 1):
        enunciado = " ".join(q.get("enunciado") or [])[:400]
        comando   = (q.get("comando") or "")[:150]
        area      = (q.get("area") or "")
        partes.append(f"Questão {i}:\nÁrea: {area}\nEnunciado: {enunciado}\nComando: {comando}")
    partes.append(f'\nRetorne APENAS o array JSON com {len(questoes_batch)} habilidades.')
    return "\n\n".join(partes)


def chamar_groq_batch(questoes_batch: list[dict], tentativas: int = 3) -> list[str] | None:
    """Chama Groq com N questões de uma vez. Retorna lista de H-codes ou None."""
    if not GROQ_KEY:
        print("✗ GROQ_API_KEY não definida.")
        return None

    prompt = montar_prompt_batch(questoes_batch)
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": len(questoes_batch) * 8,  # ~8 tokens por habilidade
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
            return _parse_habilidades(texto, len(questoes_batch))
        except requests.exceptions.RequestException as e:
            if t < tentativas - 1:
                print(f"    ↩ Retry {t+1}/3 ({e.__class__.__name__}), aguardando 10s...")
                time.sleep(10)
            else:
                print(f"    ✗ Falha após {tentativas} tentativas: {e}")
    return None


def _parse_habilidades(texto: str, esperado: int) -> list[str] | None:
    """Extrai lista de H-codes do JSON retornado pelo modelo."""
    # Tenta parsear como JSON direto
    try:
        dados = json.loads(texto)
        if isinstance(dados, list):
            habs = [str(h).upper().strip() for h in dados]
            if all(re.match(r'^H([0-2]\d|30)$', h) for h in habs) and len(habs) == esperado:
                return habs
    except Exception:
        pass
    # Fallback: extrai todos os H-codes do texto
    habs = re.findall(r'\bH([0-2]\d|30)\b', texto.upper())
    habs = [f"H{n}" for n in habs]
    if len(habs) == esperado:
        return habs
    return None


def patch_supabase(q: dict, competencia: str) -> bool:
    """Atualiza competência no Supabase via PATCH com filtro nos 6 campos únicos."""
    params = {
        "fonte":  f"eq.{q['fonte']}",
        "dia":    f"eq.{q['dia']}",
        "numero": f"eq.{q['numero']}",
    }
    params["ano"] = f"eq.{q['ano']}" if q.get("ano") is not None else "is.null"
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
        print(f"    ⚠ Supabase PATCH falhou: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonte", required=True, choices=["ENEM_SIM", "UFT", "PAES"])
    parser.add_argument("--limite",      type=int, default=0,  help="Máx questões (0=todas)")
    parser.add_argument("--batch",       type=int, default=5,  help="Questões por chamada Groq")
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--reprocessar", action="store_true")
    args = parser.parse_args()

    pasta = FONTES[args.fonte]
    if not pasta.exists():
        print(f"✗ Pasta não encontrada: {pasta}")
        sys.exit(1)

    arquivos = sorted(pasta.glob("*.json"))
    print("=" * 60)
    print(f"CLASSIFICAR COMPETÊNCIAS — {args.fonte} (batch={args.batch})")
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
            print(f"  ✓ {arq.name}: sem pendências")
            continue

        print(f"\n📄 {arq.name} — {len(pendentes)} pendentes")
        modificado = False

        # Processar em batches
        i = 0
        while i < len(pendentes):
            if args.limite and total_ok >= args.limite:
                print(f"\n⏹ Limite de {args.limite} atingido.")
                break

            lote = pendentes[i:i + args.batch]

            if args.dry_run:
                nums = [str(q.get('numero','?')) for q in lote]
                print(f"  [dry] batch Q{','.join(nums)}")
                total_ok += len(lote)
                i += len(lote)
                continue

            habs = chamar_groq_batch(lote)

            if habs is None:
                # Batch falhou — tenta um a um
                print(f"  ⚠ Batch falhou, tentando 1 a 1...")
                for q in lote:
                    resp_solo = chamar_groq_batch([q])
                    if resp_solo:
                        hab = resp_solo[0]
                        q["competencia"] = hab
                        modificado = True
                        total_ok += 1
                        ok_sb = patch_supabase(q, hab)
                        print(f"  Q{q.get('numero','?'):03} → {hab} {'✓' if ok_sb else '⚠sb'}")
                    else:
                        total_erros += 1
                        print(f"  ✗ Q{q.get('numero','?'):03} sem resposta")
                    time.sleep(DELAY_APOS_LOTE)
                i += len(lote)
                continue

            # Aplicar habilidades do batch
            for q, hab in zip(lote, habs):
                q["competencia"] = hab
                modificado = True
                total_ok += 1
                ok_sb = patch_supabase(q, hab)
                print(f"  Q{q.get('numero','?'):03} [{(q.get('area') or '')[:15]}] → {hab} {'✓' if ok_sb else '⚠sb'}")

            i += len(lote)
            time.sleep(DELAY_APOS_LOTE)

        if modificado and not args.dry_run:
            arq.write_text(json.dumps(questoes, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  💾 {arq.name} salvo")

        if args.limite and total_ok >= args.limite:
            break

    duracao = time.time() - inicio
    print(f"\n{'=' * 60}")
    print(f"✅  Classificadas: {total_ok}")
    print(f"✗   Erros:        {total_erros}")
    print(f"⏱   Tempo:        {duracao / 60:.1f} min")
    if total_ok and not args.dry_run:
        print(f"⚡  Média:        {duracao / total_ok:.2f}s/questão")


if __name__ == "__main__":
    main()
