"""
Upload de PDFs e imagens para o Supabase Storage.

Uso:
    python upload_supabase.py --pdfs          # sobe todos os PDFs
    python upload_supabase.py --imagens       # sobe todas as imagens
    python upload_supabase.py --pdfs --imagens  # sobe tudo

Requer:
    SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY definidos abaixo
    ou em variavel de ambiente / arquivo .env

Buckets criados automaticamente se nao existirem:
    provas-pdf        (acesso publico)
    imagens-questoes  (acesso publico)
"""

import os, sys, json, time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Credenciais ───────────────────────────────────────────────────────────────
SUPABASE_URL          = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPABASE_SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")   # definir abaixo apos obter a chave

# Cole aqui a service role key (Settings → API → service_role no painel Supabase):
# SUPABASE_SERVICE_KEY = "eyJhbGci..."

PASTA_PROVAS  = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_IMAGENS = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")
PASTA_JSON_V2 = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")

BUCKET_PDFS    = "provas-pdf"
BUCKET_IMAGENS = "imagens-questoes"


# ── Helpers HTTP ──────────────────────────────────────────────────────────────

def _headers(content_type: str = "application/octet-stream") -> dict:
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  content_type,
    }


def criar_bucket(nome: str, publico: bool = True) -> None:
    url  = f"{SUPABASE_URL}/storage/v1/bucket"
    body = {"id": nome, "name": nome, "public": publico}
    r = requests.post(url, json=body, headers=_headers("application/json"))
    if r.status_code in (200, 201):
        print(f"  Bucket '{nome}' criado.")
    elif r.status_code == 409:
        print(f"  Bucket '{nome}' ja existe.")
    else:
        print(f"  [AVISO] Bucket '{nome}': {r.status_code} {r.text[:120]}")


def upload_arquivo(bucket: str, caminho_remoto: str, arquivo_local: Path,
                   content_type: str = "application/octet-stream") -> bool:
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{caminho_remoto}"
    with open(arquivo_local, "rb") as f:
        dados = f.read()
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  content_type,
        "x-upsert":      "true",          # sobrescreve se ja existir
    }
    r = requests.post(url, data=dados, headers=headers)
    return r.status_code in (200, 201)


def url_publica(bucket: str, caminho_remoto: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{caminho_remoto}"


# ── Upload de PDFs ────────────────────────────────────────────────────────────

def upload_pdfs() -> None:
    print("\n=== Upload de PDFs ===")
    criar_bucket(BUCKET_PDFS)

    pdfs = sorted(PASTA_PROVAS.rglob("*.pdf"))
    total, ok, skip = len(pdfs), 0, 0

    for i, pdf in enumerate(pdfs):
        # Caminho remoto: 2023/dia1.pdf
        partes = pdf.parts
        idx_provas = next((j for j, p in enumerate(partes) if p == "PROVAS"), None)
        if idx_provas is None:
            continue
        caminho_remoto = "/".join(partes[idx_provas + 1:])  # ex: 2023/dia1.pdf

        ct = "application/pdf"
        sucesso = upload_arquivo(BUCKET_PDFS, caminho_remoto, pdf, ct)
        status = "✓" if sucesso else "✗"
        print(f"  [{i+1:3d}/{total}] {status} {caminho_remoto}")
        if sucesso:
            ok += 1
        else:
            skip += 1

    print(f"\n  Resultado: {ok} OK  {skip} erros  (total {total})")


# ── Upload de imagens ─────────────────────────────────────────────────────────

def upload_imagens() -> None:
    print("\n=== Upload de Imagens ===")
    criar_bucket(BUCKET_IMAGENS)

    EXTENSOES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png",  ".gif": "image/gif"}

    imagens = [f for f in sorted(PASTA_IMAGENS.rglob("*"))
               if f.is_file() and f.suffix.lower() in EXTENSOES]
    total, ok, skip = len(imagens), 0, 0

    for i, img in enumerate(imagens):
        partes = img.parts
        idx_img = next((j for j, p in enumerate(partes) if p == "imagens"), None)
        if idx_img is None:
            continue
        caminho_remoto = "/".join(partes[idx_img + 1:])  # ex: 2023/dia1/q012_1.jpg
        ct = EXTENSOES.get(img.suffix.lower(), "image/jpeg")

        sucesso = upload_arquivo(BUCKET_IMAGENS, caminho_remoto, img, ct)
        status = "✓" if sucesso else "✗"
        if (i + 1) % 50 == 0 or not sucesso:
            print(f"  [{i+1:4d}/{total}] {status} {caminho_remoto}")
        ok += sucesso
        skip += not sucesso

    print(f"\n  Resultado: {ok} OK  {skip} erros  (total {total})")


# ── Atualizar JSONs com supabase_url ─────────────────────────────────────────

def atualizar_json_com_urls() -> None:
    """Adiciona supabase_url ao campo imagens de cada questao."""
    print("\n=== Atualizando JSONs com URLs do Supabase ===")
    total_q, total_img = 0, 0

    for jp in sorted(PASTA_JSON_V2.glob("enem_*.json")):
        with open(jp, encoding="utf-8") as f:
            questoes = json.load(f)

        modificado = False
        for q in questoes:
            for img in q.get("imagens") or []:
                path = img.get("path", "")
                if path and "supabase_url" not in img:
                    img["supabase_url"] = url_publica(BUCKET_IMAGENS, path)
                    modificado = True
                    total_img += 1

        if modificado:
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(questoes, f, ensure_ascii=False, indent=2)
            total_q += 1

    print(f"  {total_q} arquivos JSON atualizados  ({total_img} imagens com URL)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not SUPABASE_SERVICE_KEY:
        print("[ERRO] SUPABASE_SERVICE_ROLE_KEY nao definida.")
        print("       Abra este script e defina a variavel SUPABASE_SERVICE_KEY.")
        print("       Obtenha em: Supabase → Settings → API → service_role")
        sys.exit(1)

    fazer_pdfs    = "--pdfs"    in sys.argv or len(sys.argv) == 1
    fazer_imagens = "--imagens" in sys.argv or len(sys.argv) == 1

    if fazer_pdfs:
        upload_pdfs()
    if fazer_imagens:
        upload_imagens()
    if fazer_pdfs or fazer_imagens:
        atualizar_json_com_urls()

    print("\nUpload concluido.")


if __name__ == "__main__":
    main()
