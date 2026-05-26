"""
upload_novas_questoes.py — Faz upload das questões extraídas para o Supabase.
Processa: DADOS/json_uft/, DADOS/json_exato_provas/, DADOS/json_enem_simulados/

Uso:
    python upload_novas_questoes.py                    # todas as fontes
    python upload_novas_questoes.py --fonte UFT        # só UFT
    python upload_novas_questoes.py --fonte EXATO_P    # só EXATO provas
    python upload_novas_questoes.py --fonte ENEM_SIM   # só ENEM simulados
    python upload_novas_questoes.py --dry-run          # sem inserção real
"""
import argparse
import json
import socket
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── DNS patch (mesmo padrão de upload_questoes_exato.py) ─────────────────────
_HOST = "bmhudlpihwxvaelokugh.supabase.co"
_orig = socket.getaddrinfo
def _patch(host, port, *a, **k):
    if host == _HOST:
        host = "172.64.149.246"
    return _orig(host, port, *a, **k)
socket.getaddrinfo = _patch

# ── Credenciais via config.json ───────────────────────────────────────────────
import config as _cfg
_c = _cfg.carregar()
SUPABASE_URL = _c.get("url", "").rstrip("/")
SERVICE_KEY  = _c.get("key", "")

HDR = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}

BASE = Path(r"C:\PROJETOS\HENRYJR\DADOS")

FONTES = {
    "UFT":      BASE / "json_uft",
    "EXATO_P":  BASE / "json_exato_provas",
    "ENEM_SIM": BASE / "json_enem_simulados",
}


def _strip_nulls(obj):
    """Remove null bytes recursivamente (PostgreSQL rejeita \\x00 em colunas text)."""
    if isinstance(obj, str):
        return obj.replace('\x00', '')
    if isinstance(obj, list):
        return [_strip_nulls(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items()}
    return obj


def upsert_lote(questoes: list[dict], dry_run: bool = False) -> tuple[int, int]:
    """Faz upsert em lotes de 50. Retorna (ok, erros)."""
    if dry_run:
        print(f"    [dry-run] {len(questoes)} questões NÃO inseridas")
        return len(questoes), 0

    ok = erros = 0
    for i in range(0, len(questoes), 50):
        lote = [_strip_nulls(q) for q in questoes[i:i + 50]]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/questoes",
            headers=HDR,
            json=lote,
            timeout=60,
        )
        if r.status_code in (200, 201):
            ok += len(lote)
        else:
            # Tenta um a um para identificar o problema
            for q in lote:
                r2 = requests.post(
                    f"{SUPABASE_URL}/rest/v1/questoes",
                    headers=HDR,
                    json=[q],
                    timeout=30,
                )
                if r2.status_code in (200, 201):
                    ok += 1
                else:
                    erros += 1
                    print(f"    ✗ Q{q.get('numero')} {q.get('fonte')}/{q.get('provedor','')}: "
                          f"{r2.status_code} {r2.text[:100]}")
        if i > 0 and i % 200 == 0:
            time.sleep(0.5)
    return ok, erros


def carregar_dir(pasta: Path) -> list[dict]:
    """Carrega todos os JSONs de uma pasta e retorna lista de questões."""
    todas = []
    for arq in sorted(pasta.glob("*.json")):
        try:
            data = json.loads(arq.read_text(encoding="utf-8"))
            if isinstance(data, list):
                todas.extend(data)
                print(f"  {arq.name}: {len(data)} questões")
            else:
                print(f"  ⚠ {arq.name}: formato inesperado (não é lista)")
        except Exception as e:
            print(f"  ✗ Erro ao ler {arq.name}: {e}")
    return todas


def verificar_coluna_provedor() -> bool:
    """Verifica se a coluna provedor existe na tabela questoes."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/questoes?limit=1&select=provedor",
        headers=HDR,
        timeout=15,
    )
    return r.status_code == 200


def main():
    parser = argparse.ArgumentParser(description="Upload questões para Supabase")
    parser.add_argument("--fonte", choices=["UFT", "EXATO_P", "ENEM_SIM"],
                        help="Processar só esta fonte (padrão: todas)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria inserido sem inserir de verdade")
    args = parser.parse_args()

    if not SUPABASE_URL or not SERVICE_KEY:
        print("✗ config.json não encontrado ou sem credenciais.")
        sys.exit(1)

    print("=" * 60)
    print("UPLOAD NOVAS QUESTÕES → SUPABASE")
    print("=" * 60)

    print("\n[1/3] Verificando coluna provedor...")
    if not verificar_coluna_provedor():
        print("  ✗ Coluna 'provedor' não existe.")
        print("    Execute migracao_provedor.sql no Supabase Dashboard primeiro.")
        sys.exit(1)
    print("  OK — coluna provedor existe")

    fontes_a_processar = {args.fonte: FONTES[args.fonte]} if args.fonte else FONTES
    total_ok = total_erros = 0

    for nome, pasta in fontes_a_processar.items():
        print(f"\n[{nome}] {pasta}")
        if not pasta.exists():
            print(f"  ⚠ Pasta não encontrada: {pasta}")
            print(f"    Execute primeiro o extrator correspondente.")
            continue

        jsons = list(pasta.glob("*.json"))
        if not jsons:
            print(f"  ⚠ Nenhum JSON encontrado em {pasta}")
            continue

        questoes = carregar_dir(pasta)
        print(f"  → {len(questoes)} questões a inserir")

        if not questoes:
            continue

        ok, erros = upsert_lote(questoes, dry_run=args.dry_run)
        total_ok    += ok
        total_erros += erros
        status = "✓" if erros == 0 else "⚠"
        print(f"  {status} {ok} inseridas | {erros} erros")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} inseridas | {total_erros} erros")
    if args.dry_run:
        print("(dry-run: nada foi realmente inserido)")


if __name__ == "__main__":
    main()
