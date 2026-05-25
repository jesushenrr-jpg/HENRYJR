"""
staging.py — Acumula mudanças em memória até o usuário clicar "Enviar pacote".

Thread-safe: usa threading.Lock internamente.
Nada sobe ao Supabase sem chamar enviar_tudo().
"""
import threading
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ItemImagem:
    caminho_remoto: str   # ex: "2023/dia1/q012_1.jpg"
    img_bytes: bytes


@dataclass
class ItemFrase:
    dados: dict           # {titulo, texto, categoria} ou {id, titulo, texto, categoria}


@dataclass
class Pendentes:
    questoes: dict = field(default_factory=dict)   # id → dict da questão
    imagens:  list = field(default_factory=list)   # list[ItemImagem]
    frases:   list = field(default_factory=list)   # list[ItemFrase]


_lock = threading.Lock()
_estado = Pendentes()


# ── Registro ──────────────────────────────────────────────────────────────────

def registrar_questao(q: dict) -> None:
    """Adiciona/substitui questão no staging pelo id."""
    with _lock:
        _estado.questoes[q["id"]] = q


def registrar_imagem(caminho_remoto: str, img_bytes: bytes) -> None:
    """Enfileira imagem para upload. Substitui se mesmo caminho já existir."""
    with _lock:
        _estado.imagens = [
            i for i in _estado.imagens if i.caminho_remoto != caminho_remoto
        ]
        _estado.imagens.append(ItemImagem(caminho_remoto, img_bytes))


def registrar_frase(dados: dict) -> None:
    """Registra frase nova ou editada. Substitui se mesmo id."""
    with _lock:
        fid = dados.get("id")
        if fid is not None:
            _estado.frases = [f for f in _estado.frases if f.dados.get("id") != fid]
        _estado.frases.append(ItemFrase(dados))


# ── Consulta ──────────────────────────────────────────────────────────────────

def listar_pendentes() -> dict:
    """Retorna snapshot: {questoes: N, imagens: N, frases: N}"""
    with _lock:
        return {
            "questoes": len(_estado.questoes),
            "imagens":  len(_estado.imagens),
            "frases":   len(_estado.frases),
        }


def total_pendentes() -> int:
    p = listar_pendentes()
    return p["questoes"] + p["imagens"] + p["frases"]


# ── Envio ─────────────────────────────────────────────────────────────────────

def enviar_tudo(callback: Callable[[str, bool], None] | None = None) -> dict:
    """
    Envia todos os itens pendentes para o Supabase.
    callback(descricao, sucesso) — chamado para cada item enviado.
    Retorna relatório: {ok: N, erro: N, detalhes: [...]}
    """
    import data_layer as dl

    with _lock:
        questoes = list(_estado.questoes.values())
        imagens  = list(_estado.imagens)
        frases   = list(_estado.frases)

    relatorio = {"ok": 0, "erro": 0, "detalhes": []}

    def _reportar(desc: str, ok: bool):
        relatorio["ok" if ok else "erro"] += 1
        relatorio["detalhes"].append({"desc": desc, "ok": ok})
        if callback:
            callback(desc, ok)

    for q in questoes:
        ok, msg = dl.upsert_questao(q)
        _reportar(msg, ok)

    for img in imagens:
        ok, msg = dl.upsert_imagem(img.caminho_remoto, img.img_bytes)
        _reportar(msg, ok)

    for fr in frases:
        ok, msg = dl.upsert_frase(fr.dados)
        _reportar(msg, ok)

    # Limpa apenas os itens que foram enviados
    with _lock:
        for q in questoes:
            _estado.questoes.pop(q["id"], None)
        enviadas = {i.caminho_remoto for i in imagens}
        _estado.imagens = [i for i in _estado.imagens if i.caminho_remoto not in enviadas]
        enviadas_f = {id(f) for f in frases}
        _estado.frases = [f for f in _estado.frases if id(f) not in enviadas_f]

    return relatorio


def limpar() -> None:
    """Descarta todo o staging sem enviar."""
    with _lock:
        _estado.questoes.clear()
        _estado.imagens.clear()
        _estado.frases.clear()
