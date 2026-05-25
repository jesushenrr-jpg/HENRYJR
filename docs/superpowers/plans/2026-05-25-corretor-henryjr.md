# Corretor - HenryJr Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar o `gerenciar_imagens.py` no executável portátil "CORRETOR - HenryJr", cloud-first (Supabase), com staging em memória, abas de Frases e Upload, gerenciamento de categorias, e empacotamento via PyInstaller.

**Architecture:** Refatoração modular (Opção C do spec): o editor existente migra intacto para `ui_questoes.py`; novos módulos `data_layer.py` e `staging.py` substituem o acesso a arquivos locais; `corretor.py` monta o Notebook com as três abas. O único arquivo que fala com Supabase é `data_layer.py`.

**Tech Stack:** Python 3.11+, Tkinter + ttk, Pillow, requests, matplotlib (preview LaTeX), PyInstaller 6.x

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `config.py` | Criar | Lê/escreve `config.json` próximo ao .exe; detecta caminho correto frozen vs script |
| `data_layer.py` | Criar | Toda comunicação REST com Supabase (questões + Storage) |
| `staging.py` | Criar | Acumula mudanças em memória; thread-safe; dispara batch upload |
| `ui_questoes.py` | Criar | Editor migrado de `gerenciar_imagens.py`; usa staging em vez de JSON local |
| `ui_frases.py` | Criar | Aba de gerenciamento de frases livres |
| `ui_upload.py` | Criar | Aba de progresso de upload + relatório |
| `ui_gerenciar_provas.py` | Criar | Janela de edição de categorias/subfiltros no banco |
| `corretor.py` | Criar | Ponto de entrada; monta Notebook, barra de status, menus |
| `corretor.spec` | Criar | Configuração PyInstaller |
| `build.bat` | Criar | Script de build do .exe |
| `gerenciar_imagens.py` | Manter | Não deletar até validação completa do Corretor |

---

## Paleta de Cores (Biblioteca Cálida)

Todos os módulos usam esta paleta — **não usar os valores antigos (violeta)**:

```python
BG       = "#0E0D0B"   # fundo geral
CARD     = "#161411"   # cards / painéis
BORDER   = "#2C2820"   # bordas
SURFACE  = "#1E1B17"   # surface elevada / inputs
FG       = "#F2EDE4"   # texto principal
FG2      = "#A89880"   # texto secundário
ACC      = "#D4A853"   # dourado — cor primária
ACC_HOV  = "#B8882A"   # dourado hover
DANGER   = "#f38ba8"   # vermelho erros
OK       = "#a6e3a1"   # verde sucesso
WARN     = "#fab387"   # âmbar avisos
```

---

## Task 1: config.py — Gerenciador de Credenciais

**Files:**
- Create: `config.py`

- [ ] **Step 1: Criar config.py**

```python
"""
config.py — Lê e escreve config.json próximo ao executável.

Quando frozen pelo PyInstaller: config.json fica em sys.executable/../config.json
Quando rodando como script: config.json fica em __file__/../config.json
"""
import json
import sys
from pathlib import Path


def _config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent / "config.json"


def carregar() -> dict:
    """Retorna dict com 'url' e 'key', ou {} se não existir."""
    p = _config_path()
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar(url: str, key: str) -> None:
    """Persiste as credenciais em config.json."""
    p = _config_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"url": url.strip(), "key": key.strip()}, f, indent=2)


def credenciais_ok() -> bool:
    """True se config.json existe e tem url + key não-vazios."""
    c = carregar()
    return bool(c.get("url") and c.get("key"))
```

- [ ] **Step 2: Testar no terminal Python**

```
python -c "
import config
print('ok antes:', config.credenciais_ok())
config.salvar('https://exemplo.supabase.co', 'minha-chave')
print('ok depois:', config.credenciais_ok())
c = config.carregar()
print('url:', c['url'])
"
```
Esperado:
```
ok antes: False
ok depois: True
url: https://exemplo.supabase.co
```

- [ ] **Step 3: Commit**

```bash
git add config.py
git commit -m "feat: config.py — lê/escreve config.json próximo ao .exe"
```

---

## Task 2: data_layer.py — Comunicação com Supabase

**Files:**
- Create: `data_layer.py`

- [ ] **Step 1: Criar data_layer.py**

```python
"""
data_layer.py — Toda comunicação REST com Supabase.

Usa requests diretamente (não supabase-py, que tem dependências quebradas).
Inicialize com init() antes de usar qualquer função.
"""
import io
import sys
import requests
from typing import Any

import config as _cfg

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
    r = requests.get(
        _rest("questoes"),
        headers=_headers({"Prefer": "count=exact"}),
        params={"select": "fonte", "limit": 1000},
        timeout=10,
    )
    if not r.ok:
        return []
    dados = r.json()
    vistas = set()
    result = []
    for d in dados:
        f = d.get("fonte") or "ENEM"
        if f not in vistas:
            vistas.add(f)
            result.append(f)
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
        params={"select": "ano,dia,evento,turno", "fonte": f"eq.{categoria}", "limit": 2000},
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
```

- [ ] **Step 2: Criar tabela `frases` no Supabase (executar SQL no Dashboard)**

Abrir https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh/sql/new e rodar:

```sql
CREATE TABLE IF NOT EXISTS frases (
  id         BIGSERIAL PRIMARY KEY,
  titulo     TEXT NOT NULL,
  texto      TEXT NOT NULL,
  categoria  TEXT NOT NULL DEFAULT '',
  criado_em  TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE frases ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON frases FOR ALL USING (true);
```

- [ ] **Step 3: Testar data_layer no terminal**

```
python -c "
import config, data_layer
config.salvar('https://bmhudlpihwxvaelokugh.supabase.co', 'SEU_SERVICE_KEY')
data_layer.init()
cats = data_layer.listar_categorias()
print('Categorias:', cats)
filtros = data_layer.listar_filtros('ENEM')
print('Anos ENEM:', filtros['anos'][:3], '...')
qs = data_layer.buscar_questoes('ENEM', {'ano': 2023, 'dia': 'dia1'})
print('Questoes 2023/dia1:', len(qs))
"
```
Esperado:
```
Categorias: ['ENEM', 'EXATO']
Anos ENEM: [2024, 2023, 2022] ...
Questoes 2023/dia1: 45
```

- [ ] **Step 4: Commit**

```bash
git add data_layer.py
git commit -m "feat: data_layer.py — comunicação REST com Supabase (questões, imagens, frases)"
```

---

## Task 3: staging.py — Acumulador de Mudanças

**Files:**
- Create: `staging.py`

- [ ] **Step 1: Criar staging.py**

```python
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
```

- [ ] **Step 2: Testar staging no terminal**

```
python -c "
import staging

staging.registrar_questao({'id': 1, 'numero': 12, 'area': 'Matematica'})
staging.registrar_questao({'id': 2, 'numero': 13, 'area': 'Humanas'})
staging.registrar_questao({'id': 1, 'numero': 12, 'area': 'Matematica CORRIGIDA'})  # substitui
staging.registrar_imagem('2023/dia1/q012_1.jpg', b'bytes-fake')
staging.registrar_frase({'titulo': 'Teste', 'texto': 'Frase', 'categoria': 'ENEM'})

p = staging.listar_pendentes()
print('Pendentes:', p)
assert p == {'questoes': 2, 'imagens': 1, 'frases': 1}, f'ERRO: {p}'
print('OK — staging funcionando')
"
```
Esperado:
```
Pendentes: {'questoes': 2, 'imagens': 1, 'frases': 1}
OK — staging funcionando
```

- [ ] **Step 3: Commit**

```bash
git add staging.py
git commit -m "feat: staging.py — acumulador thread-safe de mudanças em memória"
```

---

## Task 4: ui_frases.py — Aba de Frases

**Files:**
- Create: `ui_frases.py`

- [ ] **Step 1: Criar ui_frases.py**

```python
"""
ui_frases.py — Aba de gerenciamento de frases livres.

Frases são independentes de prova: cada uma tem titulo, texto e categoria livre.
Ao salvar, registra no staging (não sobe imediatamente ao Supabase).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

import data_layer as dl
import staging

# ── Paleta ────────────────────────────────────────────────────────────────────
BG      = "#0E0D0B"
CARD    = "#161411"
BORDER  = "#2C2820"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
ACC_HOV = "#B8882A"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"


class FrasesFrame(ttk.Frame):
    def __init__(self, master, on_staging_change: Callable | None = None, **kw):
        super().__init__(master, **kw)
        self.configure(style="Dark.TFrame")
        self._on_staging_change = on_staging_change
        self._frases_cache: list[dict] = []
        self._sel_idx: int | None = None
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.configure(padding=12)

        # ── Topo: botões ──────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="FRASES", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Button(top, text="↻ Atualizar", bg=SURFACE, fg=FG, relief="flat",
                  cursor="hand2", command=self._carregar).pack(side="right", padx=4)
        tk.Button(top, text="🗑 Deletar", bg=SURFACE, fg=DANGER, relief="flat",
                  cursor="hand2", command=self._deletar).pack(side="right", padx=4)
        tk.Button(top, text="💾 Salvar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self._salvar).pack(side="right", padx=4)
        tk.Button(top, text="+ Nova", bg=SURFACE, fg=FG, relief="flat",
                  cursor="hand2", command=self._nova).pack(side="right", padx=4)

        # ── Lista à esquerda ──────────────────────────────────────────────────
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True)

        lista_frame = tk.Frame(pane, bg=CARD, bd=1, relief="flat")
        lista_frame.pack(side="left", fill="y", padx=(0, 8))

        sb = tk.Scrollbar(lista_frame, orient="vertical")
        self._lista = tk.Listbox(
            lista_frame, yscrollcommand=sb.set, width=32,
            bg=CARD, fg=FG, selectbackground=ACC, selectforeground="#0E0D0B",
            activestyle="none", borderwidth=0, highlightthickness=0,
            font=("Segoe UI", 9),
        )
        sb.config(command=self._lista.yview)
        sb.pack(side="right", fill="y")
        self._lista.pack(side="left", fill="both", expand=True)
        self._lista.bind("<<ListboxSelect>>", self._ao_selecionar)

        # ── Editor à direita ──────────────────────────────────────────────────
        editor = tk.Frame(pane, bg=BG)
        editor.pack(side="left", fill="both", expand=True)

        def lbl(texto):
            tk.Label(editor, text=texto, bg=BG, fg=FG2,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 1))

        lbl("TÍTULO")
        self._ent_titulo = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                    relief="flat", font=("Segoe UI", 10))
        self._ent_titulo.pack(fill="x", ipady=4)

        lbl("CATEGORIA")
        self._ent_cat = tk.Entry(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10))
        self._ent_cat.pack(fill="x", ipady=4)

        lbl("TEXTO")
        self._txt = tk.Text(editor, bg=SURFACE, fg=FG, insertbackground=FG,
                             relief="flat", font=("Source Serif 4", 11),
                             wrap="word", height=12)
        self._txt.pack(fill="both", expand=True)

        self._lbl_status = tk.Label(editor, text="", bg=BG, fg=FG2,
                                    font=("Segoe UI", 8), anchor="w")
        self._lbl_status.pack(fill="x", pady=(4, 0))

        self._frase_id: int | None = None  # id da frase em edição (None = nova)

    def _carregar(self):
        self._frases_cache = dl.listar_frases()
        self._lista.delete(0, "end")
        for f in self._frases_cache:
            self._lista.insert("end", f.get("titulo", "—"))
        self._lbl_status.config(text=f"{len(self._frases_cache)} frases carregadas", fg=FG2)

    def _ao_selecionar(self, _=None):
        sel = self._lista.curselection()
        if not sel:
            return
        self._sel_idx = sel[0]
        f = self._frases_cache[self._sel_idx]
        self._frase_id = f.get("id")
        self._ent_titulo.delete(0, "end")
        self._ent_titulo.insert(0, f.get("titulo", ""))
        self._ent_cat.delete(0, "end")
        self._ent_cat.insert(0, f.get("categoria", ""))
        self._txt.delete("1.0", "end")
        self._txt.insert("1.0", f.get("texto", ""))

    def _nova(self):
        self._frase_id = None
        self._sel_idx = None
        self._lista.selection_clear(0, "end")
        self._ent_titulo.delete(0, "end")
        self._ent_cat.delete(0, "end")
        self._txt.delete("1.0", "end")
        self._ent_titulo.focus()

    def _salvar(self):
        titulo = self._ent_titulo.get().strip()
        texto  = self._txt.get("1.0", "end").strip()
        cat    = self._ent_cat.get().strip()
        if not titulo or not texto:
            messagebox.showwarning("Atenção", "Título e Texto são obrigatórios.")
            return
        dados: dict = {"titulo": titulo, "texto": texto, "categoria": cat}
        if self._frase_id is not None:
            dados["id"] = self._frase_id
        staging.registrar_frase(dados)
        self._lbl_status.config(text="✓ Frase registrada no staging", fg=OK)
        if self._on_staging_change:
            self._on_staging_change()

    def _deletar(self):
        if self._frase_id is None:
            messagebox.showwarning("Atenção", "Selecione uma frase existente para deletar.")
            return
        if not messagebox.askyesno("Confirmar", "Deletar esta frase do Supabase agora?"):
            return
        ok, msg = dl.deletar_frase(self._frase_id)
        if ok:
            self._lbl_status.config(text="Frase deletada", fg=OK)
            self._nova()
            self._carregar()
        else:
            self._lbl_status.config(text=f"Erro: {msg}", fg=DANGER)
```

- [ ] **Step 2: Smoke test de importação**

```
python -c "import ui_frases; print('OK — ui_frases importado sem erros')"
```
Esperado: `OK — ui_frases importado sem erros`

- [ ] **Step 3: Commit**

```bash
git add ui_frases.py
git commit -m "feat: ui_frases.py — aba de gerenciamento de frases livres"
```

---

## Task 5: ui_upload.py — Aba de Upload e Progresso

**Files:**
- Create: `ui_upload.py`

- [ ] **Step 1: Criar ui_upload.py**

```python
"""
ui_upload.py — Aba de acompanhamento de upload em batch.

Botão "Enviar pacote" dispara staging.enviar_tudo() em thread separada.
Barra de progresso e tabela atualizadas em tempo real via after().
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from datetime import datetime

import staging

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"
WARN    = "#fab387"


class UploadFrame(ttk.Frame):
    def __init__(self, master, on_staging_change: Callable | None = None, **kw):
        super().__init__(master, **kw)
        self._on_staging_change = on_staging_change
        self._historico: list[dict] = []   # {desc, ok, ts}
        self._enviando = False
        self._build_ui()

    def _build_ui(self):
        self.configure(padding=12)

        # ── Topo ─────────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="UPLOAD", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        self._btn_relatorio = tk.Button(
            top, text="📊 Ver Relatório", bg=SURFACE, fg=FG, relief="flat",
            cursor="hand2", command=self._ver_relatorio)
        self._btn_relatorio.pack(side="right", padx=4)

        self._btn_enviar = tk.Button(
            top, text="📤 Enviar pacote", bg=ACC, fg="#0E0D0B", relief="flat",
            cursor="hand2", font=("Segoe UI", 10, "bold"),
            command=self._iniciar_upload)
        self._btn_enviar.pack(side="right", padx=4)

        # ── Pendentes resumo ──────────────────────────────────────────────────
        self._lbl_pendentes = tk.Label(
            self, text="Nenhuma alteração pendente", bg=BG, fg=FG2,
            font=("Segoe UI", 9))
        self._lbl_pendentes.pack(fill="x", pady=(0, 6))

        # ── Barra de progresso ────────────────────────────────────────────────
        self._progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self._progress.pack(fill="x", pady=(0, 8))

        self._lbl_prog = tk.Label(self, text="", bg=BG, fg=FG2, font=("Segoe UI", 8))
        self._lbl_prog.pack(fill="x", pady=(0, 6))

        # ── Tabela de histórico ───────────────────────────────────────────────
        cols = ("status", "item", "horario")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self._tree.heading("status",  text="")
        self._tree.heading("item",    text="Item")
        self._tree.heading("horario", text="Horário")
        self._tree.column("status",  width=30,  anchor="center", stretch=False)
        self._tree.column("item",    width=400, anchor="w")
        self._tree.column("horario", width=80,  anchor="center", stretch=False)

        sb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    def atualizar_pendentes(self):
        """Chamado pelo corretor.py para atualizar o resumo de pendentes."""
        p = staging.listar_pendentes()
        partes = []
        if p["questoes"]: partes.append(f"{p['questoes']} questão(ões)")
        if p["imagens"]:  partes.append(f"{p['imagens']} imagem(ns)")
        if p["frases"]:   partes.append(f"{p['frases']} frase(s)")
        if partes:
            self._lbl_pendentes.config(
                text="Pendentes: " + " · ".join(partes), fg=WARN)
        else:
            self._lbl_pendentes.config(text="Nenhuma alteração pendente", fg=FG2)

    def _iniciar_upload(self):
        if self._enviando:
            return
        total = staging.total_pendentes()
        if total == 0:
            messagebox.showinfo("Upload", "Nenhuma alteração pendente.")
            return
        self._enviando = True
        self._btn_enviar.config(state="disabled")
        self._progress["value"] = 0
        self._progress["maximum"] = total
        self._n_enviados = 0

        threading.Thread(
            target=self._thread_upload,
            daemon=True,
        ).start()

    def _thread_upload(self):
        def _cb(desc: str, ok: bool):
            self.after(0, lambda d=desc, o=ok: self._on_item_enviado(d, o))

        staging.enviar_tudo(callback=_cb)
        self.after(0, self._upload_concluido)

    def _on_item_enviado(self, desc: str, ok: bool):
        self._n_enviados += 1
        self._progress["value"] = self._n_enviados
        icone = "✅" if ok else "❌"
        ts = datetime.now().strftime("%H:%M:%S")
        self._tree.insert("", 0, values=(icone, desc, ts))
        self._historico.append({"desc": desc, "ok": ok, "ts": ts})
        self._lbl_prog.config(
            text=f"{self._n_enviados}/{int(self._progress['maximum'])} itens enviados")

    def _upload_concluido(self):
        self._enviando = False
        self._btn_enviar.config(state="normal")
        self._lbl_prog.config(text="Upload concluído.")
        self.atualizar_pendentes()
        if self._on_staging_change:
            self._on_staging_change()

    def _ver_relatorio(self):
        if not self._historico:
            messagebox.showinfo("Relatório", "Nenhum upload realizado nesta sessão.")
            return
        ok_q = sum(1 for h in self._historico if h["ok"] and "Q" in h["desc"])
        er_q = sum(1 for h in self._historico if not h["ok"] and "Q" in h["desc"])
        ok_i = sum(1 for h in self._historico if h["ok"] and "img" in h["desc"])
        er_i = sum(1 for h in self._historico if not h["ok"] and "img" in h["desc"])
        ok_f = sum(1 for h in self._historico if h["ok"] and "frase" in h["desc"])
        er_f = sum(1 for h in self._historico if not h["ok"] and "frase" in h["desc"])
        ts_ultimo = self._historico[-1]["ts"] if self._historico else "—"

        msg = (
            f"📊 RELATÓRIO DA SESSÃO\n"
            f"{'─'*35}\n"
            f"Questões:  ✅ {ok_q}  ❌ {er_q}\n"
            f"Imagens:   ✅ {ok_i}  ❌ {er_i}\n"
            f"Frases:    ✅ {ok_f}  ❌ {er_f}\n"
            f"{'─'*35}\n"
            f"Total:     ✅ {ok_q+ok_i+ok_f}  ❌ {er_q+er_i+er_f}\n"
            f"Último:    {ts_ultimo}"
        )
        messagebox.showinfo("Relatório de Upload", msg)
```

- [ ] **Step 2: Smoke test**

```
python -c "import ui_upload; print('OK — ui_upload importado')"
```

- [ ] **Step 3: Commit**

```bash
git add ui_upload.py
git commit -m "feat: ui_upload.py — aba de progresso de upload em batch"
```

---

## Task 6: ui_gerenciar_provas.py — Janela de Gerenciamento de Categorias

**Files:**
- Create: `ui_gerenciar_provas.py`

- [ ] **Step 1: Criar ui_gerenciar_provas.py**

```python
"""
ui_gerenciar_provas.py — Janela Configurações → Gerenciar Provas.

Permite renomear subfiltros (evento, turno, dia) e adicionar novas categorias.
Operações de rename vão para o staging via data_layer diretamente
(UPDATE em batch — não passa pelo staging de questões individuais).
"""
import tkinter as tk
from tkinter import ttk, messagebox

import data_layer as dl

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
DANGER  = "#f38ba8"
OK      = "#a6e3a1"


class JanelaGerenciarProvas(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerenciar Provas")
        self.geometry("640x480")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        # ── Título ────────────────────────────────────────────────────────────
        tk.Label(self, text="GERENCIAR PROVAS E CATEGORIAS",
                 bg=BG, fg=ACC, font=("Segoe UI", 11, "bold")).pack(
                 fill="x", padx=14, pady=(12, 6))

        # ── Árvore de categorias/subfiltros ───────────────────────────────────
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        cols = ("categoria", "campo", "valor", "questoes")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        self._tree.heading("categoria", text="Categoria")
        self._tree.heading("campo",     text="Campo")
        self._tree.heading("valor",     text="Valor atual")
        self._tree.heading("questoes",  text="Questões")
        self._tree.column("categoria", width=100)
        self._tree.column("campo",     width=100)
        self._tree.column("valor",     width=220)
        self._tree.column("questoes",  width=80, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # ── Botões ────────────────────────────────────────────────────────────
        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=14, pady=8)

        tk.Button(bot, text="✏ Renomear selecionado", bg=SURFACE, fg=FG,
                  relief="flat", cursor="hand2",
                  command=self._renomear).pack(side="left", padx=(0, 6))
        tk.Button(bot, text="↻ Atualizar", bg=SURFACE, fg=FG,
                  relief="flat", cursor="hand2",
                  command=self._carregar).pack(side="left")

        self._lbl_status = tk.Label(bot, text="", bg=BG, fg=FG2,
                                    font=("Segoe UI", 8))
        self._lbl_status.pack(side="right")

    def _carregar(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        categorias = dl.listar_categorias()
        for cat in categorias:
            filtros = dl.listar_filtros(cat)
            if cat == "ENEM":
                for ano in filtros.get("anos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "ano", str(ano))
                    self._tree.insert("", "end", values=(cat, "ano", ano, n))
            else:
                for ev in filtros.get("eventos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "evento", ev)
                    self._tree.insert("", "end", values=(cat, "evento", ev, n))
                for tu in filtros.get("turnos", []):
                    n = dl.contar_questoes_por_subfiltro(cat, "turno", tu)
                    self._tree.insert("", "end", values=(cat, "turno", tu, n))

        self._lbl_status.config(text=f"{len(categorias)} categoria(s) carregada(s)", fg=FG2)

    def _renomear(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um item para renomear.")
            return
        vals = self._tree.item(sel[0], "values")
        cat, campo, valor_atual, n_questoes = vals

        jan = tk.Toplevel(self)
        jan.title("Renomear")
        jan.configure(bg=BG)
        jan.geometry("380x160")
        jan.resizable(False, False)

        tk.Label(jan, text=f"Renomear '{valor_atual}' ({n_questoes} questões)",
                 bg=BG, fg=FG, font=("Segoe UI", 10)).pack(padx=14, pady=(14, 6))
        ent = tk.Entry(jan, bg=SURFACE, fg=FG, insertbackground=FG,
                       relief="flat", font=("Segoe UI", 11))
        ent.insert(0, valor_atual)
        ent.pack(fill="x", padx=14, ipady=5)

        def _confirmar():
            novo = ent.get().strip()
            if not novo or novo == valor_atual:
                jan.destroy()
                return
            if not messagebox.askyesno(
                "Confirmar",
                f"Isso atualizará {n_questoes} questão(ões) no banco.\n"
                f"'{valor_atual}' → '{novo}'\n\nContinuar?",
                parent=jan,
            ):
                return
            ok, msg, n = dl.renomear_subfiltro(cat, campo, valor_atual, novo)
            if ok:
                self._lbl_status.config(text=f"✓ {msg} ({n} atualizadas)", fg=OK)
                jan.destroy()
                self._carregar()
            else:
                self._lbl_status.config(text=f"❌ {msg}", fg=DANGER)
                jan.destroy()

        tk.Button(jan, text="Confirmar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 10, "bold"),
                  command=_confirmar).pack(pady=10)

    def _nova_categoria(self):
        messagebox.showinfo(
            "Nova categoria",
            "Para adicionar uma nova categoria, insira questões com\n"
            "fonte='NOVA_CATEGORIA' via script de importação.\n"
            "A categoria aparecerá automaticamente aqui.",
        )
```

- [ ] **Step 2: Smoke test**

```
python -c "import ui_gerenciar_provas; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add ui_gerenciar_provas.py
git commit -m "feat: ui_gerenciar_provas.py — janela de gerenciamento de categorias"
```

---

## Task 7: ui_questoes.py — Editor Principal (migrado)

**Files:**
- Create: `ui_questoes.py`
- Reference: `gerenciar_imagens.py` (fonte da migração)

- [ ] **Step 1: Copiar gerenciar_imagens.py como base**

```bash
cp gerenciar_imagens.py ui_questoes.py
```

- [ ] **Step 2: Adaptar ui_questoes.py — cabeçalho e imports**

Substituir o início do arquivo (até a linha `PASTA_JSON = ...`) por:

```python
"""
ui_questoes.py — Aba principal de edição de questões.

Migrado de gerenciar_imagens.py. Principais mudanças:
- App(tk.Tk) → QuestoesFrame(ttk.Frame) para uso dentro do Notebook
- Dados lidos do Supabase via data_layer (não do JSON local)
- Salvamento registra no staging (não no disco)
- Paleta atualizada para Biblioteca Cálida (dourado, sem violeta)
"""
import io
import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import data_layer as dl
import staging as st

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MATPLOTLIB_OK = True
except ImportError:
    _MATPLOTLIB_OK = False

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

JPEG_Q      = 92
PREVIEW_MAX = (440, 280)
THUMB_MAX   = (160, 120)
LETRAS      = ["A", "B", "C", "D", "E"]
```

- [ ] **Step 3: Remover funções de acesso local (não mais usadas)**

Deletar as funções:
- `carregar_json(ano)`
- `salvar_json(ano, questoes)`
- `salvar_questao(ano, dia, num, q)`

Manter todas as outras funções helper (`img_path`, `img_posicao`, `img_como_dict`, `proxima_idx`, `posicoes_para_n`, `pil_para_tk`).

- [ ] **Step 4: Substituir a classe App por QuestoesFrame**

Renomear `class App(tk.Tk)` → `class QuestoesFrame(ttk.Frame)` e adaptar `__init__`:

```python
class QuestoesFrame(ttk.Frame):
    BG       = "#0E0D0B"
    CARD     = "#161411"
    ACC      = "#D4A853"
    FG       = "#F2EDE4"
    FG2      = "#A89880"
    ENTRY_BG = "#1E1B17"
    EDIT_BG  = "#161411"
    BTN_BG   = "#D4A853"
    BTN_FG   = "#0E0D0B"
    BTN_HOV  = "#B8882A"
    BTN_SAV  = "#40a02b"
    DANGER   = "#f38ba8"
    OK       = "#a6e3a1"
    WARN     = "#fab387"

    def __init__(self, master, on_staging_change=None, **kw):
        super().__init__(master, **kw)
        self._on_staging_change = on_staging_change   # callback → atualiza barra global

        self._questoes: list           = []
        self._q_idx: int               = 0
        self._arquivo_sel: Path | None = None
        self._preview_tk               = None
        self._thumbs: list             = []
        self._posicao_map: dict        = {}
        self._ultimo_campo             = None

        # Estado do seletor de categoria
        self._cat_atual   = "ENEM"
        self._filtros_cat = {}   # {"ano": 2023, "dia": "dia1"} ou {"evento": ..., "turno": ...}

        self._build_ui()
        self._carregar_categorias()
        self._bind_teclado()
```

- [ ] **Step 5: Adaptar _build_ui — cabeçalho**

Substituir o bloco do cabeçalho (hdr) do antigo `_build_ui` pelo seletor de categoria em cascata:

```python
    def _build_ui(self):
        C = self

        # ── Seletor de categoria em cascata ───────────────────────────────────
        nav_top = tk.Frame(self, bg=C.BG)
        nav_top.pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(nav_top, text="Prova:", bg=C.BG, fg=C.FG2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))

        self._var_cat = tk.StringVar(value="ENEM")
        self._cb_cat  = ttk.Combobox(nav_top, textvariable=self._var_cat,
                                     state="readonly", width=10)
        self._cb_cat.pack(side="left", padx=(0, 8))
        self._cb_cat.bind("<<ComboboxSelected>>", self._ao_mudar_categoria)

        # Filtro 1 (ano ou evento)
        self._lbl_f1 = tk.Label(nav_top, text="Ano:", bg=C.BG, fg=C.FG2,
                                 font=("Segoe UI", 9))
        self._lbl_f1.pack(side="left", padx=(0, 4))
        self._var_f1 = tk.StringVar()
        self._cb_f1  = ttk.Combobox(nav_top, textvariable=self._var_f1,
                                     state="readonly", width=14)
        self._cb_f1.pack(side="left", padx=(0, 8))
        self._cb_f1.bind("<<ComboboxSelected>>", self._ao_mudar_f1)

        # Filtro 2 (dia ou turno) — visível só quando aplicável
        self._lbl_f2 = tk.Label(nav_top, text="Dia:", bg=C.BG, fg=C.FG2,
                                 font=("Segoe UI", 9))
        self._lbl_f2.pack(side="left", padx=(0, 4))
        self._var_f2 = tk.StringVar()
        self._cb_f2  = ttk.Combobox(nav_top, textvariable=self._var_f2,
                                     state="readonly", width=10)
        self._cb_f2.pack(side="left", padx=(0, 8))
        self._cb_f2.bind("<<ComboboxSelected>>", self._load_questoes)

        # Indicador de staging
        self._lbl_sync = tk.Label(nav_top, text="", bg=C.BG, fg=C.FG2,
                                   font=("Segoe UI", 8))
        self._lbl_sync.pack(side="right", padx=8)

        # ── Resto do body (mesmo layout do gerenciar_imagens.py) ──────────────
        body = tk.Frame(self, bg=C.BG)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        # [manter todo o resto de _build_ui do gerenciar_imagens.py a partir do "body"]
```

- [ ] **Step 6: Adicionar métodos de navegação por categoria**

```python
    def _carregar_categorias(self):
        cats = dl.listar_categorias()
        if not cats:
            cats = ["ENEM"]
        self._cb_cat["values"] = cats
        self._var_cat.set(cats[0])
        self._ao_mudar_categoria()

    def _ao_mudar_categoria(self, _=None):
        cat = self._var_cat.get()
        self._cat_atual = cat
        filtros = dl.listar_filtros(cat)
        self._filtros_disponiveis = filtros

        if cat == "ENEM":
            self._lbl_f1.config(text="Ano:")
            anos = [str(a) for a in filtros.get("anos", [])]
            self._cb_f1["values"] = anos
            if anos:
                self._var_f1.set(anos[0])
            self._lbl_f2.config(text="Dia:")
            dias = filtros.get("dias", ["dia1", "dia2"])
            self._cb_f2["values"] = dias
            if dias:
                self._var_f2.set(dias[0])
            self._cb_f2.pack()
            self._lbl_f2.pack()
        else:
            self._lbl_f1.config(text="Evento:")
            eventos = filtros.get("eventos", [])
            self._cb_f1["values"] = eventos
            if eventos:
                self._var_f1.set(eventos[0])
            self._lbl_f2.config(text="Turno:")
            turnos = filtros.get("turnos", [])
            self._cb_f2["values"] = turnos
            if turnos:
                self._var_f2.set(turnos[0])
            self._cb_f2.pack()
            self._lbl_f2.pack()

        self._load_questoes()

    def _ao_mudar_f1(self, _=None):
        self._load_questoes()

    def _load_questoes(self, _=None):
        cat = self._cat_atual
        f1  = self._var_f1.get()
        f2  = self._var_f2.get()
        if cat == "ENEM":
            try:
                filtros = {"ano": int(f1), "dia": f2}
            except ValueError:
                return
        else:
            filtros = {"evento": f1, "turno": f2}
        self._questoes = dl.buscar_questoes(cat, filtros)
        self._q_idx = 0
        if self._questoes:
            self._mostrar()
        else:
            self._limpar_ui()
```

- [ ] **Step 7: Adaptar _salvar_questao para usar staging**

Substituir `_salvar_questao` e `_sync_supabase_questao` por:

```python
    def _salvar_questao(self, ano, dia, num, q: dict):
        """Registra questão no staging e atualiza barra global."""
        st.registrar_questao(q)
        self._lbl_sync.config(text="● staging +1", fg=self.WARN)
        if self._on_staging_change:
            self._on_staging_change()

    def _sync_supabase_imagem(self, img_bytes: bytes, caminho_remoto: str):
        """Registra imagem no staging (sem gravar no disco)."""
        st.registrar_imagem(caminho_remoto, img_bytes)
        self._lbl_sync.config(text="● img staging", fg=self.WARN)
        if self._on_staging_change:
            self._on_staging_change()
```

- [ ] **Step 8: Adaptar _adicionar_imagem para operar em memória**

No método `_adicionar_imagem`, substituir a parte que salva em disco por:

```python
        # Em vez de salvar no disco, converter para bytes e registrar no staging
        buf = io.BytesIO()
        img_pil.save(buf, format="JPEG", quality=JPEG_Q)
        img_bytes = buf.getvalue()

        # Determinar caminho remoto
        q = self._questoes[self._q_idx]
        stem = f"q{q['numero']:03d}_{proxima_idx_remoto(q)}"
        if tipo == "alternativa":
            caminho_remoto = f"{q.get('ano') or 'exato'}/{q.get('dia','exato')}/{stem}_alt_{letra}.jpg"
        else:
            caminho_remoto = f"{q.get('ano') or 'exato'}/{q.get('dia','exato')}/{stem}.jpg"

        self._sync_supabase_imagem(img_bytes, caminho_remoto)
        # Atualizar imagens[] na questão e registrar questão no staging também
        ...
```

- [ ] **Step 9: Smoke test**

```
python -c "import ui_questoes; print('OK — ui_questoes importado')"
```

- [ ] **Step 10: Commit**

```bash
git add ui_questoes.py
git commit -m "feat: ui_questoes.py — editor migrado para cloud-first com staging"
```

---

## Task 8: corretor.py — Ponto de Entrada Principal

**Files:**
- Create: `corretor.py`

- [ ] **Step 1: Criar corretor.py**

```python
"""
corretor.py — Ponto de entrada do CORRETOR - HenryJr.

Monta a janela principal com Notebook de três abas:
  - Questões (editor completo)
  - Frases (gerenciamento de frases livres)
  - Upload (progresso de envio em batch)

Menu: Configurações → Gerenciar Provas
Barra global no topo: mostra pendentes em tempo real.
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import config as cfg
import data_layer as dl
import staging

BG      = "#0E0D0B"
CARD    = "#161411"
SURFACE = "#1E1B17"
FG      = "#F2EDE4"
FG2     = "#A89880"
ACC     = "#D4A853"
WARN    = "#fab387"


# ── Tela de configuração inicial ──────────────────────────────────────────────

class TelaConfig(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CORRETOR - HenryJr — Configuração")
        self.geometry("460x260")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._ok = False
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="CORRETOR - HenryJr", bg=BG, fg=ACC,
                 font=("Segoe UI", 16, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="Configure as credenciais do Supabase para começar.",
                 bg=BG, fg=FG2, font=("Segoe UI", 9)).pack(pady=(0, 16))

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="x", padx=40)

        def lbl(t):
            tk.Label(frame, text=t, bg=BG, fg=FG2,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 1))

        lbl("SUPABASE URL")
        self._ent_url = tk.Entry(frame, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10))
        self._ent_url.pack(fill="x", ipady=5)

        lbl("SUPABASE SERVICE KEY")
        self._ent_key = tk.Entry(frame, bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief="flat", font=("Segoe UI", 10), show="•")
        self._ent_key.pack(fill="x", ipady=5)

        self._lbl_err = tk.Label(frame, text="", bg=BG, fg="#f38ba8",
                                  font=("Segoe UI", 8))
        self._lbl_err.pack(fill="x", pady=(4, 0))

        tk.Button(self, text="Conectar", bg=ACC, fg="#0E0D0B", relief="flat",
                  cursor="hand2", font=("Segoe UI", 11, "bold"),
                  command=self._conectar).pack(pady=14)

    def _conectar(self):
        url = self._ent_url.get().strip()
        key = self._ent_key.get().strip()
        if not url or not key:
            self._lbl_err.config(text="URL e Key são obrigatórios.")
            return
        cfg.salvar(url, key)
        dl.init()
        cats = dl.listar_categorias()
        if not cats:
            self._lbl_err.config(
                text="Conexão falhou — verifique URL e Key.")
            return
        self._ok = True
        self.destroy()


# ── Janela principal ──────────────────────────────────────────────────────────

class Corretor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CORRETOR - HenryJr")
        self.geometry("1380x840")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self._build_ui()
        self._atualizar_barra()

    def _build_ui(self):
        # ── Menu ─────────────────────────────────────────────────────────────
        menubar = tk.Menu(self, bg=BG, fg=FG, activebackground=ACC,
                          activeforeground="#0E0D0B", relief="flat")
        config_menu = tk.Menu(menubar, tearoff=0, bg=SURFACE, fg=FG,
                               activebackground=ACC, activeforeground="#0E0D0B")
        config_menu.add_command(label="Gerenciar Provas",
                                command=self._abrir_gerenciar_provas)
        config_menu.add_separator()
        config_menu.add_command(label="Reconfigurar credenciais",
                                command=self._reconfigurar)
        menubar.add_cascade(label="Configurações", menu=config_menu)
        self.config(menu=menubar)

        # ── Barra superior de status ──────────────────────────────────────────
        self._barra = tk.Frame(self, bg=CARD, height=28)
        self._barra.pack(fill="x")
        self._barra.pack_propagate(False)

        self._lbl_titulo = tk.Label(
            self._barra, text="  CORRETOR - HenryJr",
            bg=CARD, fg=ACC, font=("Segoe UI", 10, "bold"))
        self._lbl_titulo.pack(side="left", padx=4)

        self._lbl_pendentes = tk.Label(
            self._barra, text="", bg=CARD, fg=FG2, font=("Segoe UI", 9))
        self._lbl_pendentes.pack(side="right", padx=12)

        # ── Notebook ──────────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",       background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",   background=SURFACE, foreground=FG2,
                         padding=[14, 6], font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", ACC)])
        style.configure("Dark.TFrame",     background=BG)
        style.configure("TCombobox",
                        fieldbackground=SURFACE, background=SURFACE,
                        foreground=FG, selectbackground=ACC, arrowcolor=FG)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Importações locais (evita circular antes de terem sido definidas)
        from ui_questoes import QuestoesFrame
        from ui_frases   import FrasesFrame
        from ui_upload   import UploadFrame

        self._tab_q = QuestoesFrame(nb, on_staging_change=self._atualizar_barra,
                                     style="Dark.TFrame")
        self._tab_f = FrasesFrame(nb, on_staging_change=self._atualizar_barra,
                                   style="Dark.TFrame")
        self._tab_u = UploadFrame(nb, on_staging_change=self._atualizar_barra,
                                   style="Dark.TFrame")

        nb.add(self._tab_q, text="  Questões  ")
        nb.add(self._tab_f, text="  Frases  ")
        nb.add(self._tab_u, text="  Upload  ")

        nb.bind("<<NotebookTabChanged>>", self._ao_mudar_aba)

    def _ao_mudar_aba(self, _=None):
        self._tab_u.atualizar_pendentes()

    def _atualizar_barra(self):
        """Atualiza o texto de pendentes na barra global."""
        p = staging.listar_pendentes()
        total = p["questoes"] + p["imagens"] + p["frases"]
        if total == 0:
            self._lbl_pendentes.config(text="● 0 alterações pendentes", fg=FG2)
        else:
            partes = []
            if p["questoes"]: partes.append(f"{p['questoes']} questão(ões)")
            if p["imagens"]:  partes.append(f"{p['imagens']} imagem(ns)")
            if p["frases"]:   partes.append(f"{p['frases']} frase(s)")
            self._lbl_pendentes.config(
                text="● " + " · ".join(partes) + " pendentes", fg=WARN)

    def _abrir_gerenciar_provas(self):
        from ui_gerenciar_provas import JanelaGerenciarProvas
        JanelaGerenciarProvas(self)

    def _reconfigurar(self):
        if messagebox.askyesno("Reconfigurar",
                               "Isso encerrará o Corretor para reconfigurar as credenciais."):
            import os
            p = cfg._config_path()
            if p.exists():
                p.unlink()
            self.destroy()


# ── Inicialização ─────────────────────────────────────────────────────────────

def main():
    # Se não tem credenciais, mostrar tela de configuração
    if not cfg.credenciais_ok():
        tela = TelaConfig()
        tela.mainloop()
        if not tela._ok:
            sys.exit(0)

    # Inicializar data_layer com credenciais salvas
    if not dl.init():
        import tkinter.messagebox as mb
        mb.showerror("Erro", "Não foi possível carregar as credenciais.\n"
                             "Delete config.json e tente novamente.")
        sys.exit(1)

    app = Corretor()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Testar abertura (requer credenciais válidas em config.json)**

```
python corretor.py
```
Esperado: janela abre com as três abas, barra superior mostra "● 0 alterações pendentes"

- [ ] **Step 3: Commit**

```bash
git add corretor.py
git commit -m "feat: corretor.py — janela principal com Notebook, barra de status e menus"
```

---

## Task 9: build.bat + corretor.spec — Empacotamento .exe

**Files:**
- Create: `corretor.spec`
- Create: `build.bat`

- [ ] **Step 1: Instalar PyInstaller**

```
pip install pyinstaller
```

- [ ] **Step 2: Criar corretor.spec**

```python
# corretor.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['corretor.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PIL._tkinter_finder',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_agg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test', 'pytest', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CORRETOR-HENRYJR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,       # sem janela de terminal
    icon=None,           # adicionar .ico aqui se quiser ícone
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CORRETOR-HENRYJR',
)
```

- [ ] **Step 3: Criar build.bat**

```bat
@echo off
echo ============================================
echo   BUILD — CORRETOR - HenryJr
echo ============================================
echo.

REM Limpar builds anteriores
if exist dist\CORRETOR-HENRYJR rmdir /s /q dist\CORRETOR-HENRYJR
if exist build rmdir /s /q build

REM Gerar .exe
pyinstaller corretor.spec --clean

echo.
if exist dist\CORRETOR-HENRYJR\CORRETOR-HENRYJR.exe (
    echo [OK] Build concluido!
    echo Arquivo: dist\CORRETOR-HENRYJR\CORRETOR-HENRYJR.exe
    echo.
    echo Para distribuir, copie a pasta dist\CORRETOR-HENRYJR\ completa.
) else (
    echo [ERRO] Build falhou. Verifique os logs acima.
)
pause
```

- [ ] **Step 4: Rodar o build**

```
build.bat
```
Esperado: `[OK] Build concluido!` e pasta `dist\CORRETOR-HENRYJR\` criada.

- [ ] **Step 5: Testar o .exe**

```
dist\CORRETOR-HENRYJR\CORRETOR-HENRYJR.exe
```
Esperado: janela abre sem instalar Python.

- [ ] **Step 6: Commit**

```bash
git add corretor.spec build.bat
git commit -m "feat: corretor.spec + build.bat — empacotamento PyInstaller"
```

---

## Self-Review

### 1. Spec coverage

| Requisito do spec | Task que implementa |
|---|---|
| Renomear para CORRETOR - HenryJr | Task 8 (`title("CORRETOR - HenryJr")`) |
| Aba de frases livres | Task 4 (`ui_frases.py`) |
| Upload em staging + batch | Tasks 3 + 5 |
| Barra de progresso em tempo real | Task 5 (`UploadFrame`) |
| Barra global de pendentes no topo | Task 8 (`_atualizar_barra`) |
| Ver Relatório | Task 5 (`_ver_relatorio`) |
| Editar nomes/categorias no banco | Task 6 (`ui_gerenciar_provas.py`) |
| Cloud-first (sem arquivos locais) | Task 2 (`data_layer.py`) |
| .exe portátil | Task 9 (`build.bat`) |
| config.json na 1ª abertura | Tasks 1 + 8 |
| Suporte a ENEM + EXATO + futuras | Task 2 (`listar_categorias`) + Task 7 |
| Todas funcionalidades do editor atual | Task 7 (migração integral) |

### 2. Placeholder scan
- Nenhum TBD ou TODO encontrado.
- Task 7 Step 8 tem `...` indicando continuação — detalhe que o agente deve completar o método `_adicionar_imagem` seguindo o padrão em memória descrito.

### 3. Consistência de tipos
- `staging.registrar_questao(q: dict)` — usado em Task 7 Step 7 ✅
- `staging.registrar_imagem(caminho_remoto: str, img_bytes: bytes)` — usado em Task 7 Step 8 ✅
- `staging.registrar_frase(dados: dict)` — usado em Task 4 Step 1 ✅
- `dl.listar_categorias()` → `list[str]` — usado em Task 7 Step 6 ✅
- `dl.listar_filtros(categoria)` → `dict` — usado em Task 7 Step 6 ✅
