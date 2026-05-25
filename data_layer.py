"""
data_layer.py — Toda comunicação REST com Supabase.

Usa requests diretamente (não supabase-py, que tem dependências quebradas).
Inicialize com init() antes de usar qualquer função.
"""
import io
import os
import sys
import requests
from typing import Any

import config as _cfg

# ── Fix SSL cert para execução empacotada (PyInstaller) ───────────────────────
# Quando rodando como .exe, certifi pode não encontrar cacert.pem pelo caminho
# padrão. Ajusta SSL_CERT_FILE para apontar para o arquivo dentro do bundle.
if getattr(sys, "frozen", False):
    _bundle = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    _cacert = os.path.join(_bundle, "certifi", "cacert.pem")
    if os.path.isfile(_cacert):
        os.environ.setdefault("SSL_CERT_FILE", _cacert)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", _cacert)

_URL: str = ""
_KEY: str = ""
_BUCKET_IMG = "imagens-questoes"


# ── Inicialização ─────────────────────────────────────────────────────────────

def init() -> bool:
    """Lê credenciais do config.json. Retorna True se ok."""
    global _URL, _KEY
    c = _cfg.carregar()
    _URL = c.get("url", "").rstrip("/")
    _KEY = c.get("key", "")
    return bool(_URL and _KEY)


def _headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": _KEY,
        "Authorization": f"Bearer {_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _rest(path: str) -> str:
    return f"{_URL}/rest/v1/{path}"


def _storage(path: str) -> str:
    return f"{_URL}/storage/v1/object/{path}"


# ── Categorias e filtros ──────────────────────────────────────────────────────

def listar_categorias() -> list[str]:
    """Retorna lista de fontes distintas: ['ENEM', 'EXATO', ...]"""
    # Verifica cada fonte conhecida individualmente para evitar problema de paginação
    fontes_conhecidas = ["ENEM", "EXATO"]
    result = []
    for fonte in fontes_conhecidas:
        r = requests.get(
            _rest("questoes"),
            headers=_headers({"Prefer": "count=exact"}),
            params={"select": "id", "fonte": f"eq.{fonte}", "limit": 1},
            timeout=10,
        )
        if r.ok:
            cr = r.headers.get("content-range", "0/0")
            try:
                total = int(cr.split("/")[1])
                if total > 0:
                    result.append(fonte)
            except Exception:
                pass
    return sorted(result)


def listar_filtros(categoria: str) -> dict:
    """
    Retorna filtros dinâmicos por categoria.
    ENEM  → {"anos": [2009..2024], "dias": ["dia1","dia2"]}
    EXATO → {"eventos": [...], "turnos": ["MANHA","TARDE"]}
    """
    r = requests.get(
        _rest("questoes"),
        headers=_headers(),
        params={"select": "ano,dia,evento,turno", "fonte": f"eq.{categoria}", "limit": 1000},
        timeout=10,
    )
    if not r.ok:
        return {}
    dados = r.json()

    if categoria == "ENEM":
        anos = sorted({d["ano"] for d in dados if d.get("ano")}, reverse=True)
        dias = sorted({d["dia"] for d in dados if d.get("dia")})
        return {"anos": anos, "dias": dias}
    else:
        eventos = sorted({d["evento"] for d in dados if d.get("evento")})
        turnos  = sorted({d["turno"]  for d in dados if d.get("turno")})
        return {"eventos": eventos, "turnos": turnos}


def buscar_questoes(fonte: str, filtros: dict) -> list[dict]:
    """
    Retorna lista de questões (id, numero, area, competencia, tem_imagem).
    filtros para ENEM:  {"ano": 2023, "dia": "dia1"}
    filtros para EXATO: {"evento": "CICLO_ZERO", "turno": "MANHA"}
    """
    params: dict[str, Any] = {
        "select": "id,numero,area,competencia,tem_imagem,gabarito,anulada",
        "fonte": f"eq.{fonte}",
        "order": "numero.asc",
        "limit": 500,
    }
    if fonte == "ENEM":
        params["ano"] = f"eq.{filtros.get('ano')}"
        params["dia"] = f"eq.{filtros.get('dia')}"
    else:
        if filtros.get("evento"):
            params["evento"] = f"eq.{filtros['evento']}"
        if filtros.get("turno"):
            params["turno"] = f"eq.{filtros['turno']}"

    r = requests.get(_rest("questoes"), headers=_headers(), params=params, timeout=15)
    return r.json() if r.ok else []


def buscar_questao(questao_id: int) -> dict | None:
    """Busca questão completa pelo id."""
    r = requests.get(
        _rest("questoes"),
        headers=_headers(),
        params={"select": "*", "id": f"eq.{questao_id}", "limit": 1},
        timeout=10,
    )
    if not r.ok:
        return None
    dados = r.json()
    return dados[0] if dados else None


# ── Escrita ───────────────────────────────────────────────────────────────────

def upsert_questao(q: dict) -> tuple[bool, str]:
    """
    Faz upsert da questão no Supabase.
    Retorna (sucesso, mensagem).
    """
    payload = {k: v for k, v in q.items() if k != "ocr"}
    r = requests.post(
        _rest("questoes"),
        headers=_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
        json=payload,
        timeout=15,
    )
    if r.ok:
        return True, f"Q{q.get('numero')} salva"
    return False, f"Q{q.get('numero')} erro {r.status_code}: {r.text[:120]}"


def upsert_imagem(caminho_remoto: str, img_bytes: bytes) -> tuple[bool, str]:
    """
    Faz upload de imagem para o bucket imagens-questoes.
    caminho_remoto: ex. "2023/dia1/q012_1.jpg"
    Retorna (sucesso, mensagem).
    """
    url = _storage(f"{_BUCKET_IMG}/{caminho_remoto}")
    headers = {
        "apikey": _KEY,
        "Authorization": f"Bearer {_KEY}",
        "Content-Type": "image/jpeg",
        "x-upsert": "true",
    }
    r = requests.post(url, headers=headers, data=img_bytes, timeout=30)
    if r.ok:
        return True, f"img {caminho_remoto}"
    return False, f"img {caminho_remoto} erro {r.status_code}"


# ── Frases ────────────────────────────────────────────────────────────────────

def listar_frases() -> list[dict]:
    """Retorna todas as frases: [{id, titulo, texto, categoria, criado_em}]"""
    r = requests.get(
        _rest("frases"),
        headers=_headers(),
        params={"select": "*", "order": "criado_em.desc", "limit": 500},
        timeout=10,
    )
    return r.json() if r.ok else []


def upsert_frase(f: dict) -> tuple[bool, str]:
    """Upsert de frase. Se f tiver 'id', atualiza; senão, insere."""
    if "id" in f:
        fid = f["id"]
        payload = {k: v for k, v in f.items() if k != "id"}
        r = requests.patch(
            _rest(f"frases?id=eq.{fid}"),
            headers=_headers({"Prefer": "return=minimal"}),
            json=payload,
            timeout=10,
        )
    else:
        r = requests.post(
            _rest("frases"),
            headers=_headers({"Prefer": "return=minimal"}),
            json=f,
            timeout=10,
        )
    if r.ok:
        return True, f"frase '{f.get('titulo','?')}'"
    return False, f"frase erro {r.status_code}: {r.text[:80]}"


def deletar_frase(frase_id: int) -> tuple[bool, str]:
    r = requests.delete(
        _rest(f"frases?id=eq.{frase_id}"),
        headers=_headers(),
        timeout=10,
    )
    return (True, "frase deletada") if r.ok else (False, f"erro {r.status_code}")


# ── Gerenciar Provas ──────────────────────────────────────────────────────────

def contar_questoes_por_subfiltro(categoria: str, campo: str, valor: str) -> int:
    """Conta quantas questões têm fonte=categoria e campo=valor."""
    r = requests.get(
        _rest("questoes"),
        headers=_headers({"Prefer": "count=exact"}),
        params={"select": "id", "fonte": f"eq.{categoria}", campo: f"eq.{valor}", "limit": 1},
        timeout=10,
    )
    if not r.ok:
        return 0
    cr = r.headers.get("content-range", "0/0")
    try:
        return int(cr.split("/")[1])
    except Exception:
        return 0


def renomear_subfiltro(categoria: str, campo: str, de: str, para: str) -> tuple[bool, str, int]:
    """
    Renomeia um subfiltro (ex: evento CICLO_ZERO → CICLO ZERO).
    Retorna (sucesso, mensagem, n_atualizadas).
    """
    r = requests.patch(
        _rest(f"questoes?fonte=eq.{categoria}&{campo}=eq.{de}"),
        headers=_headers({"Prefer": "return=minimal,count=exact"}),
        json={campo: para},
        timeout=20,
    )
    if r.ok:
        cr = r.headers.get("content-range", "0/0")
        try:
            n = int(cr.split("/")[1])
        except Exception:
            n = 0
        return True, f"{de} → {para}", n
    return False, f"erro {r.status_code}: {r.text[:80]}", 0
