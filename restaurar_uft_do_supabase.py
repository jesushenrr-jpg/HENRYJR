"""
restaurar_uft_do_supabase.py
Baixa questões UFT do Supabase e reconstrói os JSONs locais corrompidos.
Útil após race conditions ou quando o Gemini RPD está exaurido.

Uso:
    python restaurar_uft_do_supabase.py
    python restaurar_uft_do_supabase.py --dry-run
"""
import json
import sys
import socket
import argparse
from pathlib import Path
from collections import defaultdict

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── DNS patch ────────────────────────────────────────────────────────────────
_HOST = "bmhudlpihwxvaelokugh.supabase.co"
_orig = socket.getaddrinfo
def _patch(host, port, *a, **k):
    if host == _HOST:
        host = "172.64.149.246"
    return _orig(host, port, *a, **k)
socket.getaddrinfo = _patch

import config as _cfg
_c = _cfg.carregar()
SUPABASE_URL = _c.get("url", "").rstrip("/")
SERVICE_KEY  = _c.get("key", "")

HDR = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
}

SAIDA = Path(r"C:\PROJETOS\HENRYJR\DADOS\json_uft")

# Mapeamento: (ano, dia, evento) → nome do arquivo JSON
# dia = 'manha' ou 'tarde'
# evento = None, '1_EDICAO', '2_EDICAO'
def nome_arquivo(ano: int, dia: str, evento: str | None) -> str:
    ed = f"_{evento}" if evento else ""
    return f"uft_{ano}_{dia}{ed}.json"


def baixar_questoes_uft() -> list[dict]:
    """Baixa todas as questões UFT do Supabase em páginas de 1000."""
    todas = []
    offset = 0
    page_size = 1000
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/questoes",
            params={
                "fonte": "eq.UFT",
                "select": "*",
                "offset": str(offset),
                "limit":  str(page_size),
                "order":  "ano,dia,evento,numero",
            },
            headers={**HDR, "Range-Unit": "items", "Range": f"{offset}-{offset+page_size-1}"},
            timeout=30,
        )
        if r.status_code not in (200, 206):
            print(f"✗ Erro HTTP {r.status_code}: {r.text[:200]}")
            break
        lote = r.json()
        if not lote:
            break
        todas.extend(lote)
        print(f"  Baixadas: {len(todas)} questões...")
        if len(lote) < page_size:
            break
        offset += page_size
    return todas


def agrupar_por_arquivo(questoes: list[dict]) -> dict[str, list[dict]]:
    """Agrupa questões no mesmo esquema de arquivo local."""
    grupos: dict[str, list[dict]] = defaultdict(list)
    for q in questoes:
        ano    = q.get("ano")
        dia    = q.get("dia")      # 'manha' ou 'tarde'
        evento = q.get("evento")   # None, '1_EDICAO', '2_EDICAO'
        if ano is None or dia is None:
            continue
        arq = nome_arquivo(ano, dia, evento)
        grupos[arq].append(q)
    # Ordenar por número dentro de cada grupo
    for arq in grupos:
        grupos[arq].sort(key=lambda q: q.get("numero", 0))
    return dict(grupos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Não salva arquivos")
    args = parser.parse_args()

    print("=" * 60)
    print("RESTAURAR ARQUIVOS UFT DO SUPABASE")
    print("=" * 60)

    print("\n[1/3] Baixando questões UFT do Supabase...")
    questoes = baixar_questoes_uft()
    print(f"  Total: {len(questoes)} questões")

    if not questoes:
        print("✗ Nenhuma questão baixada.")
        return

    print("\n[2/3] Agrupando por arquivo...")
    grupos = agrupar_por_arquivo(questoes)
    for arq, qs in sorted(grupos.items()):
        print(f"  {arq}: {len(qs)}q")

    print(f"\n[3/3] {'Simulando escrita' if args.dry_run else 'Salvando arquivos'}...")
    SAIDA.mkdir(parents=True, exist_ok=True)

    salvos = 0
    for arq_nome, qs in sorted(grupos.items()):
        destino = SAIDA / arq_nome
        local_atual = len(json.loads(destino.read_text(encoding="utf-8"))) if destino.exists() else 0
        supabase_n  = len(qs)

        if supabase_n <= local_atual:
            print(f"  ✓ {arq_nome}: local={local_atual}q >= supabase={supabase_n}q (sem alteração)")
            continue

        if args.dry_run:
            print(f"  [dry] {arq_nome}: {local_atual}q → {supabase_n}q")
        else:
            destino.write_text(
                json.dumps(qs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  ✅ {arq_nome}: {local_atual}q → {supabase_n}q")
            salvos += 1

    print(f"\n{'='*60}")
    if args.dry_run:
        print("(dry-run: nenhum arquivo foi alterado)")
    else:
        print(f"Arquivos restaurados: {salvos}")


if __name__ == "__main__":
    main()
