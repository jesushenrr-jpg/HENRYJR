"""
supabase_client.py — Cliente REST minimalista para o Supabase.

Usado pelo gerenciar_imagens.py (write-through assincrono) e pelo
importar_para_supabase.py (importacao em lote).

Nao usa o SDK oficial (incompativel com Python 3.14 por dependencia pyiceberg).
"""

import socket
from pathlib import Path

import requests

# ── DNS monkey-patch ───────────────────────────────────────────────────────────
# O DNS local nao resolve *.supabase.co; forcamos o IP resolvido via 8.8.8.8
_SUPABASE_HOST = "bmhudlpihwxvaelokugh.supabase.co"
_SUPABASE_IP   = "172.64.149.246"
_orig_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == _SUPABASE_HOST:
        host = _SUPABASE_IP
    return _orig_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo

# ── Credenciais ────────────────────────────────────────────────────────────────
SUPABASE_URL = f"https://{_SUPABASE_HOST}"

SUPABASE_SERVICE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6"
    "InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ"
    ".KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"
)

TABELA         = "questoes"
BUCKET_IMAGENS = "imagens-questoes"

# ── Headers ────────────────────────────────────────────────────────────────────

def _h_json(extra_prefer: str = "") -> dict:
    prefer = "return=minimal"
    if extra_prefer:
        prefer = f"{extra_prefer},{prefer}"
    return {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        prefer,
    }

def _h_storage(content_type: str = "image/jpeg") -> dict:
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  content_type,
        "x-upsert":      "true",
    }

# ── Questoes — operacoes unitarias ─────────────────────────────────────────────

# Campos exatos da tabela com seus defaults (NOT NULL usa lista/dict/bool vazio)
_CAMPO_DEFAULTS = {
    "numero":               None,   # NOT NULL — sempre presente
    "ano":                  None,   # NOT NULL — sempre presente
    "dia":                  None,   # NOT NULL — sempre presente
    "area":                 None,
    "competencia":          None,
    "enunciado":            [],     # NOT NULL DEFAULT '[]'
    "comando":              None,
    "alternativas":         {},     # NOT NULL DEFAULT '{}'
    "gabarito":             None,
    "confianca":            None,
    "revisado":             False,  # NOT NULL DEFAULT FALSE
    "anulada":              False,  # NOT NULL DEFAULT FALSE
    "tem_imagem":           False,  # NOT NULL DEFAULT FALSE
    "pagina_pdf":           None,
    "imagens":              [],     # NOT NULL DEFAULT '[]'
    "imagens_alternativas": None,
}

def _normalizar(q: dict) -> dict:
    """
    Mapeia a questao para exatamente os campos da tabela.
    - Usa defaults corretos para campos NOT NULL (evita 23502)
    - Garante chaves identicas em todo lote (evita PGRST102)
    """
    return {
        k: q[k] if k in q and q[k] is not None else default
        for k, default in _CAMPO_DEFAULTS.items()
    }


def upsert_questao(q: dict) -> bool:
    """
    Insere ou atualiza uma questao pelo UNIQUE(ano, dia, numero).
    Retorna True se sucesso, False caso contrario.
    """
    url = f"{SUPABASE_URL}/rest/v1/{TABELA}?on_conflict=ano,dia,numero"
    try:
        r = requests.post(
            url,
            json=[_normalizar(q)],
            headers=_h_json("resolution=merge-duplicates"),
            timeout=10,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


# ── Questoes — operacoes em lote ───────────────────────────────────────────────

def upsert_lote(questoes: list, tamanho: int = 100) -> tuple:
    """
    Upsert em lotes. Seguro para re-execucao (idempotente).
    - Normaliza chaves de cada lote (evita PGRST102)
    - Prefer sem return=minimal (evita conflito com resolution)
    Retorna (total_ok, total_erros).
    """
    url  = f"{SUPABASE_URL}/rest/v1/{TABELA}?on_conflict=ano,dia,numero"
    hdrs = {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates",
    }
    ok, erros = 0, 0

    for i in range(0, len(questoes), tamanho):
        lote = questoes[i : i + tamanho]
        # Deduplica dentro do lote por (ano, dia, numero) — mantém a ultima ocorrencia
        seen: dict = {}
        for q in lote:
            key = (q.get("ano"), q.get("dia"), q.get("numero"))
            seen[key] = q
        payload = [_normalizar(q) for q in seen.values()]
        try:
            r = requests.post(url, json=payload, headers=hdrs, timeout=30)
            if r.status_code in (200, 201):
                ok += len(lote)
            else:
                erros += len(lote)
                print(f"  [ERRO lote {i // tamanho + 1}] {r.status_code}: {r.text[:200]}")
        except Exception as e:
            erros += len(lote)
            print(f"  [ERRO lote {i // tamanho + 1}] {e}")

    return ok, erros


# ── Storage — imagens ──────────────────────────────────────────────────────────

_CT_MAP = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
}

def upload_imagem(arquivo_local: Path, caminho_remoto: str) -> bool:
    """
    Faz upload de uma imagem para o bucket imagens-questoes.
    Usa x-upsert=true (sobrescreve se ja existir).
    """
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_IMAGENS}/{caminho_remoto}"
    ct  = _CT_MAP.get(Path(arquivo_local).suffix.lower(), "image/jpeg")
    try:
        with open(arquivo_local, "rb") as f:
            dados = f.read()
        r = requests.post(url, data=dados, headers=_h_storage(ct), timeout=30)
        return r.status_code in (200, 201)
    except Exception:
        return False


def deletar_imagem(caminho_remoto: str) -> bool:
    """Remove uma imagem do bucket imagens-questoes."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_IMAGENS}"
    try:
        r = requests.delete(
            url,
            json={"prefixes": [caminho_remoto]},
            headers=_h_json(),
            timeout=10,
        )
        return r.status_code in (200, 204)
    except Exception:
        return False


def url_publica(caminho_remoto: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_IMAGENS}/{caminho_remoto}"


# ── Verificacao de conectividade ───────────────────────────────────────────────

def ping() -> bool:
    """Retorna True se o Supabase esta acessivel."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABELA}",
            params={"limit": "1"},
            headers={
                "apikey":        SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            },
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False
