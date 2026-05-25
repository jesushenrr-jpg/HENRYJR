"""
Item 8: Upload dos PDFs das provas originais para o Supabase Storage.
Bucket: provas-pdf
Estrutura: {ano}/dia1.pdf, {ano}/dia2.pdf, {ano}/gabarito_dia1.pdf, {ano}/gabarito_dia2.pdf

Uso:
  python upload_provas_supabase.py            # todos os anos
  python upload_provas_supabase.py --ano 2023 # apenas 2023
  python upload_provas_supabase.py --force    # re-upload mesmo se já existir
"""

import os, sys, argparse, requests, time
from pathlib import Path

BASE     = Path("C:/PROJETOS/HENRYJR/DADOS")
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"
BUCKET   = "provas-pdf"

TIPOS_PDF = ["dia1", "dia2", "gabarito_dia1", "gabarito_dia2"]
ANOS = list(range(2009, 2025))

def upload_pdf(local_path: Path, storage_path: str, force: bool = False) -> str | None:
    """Faz upload de um PDF para o Supabase Storage. Retorna URL pública ou None."""
    if not local_path.exists():
        return None

    url = f"{SUPA_URL}/storage/v1/object/{BUCKET}/{storage_path}"
    headers = {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true" if force else "false"
    }

    with open(local_path, "rb") as f:
        data = f.read()

    size_mb = len(data) / 1024 / 1024
    print(f"  Upload {storage_path} ({size_mb:.1f} MB)...", end=" ", flush=True)

    r = requests.post(url, data=data, headers=headers, timeout=120)
    if r.status_code in (200, 201):
        pub_url = f"{SUPA_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
        print(f"OK")
        return pub_url
    elif r.status_code == 409 and not force:
        print(f"JA EXISTE (use --force para re-upload)")
        return f"{SUPA_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
    else:
        print(f"ERRO {r.status_code}: {r.text[:100]}")
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, help="Processa apenas um ano específico")
    ap.add_argument("--force", action="store_true", help="Re-upload mesmo se já existir")
    args = ap.parse_args()

    anos = [args.ano] if args.ano else ANOS

    uploaded = 0
    skipped = 0
    errors = 0

    print(f"Fazendo upload de PDFs para Supabase Storage (bucket: {BUCKET})...")
    print(f"Anos: {anos[0]}–{anos[-1]}\n")

    for ano in anos:
        pasta = BASE / "provas" / str(ano)
        if not pasta.exists():
            print(f"[{ano}] Pasta nao encontrada: {pasta}")
            continue

        print(f"[{ano}]")
        for tipo in TIPOS_PDF:
            local = pasta / f"{tipo}.pdf"
            storage_path = f"{ano}/{tipo}.pdf"
            result = upload_pdf(local, storage_path, force=args.force)
            if result:
                uploaded += 1
            elif local.exists():
                errors += 1
            else:
                skipped += 1

        time.sleep(0.2)  # pausa entre anos

    print(f"\nRESUMO:")
    print(f"  Uploadados  : {uploaded}")
    print(f"  Nao existem : {skipped}")
    print(f"  Erros       : {errors}")
    print("\nURLs disponiveis em:")
    print(f"  {SUPA_URL}/storage/v1/object/public/{BUCKET}/{{ano}}/{{tipo}}.pdf")

if __name__ == "__main__":
    main()
