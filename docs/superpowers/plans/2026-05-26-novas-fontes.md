# Novas Fontes (UFT, EXATO_PROVAS, ENEM_SIMULADOS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extrair questões de 3 novas pastas (UFT_PROVAS, EXATO_PROVAS, ENEM_SIMULADOS), adicioná-las ao Supabase e atualizar frontend + CORRETOR.

**Architecture:** Pipeline Python (lib_extrair → extratores por fonte → uploader unificado) + migração DB (coluna `provedor`) + redesign do FiltroSidebar (fonte como chips, não tabs).

**Tech Stack:** Python/PyMuPDF/requests/Groq Vision, Next.js/React/Tailwind, Supabase REST

---

## Notas de contexto para o implementador

### Constraint UNIQUE no banco
A tabela `questoes` tem constraint `UNIQUE(ano, dia, numero)`. Para evitar conflitos:
- EXATO simulados: `ano=NULL, dia='exato'`
- UFT: `ano=<year>, dia='exato'` (sem colisão com ENEM pois ENEM usa dia1/dia2)
- EXATO provas: `ano=<year>, dia='exato'`
- ENEM simulados: `ano=<year>, dia='simu_dia1'` ou `dia='simu_dia2'` (conflitaria com ENEM real se usasse 'dia1')

### Estrutura de pastas confirmada
```
DADOS/UFT_PROVAS/
  2018/                    → GAB.pdf, MANHÃ.pdf, TARDE.pdf
  2019/                    → GAB.pdf, MANHÃ.pdf, TARDE.pdf
  2021 - 1º EDIÇÃO/        → GAB.pdf, MANHÃ.pdf, TARDE.pdf
  2021 - 2º EDIÇÃO/        → GAB.pdf, MANHÃ.pdf, TARDE.pdf
  2022 - 1º EDIÇÃO/ ... 2022 - 2º EDIÇÃO/ ... (mesma estrutura)
  2023 - 1º EDIÇÃO/ ... 2023 - 2º EDIÇÃO/
  2024/                    → GAB.pdf, MANHÃ.pdf, TARDE.pdf

DADOS/EXATO_PROVAS/
  2024/                    → GAB.pdf, MANHÃ.PDF, TARDE.PDF
  2025 - 1º EDIÇÃO/        → GAB.pdf, MANHÃ.pdf, TARDE.pdf
  2025 - 2º EDIÇÃO/        → GAB PROVISÓRIO.pdf, MANHÃ.pdf, TARDE.pdf

DADOS/ENEM_SIMULADOS/
  Bernoulli 2023/Simulado 00-2023/  → "simu 00_2023 - 1º dia …", "Gab - simu 00_2023 - 1º dia …"
  Bernoulli 2024/Simulado 00/       → "1º dia Bernoulli 00 -2024.pdf", "gab 1º dia …"
  Farias Brito 2023/FB 01/          → "Simulado 01 - DIA 1 …", "Gabarito Dia 01 …"
  Poliedro 2023/Ciclo 01/           → "…_Prova.pdf", "…_Resolução.pdf"
  Poliedro 2024/01/                 → "prova d1 …", "gab D1 …", "D1 resolução …"
  SAS 2023/SAS 01/                  → "1 SAS 2023 - DIA 1 PROVA.pdf", "… GABARITO.pdf"
  SAS 2024/01/                      → "Simu 1º dia …", "GAB 1º dia …"
  Somos 2023/SOMOS 01/              → "DIA 1 SOMOS…", "GAB DIA 1 SOMOS…"
  Somos 2024/01/                    → "SOMOS 1º dia …", "gab SOMOS 1º dia …"
```

### Credenciais Groq
Definir variável de ambiente antes de rodar os extratores:
```
set GROQ_API_KEY=gsk_SEU_TOKEN_AQUI
```

### Credenciais Supabase
`config.json` no root do projeto (já existe, não commitar).

---

## File Structure

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `lib_extrair.py` | Create | Funções compartilhadas: PyMuPDF, Groq Vision, gabarito, normalização |
| `extrair_uft.py` | Create | UFT_PROVAS → JSONs em DADOS/json_uft/ |
| `extrair_exato_provas.py` | Create | EXATO_PROVAS → JSONs em DADOS/json_exato_provas/ |
| `extrair_enem_simulados.py` | Create | ENEM_SIMULADOS → JSONs em DADOS/json_enem_simulados/ |
| `upload_novas_questoes.py` | Create | JSONs das 3 fontes → Supabase |
| `frontend/components/FiltroSidebar.tsx` | Modify | Remove tabs ENEM/EXATO; adiciona chips Fonte + Provedor |
| `frontend/app/questoes/page.tsx` | Modify | Aceita `provedor` searchParam; query por provedor; UFT ordering |
| `frontend/app/simulado/page.tsx` | Modify | Adiciona filtro Fonte (ENEM/EXATO/UFT) |
| `frontend/lib/provas.ts` | Modify | Adiciona UFT; labels para simu_dia1/simu_dia2 |
| `data_layer.py` | Modify | `listar_categorias` inclui UFT; `buscar_questoes` aceita `provedor` |
| `ui_questoes.py` | Modify | Dropdown Fonte expande (UFT); Provedor dropdown condicional |

---

## Task 1: DB Migration — coluna `provedor`

**Files:**
- Create: `migracao_provedor.sql`

- [ ] **Step 1: Criar o arquivo SQL**

```sql
-- migracao_provedor.sql
-- Adiciona coluna provedor para identificar elaborador de simulados ENEM
-- (BERNOULLI, SAS, POLIEDRO, FARIAS_BRITO, SOMOS)
-- Para ENEM real, EXATO e UFT: NULL

ALTER TABLE questoes ADD COLUMN IF NOT EXISTS provedor TEXT NULL;
CREATE INDEX IF NOT EXISTS idx_questoes_provedor ON questoes(provedor);
```

Salve em `C:\PROJETOS\HENRYJR\migracao_provedor.sql`.

- [ ] **Step 2: Executar no Supabase**

Abrir o SQL Editor em https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh/sql/new e colar o conteúdo do arquivo. Clicar em "Run".

Resultado esperado: `Success. No rows returned.`

- [ ] **Step 3: Verificar**

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'questoes' AND column_name = 'provedor';
```

Resultado esperado: 1 linha com `provedor | text | YES`.

- [ ] **Step 4: Commit**

```bash
git add migracao_provedor.sql
git commit -m "feat: add provedor column to questoes table"
```

---

## Task 2: Criar `lib_extrair.py`

**Files:**
- Create: `lib_extrair.py`

- [ ] **Step 1: Escrever o arquivo**

```python
"""
lib_extrair.py — Funções compartilhadas para extração de questões.
Usada por extrair_uft.py, extrair_exato_provas.py, extrair_enem_simulados.py.
"""
import base64
import json
import os
import re
import time
from pathlib import Path

import fitz  # PyMuPDF: pip install pymupdf

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_TEXT_MODEL   = "llama-3.1-8b-instant"

AREA_ALIASES: dict[str, str] = {
    "linguagens": "Linguagens, Codigos e suas Tecnologias",
    "linguagens, códigos e suas tecnologias": "Linguagens, Codigos e suas Tecnologias",
    "linguagens, codigos e suas tecnologias": "Linguagens, Codigos e suas Tecnologias",
    "ciências humanas e suas tecnologias": "Ciencias Humanas e suas Tecnologias",
    "ciencias humanas e suas tecnologias": "Ciencias Humanas e suas Tecnologias",
    "humanas": "Ciencias Humanas e suas Tecnologias",
    "ciências da natureza e suas tecnologias": "Ciencias da Natureza e suas Tecnologias",
    "ciencias da natureza e suas tecnologias": "Ciencias da Natureza e suas Tecnologias",
    "natureza": "Ciencias da Natureza e suas Tecnologias",
    "matemática e suas tecnologias": "Matematica e suas Tecnologias",
    "matematica e suas tecnologias": "Matematica e suas Tecnologias",
    "matemática": "Matematica e suas Tecnologias",
    "matematica": "Matematica e suas Tecnologias",
}

AREAS_VALIDAS = {
    "Linguagens, Codigos e suas Tecnologias",
    "Ciencias Humanas e suas Tecnologias",
    "Ciencias da Natureza e suas Tecnologias",
    "Matematica e suas Tecnologias",
}


def normalizar_area(texto: str) -> str | None:
    """Normaliza nome de área para o padrão do banco. Retorna None se não reconhecida."""
    key = texto.strip().lower()
    for alias, canonical in AREA_ALIASES.items():
        if alias in key:
            return canonical
    # Tenta match direto
    for area in AREAS_VALIDAS:
        if area.lower() in key:
            return area
    return None


def pagina_tem_texto(texto: str, min_chars: int = 150) -> bool:
    """True se o texto extraído tem conteúdo suficiente (dispensa Vision)."""
    return len(texto.strip()) >= min_chars


def extrair_texto_pagina(doc: fitz.Document, page_num: int) -> str:
    """Extrai texto de uma página específica."""
    return doc[page_num].get_text()


def renderizar_pagina_base64(doc: fitz.Document, page_num: int, dpi: int = 200) -> str:
    """Renderiza uma página como PNG e retorna base64."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = doc[page_num].get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    return base64.b64encode(png_bytes).decode()


def _chamar_groq_json(messages: list, max_tokens: int = 4096, tentativas: int = 3) -> str | None:
    """Chama a API Groq e retorna o texto da resposta."""
    import urllib.request, urllib.error
    payload = json.dumps({
        "model": GROQ_VISION_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode()
    for t in range(tentativas):
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = 65 if t == 0 else 120
                print(f"    ↩ Rate limit 429 — aguardando {espera}s...")
                time.sleep(espera)
            elif t < tentativas - 1:
                time.sleep(10 * (t + 1))
            else:
                print(f"    ✗ Groq falhou após {tentativas} tentativas: HTTP {e.code}")
                return None
        except Exception as e:
            if t < tentativas - 1:
                time.sleep(10 * (t + 1))
            else:
                print(f"    ✗ Groq falhou: {e}")
                return None
    return None


PROMPT_EXTRAIR_QUESTOES = """Analise esta página de prova e extraia TODAS as questões visíveis.
Para cada questão retorne um objeto JSON com:
- numero (int): número da questão
- area (str): área — exatamente uma de: "Linguagens, Codigos e suas Tecnologias", "Ciencias Humanas e suas Tecnologias", "Ciencias da Natureza e suas Tecnologias", "Matematica e suas Tecnologias"
- enunciado (list[str]): parágrafos do enunciado (sem o comando)
- comando (str): frase final antes das alternativas (começa com verbo)
- alternativas (dict): {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}

Retorne JSON válido no formato:
{"questoes": [...]}

Se não houver questões na página, retorne {"questoes": []}.
Nunca inclua o número da questão nos campos de texto."""


def extrair_questoes_pagina_vision(doc: fitz.Document, page_num: int) -> list[dict]:
    """Usa Groq Vision para extrair questões de uma página como imagem."""
    img_b64 = renderizar_pagina_base64(doc, page_num)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": PROMPT_EXTRAIR_QUESTOES},
        ],
    }]
    resposta = _chamar_groq_json(messages)
    if not resposta:
        return []
    # Extrai JSON da resposta (pode ter markdown ```json ... ```)
    match = re.search(r'\{.*\}', resposta, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        questoes = data.get("questoes", [])
        # Normaliza áreas
        for q in questoes:
            if q.get("area"):
                q["area"] = normalizar_area(q["area"]) or q["area"]
        return questoes
    except json.JSONDecodeError:
        print(f"    ⚠ JSON inválido na página {page_num}")
        return []


def extrair_questoes_pdf(pdf_path: Path) -> list[dict]:
    """
    Extrai questões de um PDF usando PyMuPDF + Groq Vision fallback.
    Retorna lista de questões brutas (sem gabarito).
    """
    if not pdf_path.exists():
        print(f"  ✗ PDF não encontrado: {pdf_path}")
        return []

    doc = fitz.open(str(pdf_path))
    todas: list[dict] = []
    print(f"  Extraindo {pdf_path.name} ({len(doc)} páginas)...")

    for page_num in range(len(doc)):
        texto = extrair_texto_pagina(doc, page_num)
        if pagina_tem_texto(texto):
            # Tentativa PyMuPDF: busca padrão "QUESTÃO N" ou "N."
            questoes_pagina = _parse_questoes_texto(texto, pdf_path.name)
            if questoes_pagina:
                todas.extend(questoes_pagina)
                print(f"    Página {page_num+1}: {len(questoes_pagina)} questões (texto)")
                continue

        # Fallback: Groq Vision
        print(f"    Página {page_num+1}: usando Vision...")
        questoes_pagina = extrair_questoes_pagina_vision(doc, page_num)
        if questoes_pagina:
            todas.extend(questoes_pagina)
            print(f"    Página {page_num+1}: {len(questoes_pagina)} questões (Vision)")
        time.sleep(1)  # Evita rate limit

    doc.close()
    return todas


def _parse_questoes_texto(texto: str, nome_arquivo: str = "") -> list[dict]:
    """
    Tenta extrair questões de texto PyMuPDF usando padrão ENEM.
    Retorna [] se não conseguir detectar estrutura.
    """
    # Detecta se tem padrão de questões numeradas
    if not re.search(r'\b(?:QUESTÃO|Questão|QUEST[AÃ]O)\s+\d+', texto) and \
       not re.search(r'^\s*\d+\s*[.)]\s+[A-E]\s', texto, re.MULTILINE):
        return []
    # Por simplicidade, retorna [] — deixa para Vision quando há texto mas sem estrutura clara
    # Pode ser expandido com lógica mais robusta se necessário
    return []


# ---------------------------------------------------------------------------
# Parse de gabaritos
# ---------------------------------------------------------------------------

def parse_gabarito(pdf_path: Path) -> dict[int, str | None]:
    """
    Extrai gabarito de um PDF. Tenta múltiplos padrões em sequência.
    Retorna dict {numero: letra} onde letra pode ser None (anulada).
    """
    if not pdf_path.exists():
        print(f"  ⚠ Gabarito não encontrado: {pdf_path}")
        return {}

    doc = fitz.open(str(pdf_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()

    # Tenta cada formato em ordem de confiança
    resultado = _gabarito_tabela(texto)
    if resultado:
        return resultado

    resultado = _gabarito_numero_letra(texto)
    if resultado:
        return resultado

    resultado = _gabarito_brackets(texto)
    if resultado:
        return resultado

    # Último recurso: Groq Vision no primeiro frame
    print(f"  ⚠ Gabarito texto falhou para {pdf_path.name}, tentando Vision...")
    return _gabarito_vision(pdf_path)


def _gabarito_tabela(texto: str) -> dict[int, str | None]:
    """Formato: tabela com número e letra, ex: '01 A  02 B  03 C'"""
    pattern = re.compile(r'(\d{1,2})\s+([A-E])\b')
    resultado = {}
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 180:  # Sanity check
            resultado[num] = m.group(2).upper()
    return resultado if len(resultado) >= 5 else {}


def _gabarito_numero_letra(texto: str) -> dict[int, str | None]:
    """Formato: '1. A', '1- A', '01. A'"""
    resultado = {}
    pattern = re.compile(
        r'^(\d{1,3})[.\-]\s*([A-E]|ANULADA)(?:\s|$)',
        re.MULTILINE | re.IGNORECASE,
    )
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        val = m.group(2).upper()
        if 1 <= num <= 180:
            resultado[num] = None if val == "ANULADA" else val
    return resultado if len(resultado) >= 5 else {}


def _gabarito_brackets(texto: str) -> dict[int, str | None]:
    """Formato: '1. [A]', '01. [B]'"""
    resultado = {}
    pattern = re.compile(
        r'(\d{1,3})[.\-]\s*\[([A-E])\](?:\s*[-–]\s*(ANULADA))?',
        re.IGNORECASE,
    )
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        letra = m.group(2).upper()
        anulada = bool(m.group(3))
        if 1 <= num <= 180:
            resultado[num] = None if anulada else letra
    return resultado if len(resultado) >= 5 else {}


def _gabarito_vision(pdf_path: Path) -> dict[int, str | None]:
    """Extrai gabarito via Groq Vision quando texto falha."""
    doc = fitz.open(str(pdf_path))
    img_b64 = renderizar_pagina_base64(doc, 0)
    doc.close()

    prompt = """Esta é a página de gabarito de uma prova. Extraia todos os pares (número, resposta).
Retorne JSON: {"gabarito": {"1": "A", "2": "B", ...}}
Para questões anuladas use null. Somente números e letras A-E."""

    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": prompt},
        ],
    }]
    resposta = _chamar_groq_json(messages, max_tokens=1024)
    if not resposta:
        return {}
    match = re.search(r'\{.*\}', resposta, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group())
        gab = data.get("gabarito", {})
        return {int(k): (v.upper() if v else None) for k, v in gab.items()
                if str(k).isdigit() and (v is None or v.upper() in "ABCDE")}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Normalização de questão para o esquema do banco
# ---------------------------------------------------------------------------

def normalizar_questao_banco(
    q: dict,
    fonte: str,
    tipo: str,
    ano: int | None,
    turno: str | None,
    evento: str | None,
    provedor: str | None,
    dia: str,
    gabarito_map: dict[int, str | None],
    numero_global: int,
) -> dict:
    """
    Converte uma questão bruta para o formato do banco de dados.
    numero_global: número único para esta questão nesta fonte/prova.
    """
    num_local = q.get("numero", numero_global)
    gabarito = gabarito_map.get(num_local)
    anulada = gabarito is None and num_local in gabarito_map

    alternativas = q.get("alternativas", {})
    # Garante que alternativas é dict com chaves A-E
    if isinstance(alternativas, list):
        alternativas = {chr(65 + i): v for i, v in enumerate(alternativas)}

    enunciado = q.get("enunciado", [])
    if isinstance(enunciado, str):
        enunciado = [enunciado]

    row = {
        "numero":       numero_global,
        "ano":          ano,
        "dia":          dia,
        "area":         q.get("area") or "Linguagens, Codigos e suas Tecnologias",
        "competencia":  None,  # classificar_competencias.py depois
        "enunciado":    enunciado,
        "comando":      q.get("comando", ""),
        "alternativas": alternativas,
        "gabarito":     gabarito,
        "confianca":    0.80,
        "revisado":     False,
        "anulada":      anulada,
        "tem_imagem":   False,
        "pagina_pdf":   None,
        "imagens":      [],
        "fonte":        fonte,
        "tipo":         tipo,
        "evento":       evento,
        "turno":        turno,
        "provedor":     provedor,
    }
    return {k: v for k, v in row.items() if v is not None or k in (
        "ano", "competencia", "pagina_pdf", "evento", "turno", "provedor",
        "gabarito",
    )}
```

Salve em `C:\PROJETOS\HENRYJR\lib_extrair.py`.

- [ ] **Step 2: Verificar que PyMuPDF está instalado**

```
python -c "import fitz; print('PyMuPDF OK', fitz.__version__)"
```

Se falhar: `pip install pymupdf`

- [ ] **Step 3: Teste de smoke dos helpers**

```python
# Rodar: python -c "..."
python -c "
from lib_extrair import normalizar_area, pagina_tem_texto, parse_gabarito
from pathlib import Path
assert normalizar_area('matemática') == 'Matematica e suas Tecnologias'
assert normalizar_area('humanas') == 'Ciencias Humanas e suas Tecnologias'
assert pagina_tem_texto('x' * 200) == True
assert pagina_tem_texto('x' * 50) == False
print('lib_extrair: OK')
"
```

Esperado: `lib_extrair: OK`

- [ ] **Step 4: Commit**

```bash
git add lib_extrair.py
git commit -m "feat: lib_extrair.py — funções compartilhadas de extração"
```

---

## Task 3: Criar `extrair_uft.py`

**Files:**
- Create: `extrair_uft.py`
- Output dir: `DADOS/json_uft/`

- [ ] **Step 1: Escrever o script**

```python
"""
extrair_uft.py — Extrai questões dos vestibulares UFT (2018–2024).
Saída: DADOS/json_uft/{ano}_{turno}[_{edicao}].json

Uso:
    set GROQ_API_KEY=gsk_...
    python extrair_uft.py
    python extrair_uft.py --pasta "2024"   # só um ano
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib_extrair import extrair_questoes_pdf, parse_gabarito, normalizar_questao_banco

BASE      = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR = BASE / "DADOS" / "UFT_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_uft"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_pasta(nome: str) -> tuple[int, str | None]:
    """
    '2024' → (2024, None)
    '2021 - 1º EDIÇÃO' → (2021, '1_EDICAO')
    '2022 - 2º EDIÇÃO' → (2022, '2_EDICAO')
    """
    m_edicao = re.search(r'(\d+)º', nome)
    m_ano    = re.match(r'(\d{4})', nome)
    ano      = int(m_ano.group(1)) if m_ano else 0
    edicao   = f"{m_edicao.group(1)}_EDICAO" if m_edicao else None
    return ano, edicao


def processar_pasta(pasta: Path) -> list[dict]:
    """Processa uma subpasta (um ano/edição) e retorna questões de MANHÃ e TARDE."""
    ano, edicao = parse_pasta(pasta.name)
    if not ano:
        print(f"  ⚠ Não foi possível detectar ano em: {pasta.name}")
        return []

    evento = edicao  # None ou '1_EDICAO' / '2_EDICAO'
    resultado = []

    for turno_nome, turno_val in [("MANHÃ.pdf", "MANHA"), ("TARDE.pdf", "TARDE")]:
        prova_pdf = pasta / turno_nome
        if not prova_pdf.exists():
            # Tenta maiúscula alternativa
            prova_pdf = pasta / turno_nome.upper()
        if not prova_pdf.exists():
            print(f"  ⚠ Não encontrado: {pasta.name}/{turno_nome}")
            continue

        # Gabarito
        gab_pdf = pasta / "GAB.pdf"
        if not gab_pdf.exists():
            gab_pdf = pasta / "GAB PROVISÓRIO.pdf"

        print(f"\n  [{pasta.name}] {turno_val}")
        questoes_brutas = extrair_questoes_pdf(prova_pdf)
        gabarito_map    = parse_gabarito(gab_pdf) if gab_pdf.exists() else {}
        print(f"    → {len(questoes_brutas)} questões brutas | {len(gabarito_map)} gabaritos")

        for idx, q in enumerate(questoes_brutas):
            numero_local = q.get("numero", idx + 1)
            row = normalizar_questao_banco(
                q=q,
                fonte="UFT",
                tipo="PROVA",
                ano=ano,
                turno=turno_val,
                evento=evento,
                provedor=None,
                dia="exato",
                gabarito_map=gabarito_map,
                numero_global=numero_local,
            )
            resultado.append(row)

        # Salva JSON por turno
        sufixo = f"_{edicao}" if edicao else ""
        out = OUTPUT_DIR / f"uft_{ano}_{turno_val.lower()}{sufixo}.json"
        out.write_text(json.dumps(resultado[-len(questoes_brutas):], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    → Salvo: {out.name}")

    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pasta", help="Processar só esta subpasta (ex: '2024')")
    args = parser.parse_args()

    pastas = sorted(INPUT_DIR.iterdir()) if INPUT_DIR.exists() else []
    if args.pasta:
        pastas = [p for p in pastas if args.pasta in p.name]

    print(f"UFT_PROVAS — {len(pastas)} pastas a processar")
    total = 0
    for pasta in pastas:
        if pasta.is_dir():
            qs = processar_pasta(pasta)
            total += len(qs)

    print(f"\n✓ Total: {total} questões UFT extraídas → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

Salve em `C:\PROJETOS\HENRYJR\extrair_uft.py`.

- [ ] **Step 2: Teste com uma pasta simples**

```
cd C:\PROJETOS\HENRYJR
set GROQ_API_KEY=gsk_SEU_TOKEN_AQUI
python extrair_uft.py --pasta "2024"
```

Esperado: Cria `DADOS/json_uft/uft_2024_manha.json` e `uft_2024_tarde.json`. Cada arquivo deve ter lista de dicts com campos `numero`, `area`, `gabarito`, `fonte`, `tipo`.

- [ ] **Step 3: Rodar para todos os anos**

```
python extrair_uft.py
```

Verificar que `DADOS/json_uft/` contém arquivos para todos os anos/turnos/edições.

- [ ] **Step 4: Commit**

```bash
git add extrair_uft.py
git commit -m "feat: extrair_uft.py — extração questões UFT_PROVAS"
```

---

## Task 4: Criar `extrair_exato_provas.py`

**Files:**
- Create: `extrair_exato_provas.py`
- Output dir: `DADOS/json_exato_provas/`

- [ ] **Step 1: Escrever o script**

```python
"""
extrair_exato_provas.py — Extrai provas (não simulados) do EXATO (2024, 2025).
Saída: DADOS/json_exato_provas/{ano}_{turno}[_{edicao}].json

Uso:
    set GROQ_API_KEY=gsk_...
    python extrair_exato_provas.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib_extrair import extrair_questoes_pdf, parse_gabarito, normalizar_questao_banco

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "EXATO_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_exato_provas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_pasta(nome: str) -> tuple[int, str | None]:
    """
    '2024' → (2024, None)
    '2025 - 1º EDIÇÃO' → (2025, '1_EDICAO')
    """
    m_edicao = re.search(r'(\d+)º', nome)
    m_ano    = re.match(r'(\d{4})', nome)
    ano      = int(m_ano.group(1)) if m_ano else 0
    edicao   = f"{m_edicao.group(1)}_EDICAO" if m_edicao else None
    return ano, edicao


def processar_pasta(pasta: Path) -> list[dict]:
    ano, edicao = parse_pasta(pasta.name)
    if not ano:
        return []

    resultado = []
    for turno_nome_variantes, turno_val in [
        (["MANHÃ.pdf", "MANHÃ.PDF"], "MANHA"),
        (["TARDE.pdf", "TARDE.PDF"], "TARDE"),
    ]:
        prova_pdf = None
        for nome in turno_nome_variantes:
            p = pasta / nome
            if p.exists():
                prova_pdf = p
                break
        if not prova_pdf:
            print(f"  ⚠ Não encontrado turno {turno_val} em {pasta.name}")
            continue

        # Gabarito: aceita GAB.pdf ou GAB PROVISÓRIO.pdf
        gab_pdf = pasta / "GAB.pdf"
        if not gab_pdf.exists():
            gab_pdf = pasta / "GAB PROVISÓRIO.pdf"

        print(f"\n  [{pasta.name}] {turno_val}")
        questoes_brutas = extrair_questoes_pdf(prova_pdf)
        gabarito_map    = parse_gabarito(gab_pdf) if gab_pdf.exists() else {}
        print(f"    → {len(questoes_brutas)} questões | {len(gabarito_map)} gabaritos")

        questoes_turno = []
        for idx, q in enumerate(questoes_brutas):
            numero_local = q.get("numero", idx + 1)
            row = normalizar_questao_banco(
                q=q,
                fonte="EXATO",
                tipo="PROVA",
                ano=ano,
                turno=turno_val,
                evento=None,  # EXATO provas não têm evento
                provedor=None,
                dia="exato",
                gabarito_map=gabarito_map,
                numero_global=numero_local,
            )
            questoes_turno.append(row)

        sufixo = f"_{edicao}" if edicao else ""
        out = OUTPUT_DIR / f"exato_prova_{ano}_{turno_val.lower()}{sufixo}.json"
        out.write_text(json.dumps(questoes_turno, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    → Salvo: {out.name}")
        resultado.extend(questoes_turno)

    return resultado


def main():
    pastas = sorted(INPUT_DIR.iterdir()) if INPUT_DIR.exists() else []
    print(f"EXATO_PROVAS — {len(pastas)} pastas")
    total = 0
    for pasta in pastas:
        if pasta.is_dir():
            qs = processar_pasta(pasta)
            total += len(qs)
    print(f"\n✓ Total: {total} questões EXATO_PROVAS → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

Salve em `C:\PROJETOS\HENRYJR\extrair_exato_provas.py`.

- [ ] **Step 2: Rodar**

```
set GROQ_API_KEY=gsk_SEU_TOKEN_AQUI
python extrair_exato_provas.py
```

Verificar criação de arquivos em `DADOS/json_exato_provas/`.

- [ ] **Step 3: Commit**

```bash
git add extrair_exato_provas.py
git commit -m "feat: extrair_exato_provas.py — extração provas EXATO_PROVAS"
```

---

## Task 5: Criar `extrair_enem_simulados.py`

**Files:**
- Create: `extrair_enem_simulados.py`
- Output dir: `DADOS/json_enem_simulados/`

**Nota importante:** ENEM simulados usam `dia='simu_dia1'` / `dia='simu_dia2'` (não 'dia1'/'dia2') para evitar conflito de UNIQUE com ENEM real no mesmo ano/dia/numero.

- [ ] **Step 1: Escrever o script**

```python
"""
extrair_enem_simulados.py — Extrai simulados preditivos ENEM.
Saída: DADOS/json_enem_simulados/{provedor}_{ano}_{evento}_{dia}.json

Estrutura esperada: DADOS/ENEM_SIMULADOS/{Provedor Ano}/{Simulado X}/
  - Arquivos com padrões diversos de nome (ver comentários)

Uso:
    set GROQ_API_KEY=gsk_...
    python extrair_enem_simulados.py
    python extrair_enem_simulados.py --provedor "Bernoulli 2024"
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib_extrair import extrair_questoes_pdf, parse_gabarito, normalizar_questao_banco

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "ENEM_SIMULADOS"
OUTPUT_DIR = BASE / "DADOS" / "json_enem_simulados"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Normaliza nome da pasta para enum de provedor
PROVEDOR_MAP: dict[str, str] = {
    "bernoulli":    "BERNOULLI",
    "farias brito": "FARIAS_BRITO",
    "poliedro":     "POLIEDRO",
    "sas":          "SAS",
    "somos":        "SOMOS",
}


def normalizar_provedor(nome_pasta: str) -> str | None:
    """'Bernoulli 2023' → 'BERNOULLI'"""
    lower = nome_pasta.lower()
    for chave, enum in PROVEDOR_MAP.items():
        if chave in lower:
            return enum
    return None


def extrair_ano_pasta(nome_pasta: str) -> int | None:
    """'Bernoulli 2023' → 2023"""
    m = re.search(r'(20\d{2})', nome_pasta)
    return int(m.group(1)) if m else None


def normalizar_evento(nome_subpasta: str, provedor: str) -> str:
    """
    'Simulado 00-2023' → 'SIM_00'
    'FB 01' → 'SIM_01'
    'Ciclo 01' → 'SIM_01'
    'SAS 01' → 'SIM_01'
    'SOMOS 01' → 'SIM_01'
    '01' (número puro) → 'SIM_01'
    """
    # Busca número no final ou início da pasta
    m = re.search(r'\b0*(\d+)\b', nome_subpasta)
    if m:
        num = int(m.group(1))
        return f"SIM_{num:02d}"
    return "SIM_01"


def classificar_arquivo(nome: str) -> tuple[str | None, str | None]:
    """
    Classifica um arquivo PDF como ('prova'/'gabarito', 'simu_dia1'/'simu_dia2').
    Retorna (None, None) se não reconhecido.
    """
    n = nome.lower()

    # Detecta dia
    dia = None
    if re.search(r'1[°º]?\s*dia|dia\s*1\b|d[_\s-]?1\b|1º?\s*dia', n):
        dia = "simu_dia1"
    elif re.search(r'2[°º]?\s*dia|dia\s*2\b|d[_\s-]?2\b|2º?\s*dia', n):
        dia = "simu_dia2"

    # Detecta tipo
    tipo = None
    if re.search(r'gab|gabarito|resolu[cç]', n):
        tipo = "gabarito"
    elif re.search(r'prova|simu|s[0-9]|berno|poliedro|somos|sas|farias', n):
        tipo = "prova"

    return tipo, dia


def processar_subpasta(subpasta: Path, provedor: str, ano: int, evento: str) -> list[dict]:
    """Processa uma subpasta (um simulado) e retorna questões dia1 + dia2."""
    pdfs = list(subpasta.glob("*.pdf")) + list(subpasta.glob("*.PDF"))
    if not pdfs:
        return []

    # Organiza arquivos por (tipo, dia)
    arquivos: dict[tuple[str, str], Path] = {}
    nao_classificados = []
    for pdf in pdfs:
        tipo, dia = classificar_arquivo(pdf.name)
        if tipo and dia:
            arquivos[(tipo, dia)] = pdf
        else:
            nao_classificados.append(pdf)

    # Se não classificou por dia, tenta por posição (1 prova = dia1, 2 prova = dia2)
    if not arquivos and len(pdfs) >= 2:
        pdfs_sorted = sorted(pdfs, key=lambda p: p.name.lower())
        provas   = [p for p in pdfs_sorted if not re.search(r'gab|resolu', p.name.lower())]
        gabarito = [p for p in pdfs_sorted if re.search(r'gab|resolu', p.name.lower())]
        for i, p in enumerate(provas[:2]):
            dia = f"simu_dia{i+1}"
            arquivos[("prova", dia)] = p
        for i, g in enumerate(gabarito[:2]):
            dia = f"simu_dia{i+1}"
            arquivos[("gabarito", dia)] = g

    resultado = []
    for dia_val in ["simu_dia1", "simu_dia2"]:
        prova_pdf = arquivos.get(("prova", dia_val))
        gab_pdf   = arquivos.get(("gabarito", dia_val))

        if not prova_pdf:
            continue

        print(f"\n    [{subpasta.name}] {dia_val}")
        questoes_brutas = extrair_questoes_pdf(prova_pdf)
        gabarito_map    = parse_gabarito(gab_pdf) if gab_pdf else {}
        print(f"      → {len(questoes_brutas)} questões | {len(gabarito_map)} gabaritos")

        questoes_dia = []
        for idx, q in enumerate(questoes_brutas):
            numero_local = q.get("numero", idx + 1)
            row = normalizar_questao_banco(
                q=q,
                fonte="ENEM",
                tipo="SIMULADO",
                ano=ano,
                turno=None,
                evento=evento,
                provedor=provedor,
                dia=dia_val,
                gabarito_map=gabarito_map,
                numero_global=numero_local,
            )
            questoes_dia.append(row)

        out = OUTPUT_DIR / f"{provedor.lower()}_{ano}_{evento}_{dia_val}.json"
        out.write_text(json.dumps(questoes_dia, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"      → Salvo: {out.name}")
        resultado.extend(questoes_dia)

    return resultado


def processar_pasta_provedor(pasta: Path) -> list[dict]:
    """Processa 'Bernoulli 2023' (uma pasta provedor+ano)."""
    provedor = normalizar_provedor(pasta.name)
    ano      = extrair_ano_pasta(pasta.name)
    if not provedor or not ano:
        print(f"  ⚠ Não reconhecido: {pasta.name}")
        return []

    print(f"\n{pasta.name} → provedor={provedor}, ano={ano}")
    subpastas = sorted(p for p in pasta.iterdir() if p.is_dir())
    resultado = []
    for subpasta in subpastas:
        evento = normalizar_evento(subpasta.name, provedor)
        qs = processar_subpasta(subpasta, provedor, ano, evento)
        resultado.extend(qs)

    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provedor", help="Processar só esta pasta (ex: 'Bernoulli 2024')")
    args = parser.parse_args()

    pastas = sorted(INPUT_DIR.iterdir()) if INPUT_DIR.exists() else []
    if args.provedor:
        pastas = [p for p in pastas if args.provedor.lower() in p.name.lower()]

    print(f"ENEM_SIMULADOS — {len(pastas)} pastas a processar")
    total = 0
    for pasta in pastas:
        if pasta.is_dir():
            qs = processar_pasta_provedor(pasta)
            total += len(qs)

    print(f"\n✓ Total: {total} questões ENEM_SIMULADOS → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

Salve em `C:\PROJETOS\HENRYJR\extrair_enem_simulados.py`.

- [ ] **Step 2: Testar com um provider pequeno**

```
set GROQ_API_KEY=gsk_SEU_TOKEN_AQUI
python extrair_enem_simulados.py --provedor "Farias Brito 2023"
```

Verificar: criação de `DADOS/json_enem_simulados/FARIAS_BRITO_2023_SIM_01_simu_dia1.json` e `_simu_dia2.json`.

- [ ] **Step 3: Rodar todos**

```
python extrair_enem_simulados.py
```

- [ ] **Step 4: Commit**

```bash
git add extrair_enem_simulados.py
git commit -m "feat: extrair_enem_simulados.py — extração simulados ENEM preditivos"
```

---

## Task 6: Criar `upload_novas_questoes.py`

**Files:**
- Create: `upload_novas_questoes.py`

- [ ] **Step 1: Escrever o script**

```python
"""
upload_novas_questoes.py — Faz upload das questões extraídas para o Supabase.
Processa: DADOS/json_uft/, DADOS/json_exato_provas/, DADOS/json_enem_simulados/

Uso:
    python upload_novas_questoes.py
    python upload_novas_questoes.py --fonte UFT        # só UFT
    python upload_novas_questoes.py --fonte EXATO_P    # só EXATO provas
    python upload_novas_questoes.py --fonte ENEM_SIM   # só ENEM simulados
    python upload_novas_questoes.py --dry-run          # sem inserção real
"""
import argparse
import json
import re
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
    if isinstance(obj, str):
        return obj.replace('\x00', '')
    if isinstance(obj, list):
        return [_strip_nulls(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items()}
    return obj


def upsert_lote(questoes: list[dict], dry_run: bool = False) -> tuple[int, int]:
    if dry_run:
        print(f"    [dry-run] {len(questoes)} questões NÃO inseridas")
        return len(questoes), 0

    ok = erros = 0
    for i in range(0, len(questoes), 50):
        lote = questoes[i:i + 50]
        lote_limpo = [_strip_nulls(q) for q in lote]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/questoes",
            headers=HDR,
            json=lote_limpo,
            timeout=60,
        )
        if r.status_code in (200, 201):
            ok += len(lote)
        else:
            # Tenta um a um
            for q in lote_limpo:
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
                    print(f"    ✗ Q{q.get('numero')} {q.get('fonte')}: {r2.status_code} {r2.text[:100]}")
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
        except Exception as e:
            print(f"  ✗ Erro ao ler {arq.name}: {e}")
    return todas


def verificar_coluna_provedor() -> bool:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/questoes?limit=1&select=provedor",
        headers=HDR,
        timeout=15,
    )
    return r.status_code == 200


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonte", choices=["UFT", "EXATO_P", "ENEM_SIM"],
                        help="Processar só esta fonte")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra o que seria inserido sem inserir")
    args = parser.parse_args()

    if not SUPABASE_URL or not SERVICE_KEY:
        print("✗ config.json não encontrado ou sem credenciais.")
        sys.exit(1)

    print("=" * 60)
    print("UPLOAD NOVAS QUESTÕES → SUPABASE")
    print("=" * 60)

    print("\n[1/3] Verificando coluna provedor...")
    if not verificar_coluna_provedor():
        print("  ✗ Coluna 'provedor' não existe. Execute migracao_provedor.sql primeiro.")
        sys.exit(1)
    print("  OK")

    fontes_a_processar = {args.fonte: FONTES[args.fonte]} if args.fonte else FONTES
    total_ok = total_erros = 0

    for nome, pasta in fontes_a_processar.items():
        print(f"\n[{nome}] {pasta}")
        if not pasta.exists():
            print(f"  ⚠ Pasta não encontrada: {pasta}")
            continue

        questoes = carregar_dir(pasta)
        print(f"  → {len(questoes)} questões a inserir")

        if not questoes:
            continue

        ok, erros = upsert_lote(questoes, dry_run=args.dry_run)
        total_ok    += ok
        total_erros += erros
        print(f"  ✓ {ok} inseridas | ✗ {erros} erros")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} inseridas | {total_erros} erros")
    if args.dry_run:
        print("(dry-run: nada foi inserido)")


if __name__ == "__main__":
    main()
```

Salve em `C:\PROJETOS\HENRYJR\upload_novas_questoes.py`.

- [ ] **Step 2: Dry-run para verificar sem inserir**

```
python upload_novas_questoes.py --dry-run
```

Esperado: lista os arquivos JSON encontrados e conta questões sem inserir.

- [ ] **Step 3: Upload real (depois dos extratores rodarem)**

```
python upload_novas_questoes.py --fonte UFT
python upload_novas_questoes.py --fonte EXATO_P
python upload_novas_questoes.py --fonte ENEM_SIM
```

Verificar no Supabase Dashboard → Table Editor → questoes: novas linhas com fonte='UFT', fonte='EXATO'/tipo='PROVA', provedor='BERNOULLI' etc.

- [ ] **Step 4: Commit**

```bash
git add upload_novas_questoes.py
git commit -m "feat: upload_novas_questoes.py — uploader unificado UFT/EXATO_P/ENEM_SIM"
```

---

## Task 7: Frontend — Reescrever `FiltroSidebar.tsx`

**Files:**
- Modify: `frontend/components/FiltroSidebar.tsx`
- Modify: `frontend/lib/provas.ts`

Antes de editar, entenda a estrutura atual: o sidebar tem tabs [ENEM][EXATO] no topo, seguidas de TipoToggle, seguidas de filtros condicionais. O novo design **remove as tabs** e coloca Fonte como chips dentro de um FilterGroup.

- [ ] **Step 1: Atualizar `lib/provas.ts`**

```typescript
// frontend/lib/provas.ts
export interface Prova {
  id: string
  nome: string
  descricao: string
  cor: string
  corDark: string
  bg: string
  text: string
  border: string
  anos?: number[]
  eventos?: string[]
}

export const PROVAS: Prova[] = [
  {
    id: 'ENEM',
    nome: 'ENEM',
    descricao: 'Exame Nacional do Ensino Médio',
    cor: '#3B82F6',
    corDark: '#1D4ED8',
    bg: 'bg-blue-500/15',
    text: 'text-blue-300',
    border: 'border-blue-500/30',
    anos: Array.from({ length: 16 }, (_, i) => 2024 - i),
  },
  {
    id: 'EXATO',
    nome: 'EXATO',
    descricao: 'Simulados e Provas TESSAT/EXATO',
    cor: '#F59E0B',
    corDark: '#B45309',
    bg: 'bg-amber-500/15',
    text: 'text-amber-300',
    border: 'border-amber-500/30',
    eventos: ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS'],
  },
  {
    id: 'UFT',
    nome: 'UFT',
    descricao: 'Vestibular da UFT (2018–2024)',
    cor: '#10B981',
    corDark: '#059669',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-300',
    border: 'border-emerald-500/30',
  },
]

export const PROVA_MAP = Object.fromEntries(PROVAS.map(p => [p.id, p]))

// Label amigável para eventos EXATO
export const EVENTO_LABEL: Record<string, string> = {
  'CICLO_ZERO':          'Ciclo Zero',
  '1_SIMULADO_TESSAT':   '1º Simulado',
  '2_SIMULADO_TESSAT':   '2º Simulado',
  'OUTUBRO_2025':        'Outubro 2025',
  'ABRIL_2026':          'Abril 2026',
  'NATUREZAS_TESSAT':    'Naturezas',
  'TRADICIONAIS':        'Tradicionais',
  // ENEM simulados
  'SIM_00': 'Sim. 00', 'SIM_01': 'Sim. 01', 'SIM_02': 'Sim. 02',
  'SIM_03': 'Sim. 03', 'SIM_04': 'Sim. 04', 'SIM_05': 'Sim. 05',
  'SIM_06': 'Sim. 06', 'SIM_07': 'Sim. 07', 'SIM_08': 'Sim. 08',
  // UFT edições
  '1_EDICAO': '1ª Edição', '2_EDICAO': '2ª Edição',
}

// Label para 'dia' (inclui simu_dia1/simu_dia2)
export const DIA_LABEL: Record<string, string> = {
  'dia1':      '1º Dia',
  'dia2':      '2º Dia',
  'simu_dia1': '1º Dia',
  'simu_dia2': '2º Dia',
}

// Label para provedores
export const PROVEDOR_LABEL: Record<string, string> = {
  'BERNOULLI':   'Bernoulli',
  'SAS':         'SAS',
  'POLIEDRO':    'Poliedro',
  'FARIAS_BRITO':'Farias Brito',
  'SOMOS':       'Somos',
}
```

- [ ] **Step 2: Reescrever `FiltroSidebar.tsx`**

```typescript
'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useTransition } from 'react'
import { COMPETENCIAS, TODAS_HABILIDADES } from '@/lib/competencias'
import { EVENTO_LABEL, PROVEDOR_LABEL } from '@/lib/provas'
import TipoToggle from '@/components/TipoToggle'

interface Props {
  anos: number[]
  areas: string[]
  anoAtivo?: number
  diaAtivo?: string
  areaAtiva?: string
  competenciaAtiva?: string
  fonteAtiva?: string
  eventoAtivo?: string
  turnoAtivo?: string
  tipoAtivo?: string
  provedorAtivo?: string
}

const AREA_META: Record<string, { label: string; bg: string; text: string; border: string }> = {
  'Linguagens, Codigos e suas Tecnologias':   { label: 'Linguagens',  bg: 'bg-sky-500/15',     text: 'text-sky-300',     border: 'border-sky-500/30' },
  'Ciencias Humanas e suas Tecnologias':      { label: 'Humanas',     bg: 'bg-amber-500/15',   text: 'text-amber-300',   border: 'border-amber-500/30' },
  'Ciencias da Natureza e suas Tecnologias':  { label: 'C. Natureza', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  'Matematica e suas Tecnologias':            { label: 'Matemática',  bg: 'bg-violet-500/15',  text: 'text-violet-300',  border: 'border-violet-500/30' },
}

const EVENTOS_EXATO = ['CICLO_ZERO', '1_SIMULADO_TESSAT', '2_SIMULADO_TESSAT', 'OUTUBRO_2025', 'ABRIL_2026', 'NATUREZAS_TESSAT', 'TRADICIONAIS']
const PROVEDORES    = ['BERNOULLI', 'SAS', 'POLIEDRO', 'FARIAS_BRITO', 'SOMOS']
const FONTES        = [
  { key: 'ENEM',  label: 'ENEM',  colorActive: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  { key: 'EXATO', label: 'EXATO', colorActive: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  { key: 'UFT',   label: 'UFT',   colorActive: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
]

export default function FiltroSidebar({
  anos, areas, anoAtivo, diaAtivo, areaAtiva, competenciaAtiva,
  fonteAtiva, eventoAtivo, turnoAtivo, tipoAtivo, provedorAtivo,
}: Props) {
  const [anosExpandido, setAnosExpandido] = useState(false)
  const [compExpandido,  setCompExpandido] = useState(false)
  const pathname = usePathname()
  const router   = useRouter()
  const [, startTransition] = useTransition()

  const isExato = fonteAtiva === 'EXATO'
  const isUFT   = fonteAtiva === 'UFT'
  const isEnem  = !fonteAtiva || fonteAtiva === 'ENEM'

  function url(overrides: Record<string, string | undefined>) {
    const p: Record<string, string> = {}
    if (fonteAtiva)       p.fonte       = fonteAtiva
    if (anoAtivo)         p.ano         = String(anoAtivo)
    if (diaAtivo)         p.dia         = diaAtivo
    if (areaAtiva)        p.area        = areaAtiva
    if (competenciaAtiva) p.competencia = competenciaAtiva
    if (eventoAtivo)      p.evento      = eventoAtivo
    if (turnoAtivo)       p.turno       = turnoAtivo
    if (tipoAtivo)        p.tipo        = tipoAtivo
    if (provedorAtivo)    p.provedor    = provedorAtivo
    for (const [k, v] of Object.entries(overrides)) {
      if (v === undefined) delete p[k]
      else p[k] = v
    }
    return `${pathname}?${new URLSearchParams(p)}`
  }

  function nav(href: string) { startTransition(() => router.push(href)) }

  function switchFonte(fonte: string | undefined) {
    const params: Record<string, string> = {}
    if (fonte) params.fonte = fonte
    if (tipoAtivo) params.tipo = tipoAtivo
    startTransition(() => router.push(`${pathname}?${new URLSearchParams(params)}`))
  }

  const anosVisiveis = anosExpandido ? anos : anos.slice(0, 8)
  const habilidades  = compExpandido ? TODAS_HABILIDADES : TODAS_HABILIDADES.slice(0, 15)

  const hasFilter = anoAtivo || diaAtivo || areaAtiva || competenciaAtiva
    || eventoAtivo || turnoAtivo || tipoAtivo || provedorAtivo
    || (fonteAtiva && fonteAtiva !== 'ENEM')

  return (
    <div className="space-y-3">

      {/* Toggle Tipo */}
      <TipoToggle full />

      {/* Filtros numa caixa */}
      <div className="rounded-xl bg-[#161411] border border-[#2C2820] divide-y divide-[#2C2820]">

        {/* Fonte */}
        <FilterGroup title="Fonte">
          <div className="flex flex-wrap gap-1.5">
            <Chip active={!fonteAtiva || fonteAtiva === 'ENEM'} onClick={() => switchFonte('ENEM')}>
              ENEM
            </Chip>
            {FONTES.filter(f => f.key !== 'ENEM').map(f => (
              <Chip
                key={f.key}
                active={fonteAtiva === f.key}
                onClick={() => switchFonte(fonteAtiva === f.key ? 'ENEM' : f.key)}
                colorClass={fonteAtiva === f.key ? f.colorActive : ''}
              >
                {f.label}
              </Chip>
            ))}
          </div>
        </FilterGroup>

        {/* ── Filtros ENEM Provas ── */}
        {isEnem && tipoAtivo !== 'SIMULADO' && (
          <>
            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined, competencia: undefined }))}>
                  Todas
                </Chip>
                {areas.map(a => {
                  const m = AREA_META[a]; const ativo = areaAtiva === a
                  return (
                    <Chip key={a} active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a, competencia: undefined }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}>
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>

            <FilterGroup title="Ano">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!anoAtivo} onClick={() => nav(url({ ano: undefined }))}>Todos</Chip>
                {anosVisiveis.map(y => (
                  <Chip key={y} active={anoAtivo === y}
                    onClick={() => nav(url({ ano: anoAtivo === y ? undefined : String(y) }))}>
                    {y}
                  </Chip>
                ))}
              </div>
              {anos.length > 8 && (
                <button onClick={() => setAnosExpandido(v => !v)}
                  className="mt-2 text-[10px] text-[#635D56] hover:text-[#9E9589] transition">
                  {anosExpandido ? '▲ menos' : `▼ +${anos.length - 8} anos`}
                </button>
              )}
            </FilterGroup>

            <FilterGroup title="Dia">
              <div className="flex gap-1.5">
                <Chip active={!diaAtivo} onClick={() => nav(url({ dia: undefined }))}>Todos</Chip>
                <Chip active={diaAtivo === 'dia1'} onClick={() => nav(url({ dia: diaAtivo === 'dia1' ? undefined : 'dia1' }))}>1º Dia</Chip>
                <Chip active={diaAtivo === 'dia2'} onClick={() => nav(url({ dia: diaAtivo === 'dia2' ? undefined : 'dia2' }))}>2º Dia</Chip>
              </div>
            </FilterGroup>

            <FilterGroup title="Competência H01–H30">
              <div className="flex flex-wrap gap-1">
                <Chip small active={!competenciaAtiva} onClick={() => nav(url({ competencia: undefined }))}>Todas</Chip>
                {habilidades.map(h => (
                  <Chip key={h} small active={competenciaAtiva === h}
                    onClick={() => nav(url({ competencia: competenciaAtiva === h ? undefined : h }))}
                    title={COMPETENCIAS[h]?.descricao}>{h}</Chip>
                ))}
              </div>
              <button onClick={() => setCompExpandido(v => !v)}
                className="mt-2 text-[10px] text-[#635D56] hover:text-[#9E9589] transition">
                {compExpandido ? '▲ menos' : '▼ ver H16–H30'}
              </button>
            </FilterGroup>
          </>
        )}

        {/* ── Filtros ENEM Simulados ── */}
        {isEnem && tipoAtivo === 'SIMULADO' && (
          <>
            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined }))}>Todas</Chip>
                {areas.map(a => {
                  const m = AREA_META[a]; const ativo = areaAtiva === a
                  return (
                    <Chip key={a} active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}>
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>

            <FilterGroup title="Provedor">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!provedorAtivo} onClick={() => nav(url({ provedor: undefined }))}>Todos</Chip>
                {PROVEDORES.map(p => (
                  <Chip key={p} active={provedorAtivo === p}
                    onClick={() => nav(url({ provedor: provedorAtivo === p ? undefined : p }))}>
                    {PROVEDOR_LABEL[p] ?? p}
                  </Chip>
                ))}
              </div>
            </FilterGroup>

            <FilterGroup title="Ano">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!anoAtivo} onClick={() => nav(url({ ano: undefined }))}>Todos</Chip>
                {[2024, 2023].map(y => (
                  <Chip key={y} active={anoAtivo === y}
                    onClick={() => nav(url({ ano: anoAtivo === y ? undefined : String(y) }))}>
                    {y}
                  </Chip>
                ))}
              </div>
            </FilterGroup>

            <FilterGroup title="Dia">
              <div className="flex gap-1.5">
                <Chip active={!diaAtivo} onClick={() => nav(url({ dia: undefined }))}>Todos</Chip>
                <Chip active={diaAtivo === 'simu_dia1'} onClick={() => nav(url({ dia: diaAtivo === 'simu_dia1' ? undefined : 'simu_dia1' }))}>1º Dia</Chip>
                <Chip active={diaAtivo === 'simu_dia2'} onClick={() => nav(url({ dia: diaAtivo === 'simu_dia2' ? undefined : 'simu_dia2' }))}>2º Dia</Chip>
              </div>
            </FilterGroup>
          </>
        )}

        {/* ── Filtros EXATO ── */}
        {isExato && (
          <>
            <FilterGroup title="Evento">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!eventoAtivo} onClick={() => nav(url({ evento: undefined }))}>Todos</Chip>
                {EVENTOS_EXATO.map(e => (
                  <Chip key={e} active={eventoAtivo === e}
                    onClick={() => nav(url({ evento: eventoAtivo === e ? undefined : e }))}
                    colorClass={eventoAtivo === e ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : ''}>
                    {EVENTO_LABEL[e] ?? e}
                  </Chip>
                ))}
              </div>
            </FilterGroup>

            <FilterGroup title="Turno">
              <div className="flex gap-1.5">
                <Chip active={!turnoAtivo} onClick={() => nav(url({ turno: undefined }))}>Todos</Chip>
                <Chip active={turnoAtivo === 'MANHA'} onClick={() => nav(url({ turno: turnoAtivo === 'MANHA' ? undefined : 'MANHA' }))}>Manhã</Chip>
                <Chip active={turnoAtivo === 'TARDE'} onClick={() => nav(url({ turno: turnoAtivo === 'TARDE' ? undefined : 'TARDE' }))}>Tarde</Chip>
              </div>
            </FilterGroup>

            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined }))}>Todas</Chip>
                {areas.map(a => {
                  const m = AREA_META[a]; const ativo = areaAtiva === a
                  return (
                    <Chip key={a} active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}>
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>
          </>
        )}

        {/* ── Filtros UFT ── */}
        {isUFT && (
          <>
            <FilterGroup title="Área">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!areaAtiva} onClick={() => nav(url({ area: undefined }))}>Todas</Chip>
                {areas.map(a => {
                  const m = AREA_META[a]; const ativo = areaAtiva === a
                  return (
                    <Chip key={a} active={ativo}
                      onClick={() => nav(url({ area: ativo ? undefined : a }))}
                      colorClass={ativo && m ? `${m.bg} ${m.text} ${m.border}` : ''}>
                      {m?.label ?? a}
                    </Chip>
                  )
                })}
              </div>
            </FilterGroup>

            <FilterGroup title="Ano">
              <div className="flex flex-wrap gap-1.5">
                <Chip active={!anoAtivo} onClick={() => nav(url({ ano: undefined }))}>Todos</Chip>
                {Array.from({length: 7}, (_, i) => 2024 - i).map(y => (
                  <Chip key={y} active={anoAtivo === y}
                    onClick={() => nav(url({ ano: anoAtivo === y ? undefined : String(y) }))}>
                    {y}
                  </Chip>
                ))}
              </div>
            </FilterGroup>

            <FilterGroup title="Turno">
              <div className="flex gap-1.5">
                <Chip active={!turnoAtivo} onClick={() => nav(url({ turno: undefined }))}>Todos</Chip>
                <Chip active={turnoAtivo === 'MANHA'} onClick={() => nav(url({ turno: turnoAtivo === 'MANHA' ? undefined : 'MANHA' }))}>Manhã</Chip>
                <Chip active={turnoAtivo === 'TARDE'} onClick={() => nav(url({ turno: turnoAtivo === 'TARDE' ? undefined : 'TARDE' }))}>Tarde</Chip>
              </div>
            </FilterGroup>

            <FilterGroup title="Edição">
              <div className="flex gap-1.5">
                <Chip active={!eventoAtivo} onClick={() => nav(url({ evento: undefined }))}>Todas</Chip>
                <Chip active={eventoAtivo === '1_EDICAO'} onClick={() => nav(url({ evento: eventoAtivo === '1_EDICAO' ? undefined : '1_EDICAO' }))}>1ª Edição</Chip>
                <Chip active={eventoAtivo === '2_EDICAO'} onClick={() => nav(url({ evento: eventoAtivo === '2_EDICAO' ? undefined : '2_EDICAO' }))}>2ª Edição</Chip>
              </div>
            </FilterGroup>
          </>
        )}
      </div>

      {hasFilter && (
        <Link href={`${pathname}?fonte=${fonteAtiva ?? 'ENEM'}`}
          className="block text-center text-[11px] text-[#635D56] hover:text-rose-400 transition py-1">
          ✕ Limpar filtros
        </Link>
      )}
    </div>
  )
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="p-3.5">
      <div className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#635D56] mb-2.5">{title}</div>
      {children}
    </div>
  )
}

function Chip({
  active, onClick, children, colorClass = '', small = false, title,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode
  colorClass?: string; small?: boolean; title?: string
}) {
  return (
    <button onClick={onClick} title={title}
      className={`${small ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-[11px]'} rounded-md font-medium transition border ${
        active
          ? (colorClass || 'bg-[#D4A853]/15 text-[#D4A853] border-[#D4A853]/30')
          : 'bg-[#1E1B17] text-[#9E9589] border-transparent hover:bg-[#2C2820] hover:text-[#F2EDE4]'
      }`}>
      {children}
    </button>
  )
}
```

- [ ] **Step 3: Verificar build**

```
cd frontend
npx tsc --noEmit
```

Esperado: sem erros de tipo.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/FiltroSidebar.tsx frontend/lib/provas.ts
git commit -m "feat: FiltroSidebar — remove tabs ENEM/EXATO, adiciona chips Fonte e Provedor"
```

---

## Task 8: Frontend — Atualizar `questoes/page.tsx`

**Files:**
- Modify: `frontend/app/questoes/page.tsx`

- [ ] **Step 1: Editar SearchParams e query**

Substituir o bloco de `interface SearchParams` e lógica de query. Abra `frontend/app/questoes/page.tsx` e faça as seguintes alterações:

**1a — Adicionar `provedor` em SearchParams** (linha ~8):
```typescript
interface SearchParams {
  ano?: string
  dia?: string
  area?: string
  competencia?: string
  busca?: string
  ia?: string
  pagina?: string
  fonte?: string
  evento?: string
  turno?: string
  tipo?: string
  provedor?: string   // ← ADD
}
```

**1b — Extrair `provedor` e remover hard-coded `isExato`** (linha ~43):
```typescript
  const fonte       = (params.fonte ?? 'ENEM') as string
  const isExato     = fonte === 'EXATO'
  const isUFT       = fonte === 'UFT'
  const isEnemSim   = fonte === 'ENEM' && tipo === 'SIMULADO'

  const ano         = params.ano ? parseInt(params.ano) : undefined
  const dia         = params.dia as string | undefined
  const area        = params.area
  const competencia = params.competencia
  const evento      = params.evento
  const turno       = params.turno
  const tipo        = params.tipo as 'PROVA' | 'SIMULADO' | undefined
  const provedor    = params.provedor  // ← ADD
```

**1c — Query: aceitar UFT e provedor** (linha ~74):
```typescript
  let query = supabase
    .from('questoes')
    .select('id, numero, ano, dia, area, competencia, enunciado, gabarito, tem_imagem, anulada, fonte, evento, turno, provedor', { count: 'exact' })
    .eq('anulada', false)
    .eq('fonte', fonte)

  // Ordenação
  if (isExato || isUFT) {
    query = query.order('ano', { ascending: false }).order('numero', { ascending: true })
  } else {
    query = query.order('ano', { ascending: false }).order('numero', { ascending: true })
  }

  query = query.range(offset, offset + POR_PAGINA - 1)

  // Filtros ENEM provas
  if (fonte === 'ENEM' && tipo !== 'SIMULADO') {
    if (ano)         query = query.eq('ano', ano)
    if (dia)         query = query.eq('dia', dia)
    if (competencia) query = query.eq('competencia', competencia)
  }

  // Filtros ENEM simulados
  if (fonte === 'ENEM' && tipo === 'SIMULADO') {
    if (provedor) query = query.eq('provedor', provedor)
    if (ano)      query = query.eq('ano', ano)
    if (dia)      query = query.eq('dia', dia)
    if (evento)   query = query.eq('evento', evento)
  }

  // Filtros EXATO
  if (isExato) {
    if (evento) query = query.eq('evento', evento)
    if (turno)  query = query.eq('turno', turno)
  }

  // Filtros UFT
  if (isUFT) {
    if (ano)    query = query.eq('ano', ano)
    if (turno)  query = query.eq('turno', turno)
    if (evento) query = query.eq('evento', evento)
  }

  // Filtro de área (todas as fontes)
  if (area) query = query.eq('area', area)

  // Filtro de tipo (PROVA | SIMULADO)
  if (tipo) query = query.eq('tipo', tipo)
```

**1d — Passar `provedorAtivo` para FiltroSidebar** (no JSX, linha ~154):
```typescript
          <FiltroSidebar
            anos={ANOS}
            areas={AREAS}
            anoAtivo={ano}
            diaAtivo={dia}
            areaAtiva={area}
            competenciaAtiva={competencia}
            fonteAtiva={fonte}
            eventoAtivo={evento}
            turnoAtivo={turno}
            tipoAtivo={tipo}
            provedorAtivo={provedor}
          />
```

**1e — Atualizar `paginaUrl`** (linha ~120):
```typescript
  function paginaUrl(p: number) {
    const sp = new URLSearchParams()
    sp.set('fonte', fonte)
    if (tipo)        sp.set('tipo', tipo)
    if (fonte === 'ENEM' && tipo !== 'SIMULADO') {
      if (ano)         sp.set('ano', String(ano))
      if (dia)         sp.set('dia', dia)
      if (competencia) sp.set('competencia', competencia)
    }
    if (fonte === 'ENEM' && tipo === 'SIMULADO') {
      if (provedor) sp.set('provedor', provedor)
      if (ano)      sp.set('ano', String(ano))
      if (dia)      sp.set('dia', dia)
      if (evento)   sp.set('evento', evento)
    }
    if (isExato) {
      if (evento) sp.set('evento', evento)
      if (turno)  sp.set('turno', turno)
    }
    if (isUFT) {
      if (ano)    sp.set('ano', String(ano))
      if (turno)  sp.set('turno', turno)
      if (evento) sp.set('evento', evento)
    }
    if (area)     sp.set('area', area)
    if (buscaRaw) sp.set('busca', buscaRaw)
    if (isIA)     sp.set('ia', '1')
    if (p > 1)    sp.set('pagina', String(p))
    return `/questoes?${sp}`
  }
```

**1f — Atualizar hidden inputs no form de busca manual** (linha ~194):
```typescript
              <input type="hidden" name="fonte" value={fonte} />
              {tipo && <input type="hidden" name="tipo" value={tipo} />}
              {fonte === 'ENEM' && tipo !== 'SIMULADO' && ano && <input type="hidden" name="ano" value={ano} />}
              {fonte === 'ENEM' && tipo !== 'SIMULADO' && dia && <input type="hidden" name="dia" value={dia} />}
              {fonte === 'ENEM' && tipo !== 'SIMULADO' && competencia && <input type="hidden" name="competencia" value={competencia} />}
              {fonte === 'ENEM' && tipo === 'SIMULADO' && provedor && <input type="hidden" name="provedor" value={provedor} />}
              {fonte === 'ENEM' && tipo === 'SIMULADO' && ano && <input type="hidden" name="ano" value={ano} />}
              {isExato && evento && <input type="hidden" name="evento" value={evento} />}
              {isExato && turno  && <input type="hidden" name="turno"  value={turno} />}
              {isUFT   && ano    && <input type="hidden" name="ano"    value={ano} />}
              {isUFT   && turno  && <input type="hidden" name="turno"  value={turno} />}
              {isUFT   && evento && <input type="hidden" name="evento" value={evento} />}
              {area && <input type="hidden" name="area" value={area} />}
```

- [ ] **Step 2: Verificar build**

```
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/questoes/page.tsx
git commit -m "feat: questoes/page.tsx — adiciona suporte a UFT, provedor e ENEM simulados"
```

---

## Task 9: Frontend — Atualizar `simulado/page.tsx`

**Files:**
- Modify: `frontend/app/simulado/page.tsx`
- Modify: `frontend/app/api/simulado/criar/route.ts`

- [ ] **Step 1: Adicionar estado e UI de Fonte em `simulado/page.tsx`**

Em `frontend/app/simulado/page.tsx`, adicionar estado `fonte` após os estados existentes:

```typescript
  const [fonte,       setFonte]     = useState<'ENEM' | 'EXATO' | 'UFT'>('ENEM')
```

E adicionar a seção de Fonte antes da seção "Tipo de questão" (após o return `<main ...>`):

```tsx
      {/* Fonte */}
      <div className="mb-6">
        <p className="text-[12px] font-bold uppercase tracking-wider text-[#635D56] mb-3">Fonte</p>
        <div className="grid grid-cols-3 gap-2">
          {([
            { value: 'ENEM',  label: 'ENEM',  desc: 'Provas e simulados ENEM' },
            { value: 'EXATO', label: 'EXATO', desc: 'Simulados e provas EXATO' },
            { value: 'UFT',   label: 'UFT',   desc: 'Vestibular UFT 2018–2024' },
          ] as const).map(({ value, label, desc }) => (
            <button
              key={value}
              onClick={() => setFonte(value)}
              className={`rounded-xl border p-3 text-left transition ${
                fonte === value
                  ? 'border-[#D4A853] bg-[#D4A853]/15 text-amber-200'
                  : 'border-[#2C2820] bg-[#161411] text-white/60 hover:border-[#D4A853]/40'
              }`}
            >
              <div className="text-sm font-bold mb-0.5">{label}</div>
              <div className="text-[11px] text-white/40">{desc}</div>
            </button>
          ))}
        </div>
      </div>
```

Adicionar `fonte` ao body do POST em `criar()`:

```typescript
        body: JSON.stringify({
          fonte,            // ← ADD
          area:       area || undefined,
          ano_inicio: anoInicio,
          ano_fim:    anoFim,
          quantidade,
          tipo:       tipo || undefined,
        }),
```

- [ ] **Step 2: Atualizar `api/simulado/criar/route.ts`**

```typescript
// Extrair fonte do body
const { fonte, area, ano_inicio, ano_fim, quantidade, tipo } = await request.json()

// Aplicar filtro de fonte (padrão ENEM)
const fonteQuery = fonte || 'ENEM'
query = query.eq('fonte', fonteQuery)
```

O filtro de ano deve ser condicional (UFT e EXATO_PROVAS têm ano, EXATO simulados não):

```typescript
if (fonteQuery !== 'EXATO' || tipo === 'PROVA') {
  if (ano_inicio) query = query.gte('ano', ano_inicio)
  if (ano_fim)    query = query.lte('ano', ano_fim)
}
```

- [ ] **Step 3: Ajustar ANOS no simulado/page.tsx para UFT**

Quando `fonte === 'UFT'`, o seletor de período deve mostrar 2018–2024:

```typescript
  const ANOS_DISPONIVEIS = fonte === 'UFT'
    ? Array.from({ length: 7 }, (_, i) => 2018 + i)
    : Array.from({ length: 16 }, (_, i) => 2009 + i)
```

E substituir `const ANOS = Array.from(...)` estático por `ANOS_DISPONIVEIS` nos selects de período.

- [ ] **Step 4: Verificar build e commit**

```
cd frontend && npx tsc --noEmit
git add frontend/app/simulado/page.tsx frontend/app/api/simulado/criar/route.ts
git commit -m "feat: simulado/page — adiciona filtro por fonte (ENEM/EXATO/UFT)"
```

---

## Task 10: CORRETOR — Atualizar `data_layer.py`

**Files:**
- Modify: `data_layer.py`

- [ ] **Step 1: Atualizar `listar_categorias`**

Substituir a função `listar_categorias` por:

```python
def listar_categorias() -> list[str]:
    """Retorna lista de fontes que têm questões: ['ENEM', 'EXATO', 'UFT', ...]"""
    fontes_conhecidas = ["ENEM", "EXATO", "UFT"]
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
```

- [ ] **Step 2: Atualizar `listar_filtros`**

Substituir `listar_filtros` para suportar UFT:

```python
def listar_filtros(categoria: str) -> dict:
    """
    ENEM  → {"anos": [...], "dias": ["dia1","dia2"]}
    EXATO → {"eventos": [...], "turnos": [...]}
    UFT   → {"anos": [...], "turnos": [...], "eventos": [...]}
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
    elif categoria == "UFT":
        anos    = sorted({d["ano"] for d in dados if d.get("ano")}, reverse=True)
        turnos  = sorted({d["turno"] for d in dados if d.get("turno")})
        eventos = sorted({d["evento"] for d in dados if d.get("evento")})
        return {"anos": anos, "turnos": turnos, "eventos": eventos}
    else:  # EXATO
        eventos = sorted({d["evento"] for d in dados if d.get("evento")})
        turnos  = sorted({d["turno"]  for d in dados if d.get("turno")})
        return {"eventos": eventos, "turnos": turnos}
```

- [ ] **Step 3: Atualizar `buscar_questoes`**

```python
def buscar_questoes(fonte: str, filtros: dict, tipo: str | None = None, provedor: str | None = None) -> list[dict]:
    """
    filtros para ENEM:  {"ano": 2023, "dia": "dia1"}
    filtros para EXATO: {"evento": "CICLO_ZERO", "turno": "MANHA"}
    filtros para UFT:   {"ano": 2022, "turno": "MANHA", "evento": "1_EDICAO"}
    """
    params: dict[str, Any] = {
        "select": "id,numero,area,competencia,tem_imagem,gabarito,anulada",
        "fonte": f"eq.{fonte}",
        "order": "numero.asc",
        "limit": 500,
    }
    if fonte == "ENEM":
        if filtros.get("ano"):
            params["ano"] = f"eq.{filtros['ano']}"
        if filtros.get("dia"):
            params["dia"] = f"eq.{filtros['dia']}"
    elif fonte == "UFT":
        if filtros.get("ano"):
            params["ano"] = f"eq.{filtros['ano']}"
        if filtros.get("turno"):
            params["turno"] = f"eq.{filtros['turno']}"
        if filtros.get("evento"):
            params["evento"] = f"eq.{filtros['evento']}"
    else:  # EXATO
        if filtros.get("evento"):
            params["evento"] = f"eq.{filtros['evento']}"
        if filtros.get("turno"):
            params["turno"] = f"eq.{filtros['turno']}"

    if tipo:
        params["tipo"] = f"eq.{tipo}"
    if provedor:
        params["provedor"] = f"eq.{provedor}"

    r = requests.get(_rest("questoes"), headers=_headers(), params=params, timeout=15)
    return r.json() if r.ok else []
```

- [ ] **Step 4: Commit**

```bash
git add data_layer.py
git commit -m "feat: data_layer — suporte a UFT e provedor em listar_categorias/filtros/buscar_questoes"
```

---

## Task 11: CORRETOR — Atualizar `ui_questoes.py`

**Files:**
- Modify: `ui_questoes.py`

- [ ] **Step 1: Expandir dropdown PROVA e adicionar PROVEDOR**

No método `_build_ui`, localizar o bloco do dropdown PROVA (linha ~590) e atualizar:

O `_cb_cat` já tem `width=8`. Mudar para `width=9` para caber "UFT":
```python
        self._cb_cat  = ttk.Combobox(hdr_inner, textvariable=self._var_cat,
                                     state="readonly", width=9,
                                     font=("Segoe UI", 9))
```

Após o separador do TIPO (linha ~636), adicionar o dropdown PROVEDOR:

```python
        # Separador + PROVEDOR (visível só para ENEM + SIMULADO)
        tk.Label(hdr_inner, text="│", bg=C.CARD, fg="#2C2820",
                 font=("Segoe UI", 14)).pack(side="left", padx=2)

        tk.Label(hdr_inner, text="PROVEDOR", bg=C.CARD, fg=C.FG2,
                 font=("Segoe UI", 8, "bold")).pack(side="left", padx=(4, 3))
        self._var_provedor = tk.StringVar(value="Todos")
        self._cb_provedor  = ttk.Combobox(hdr_inner, textvariable=self._var_provedor,
                                           state="readonly", width=12,
                                           font=("Segoe UI", 9))
        self._cb_provedor["values"] = ["Todos", "BERNOULLI", "SAS", "POLIEDRO", "FARIAS_BRITO", "SOMOS"]
        self._cb_provedor.pack(side="left", padx=(0, 6))
        self._cb_provedor.bind("<<ComboboxSelected>>", self._load_questoes)
```

- [ ] **Step 2: Atualizar `_ao_mudar_categoria` para suportar UFT**

Localizar o método `_ao_mudar_categoria` (linha ~977) e adicionar bloco UFT:

```python
    def _ao_mudar_categoria(self, _=None):
        cat = self._var_cat.get()
        self._cat_atual = cat
        filtros = dl.listar_filtros(cat)

        if cat == "ENEM":
            self._lbl_f1.config(text="Ano:")
            anos = [str(a) for a in filtros.get("anos", [])]
            self._cb_f1["values"] = anos
            if anos: self._var_f1.set(anos[0])
            self._lbl_f2.config(text="Dia:")
            dias = filtros.get("dias", ["dia1", "dia2"])
            self._cb_f2["values"] = dias
            if dias: self._var_f2.set(dias[0])
        elif cat == "UFT":
            self._lbl_f1.config(text="Ano:")
            anos = [str(a) for a in filtros.get("anos", [])]
            self._cb_f1["values"] = anos
            if anos: self._var_f1.set(anos[0])
            self._lbl_f2.config(text="Turno:")
            turnos = filtros.get("turnos", ["MANHA", "TARDE"])
            self._cb_f2["values"] = turnos
            if turnos: self._var_f2.set(turnos[0])
        else:  # EXATO
            self._lbl_f1.config(text="Evento:")
            eventos = filtros.get("eventos", [])
            self._cb_f1["values"] = eventos
            if eventos: self._var_f1.set(eventos[0])
            self._lbl_f2.config(text="Turno:")
            turnos = filtros.get("turnos", [])
            self._cb_f2["values"] = turnos
            if turnos: self._var_f2.set(turnos[0])

        self._load_questoes()
```

- [ ] **Step 3: Atualizar `_load_questoes` para passar provedor**

Localizar `_load_questoes` (linha ~1010):

```python
    def _load_questoes(self, _=None):
        cat = self._cat_atual
        f1  = self._var_f1.get()
        f2  = self._var_f2.get()

        if cat == "ENEM":
            try:
                filtros = {"ano": int(f1), "dia": f2}
            except ValueError:
                return
        elif cat == "UFT":
            try:
                filtros = {"ano": int(f1), "turno": f2}
            except ValueError:
                return
        else:  # EXATO
            filtros = {"evento": f1, "turno": f2}

        tipo_sel     = self._var_tipo.get()
        tipo         = None if tipo_sel == "Todos" else tipo_sel
        provedor_sel = self._var_provedor.get()
        provedor     = None if provedor_sel == "Todos" else provedor_sel

        self._lbl_sync.config(text="carregando…", fg=self.WARN)
        self.update_idletasks()

        self._questoes = dl.buscar_questoes(cat, filtros, tipo=tipo, provedor=provedor)
        self._q_idx = 0
        if self._questoes:
            self._lbl_sync.config(text=f"{len(self._questoes)} questões", fg=self.FG2)
            self._atualizar_questao()
        else:
            self._lbl_sync.config(text="sem dados", fg=self.DANGER)
            self._limpar_ui()
```

- [ ] **Step 4: Inicializar `_var_provedor` em `__init__`**

No método `__init__` (linha ~560), garantir que `_var_provedor` é declarado antes de `_build_ui`:

```python
        self._var_provedor = None  # inicializado em _build_ui
```

(O Combobox é criado em `_build_ui`, então `self._var_provedor` só existe depois. O `_load_questoes` pode ser chamado antes. Adicionar guard em `_load_questoes`:)

```python
        provedor_sel = self._var_provedor.get() if self._var_provedor else "Todos"
```

- [ ] **Step 5: Verificar que o CORRETOR inicia sem erros**

```
cd C:\PROJETOS\HENRYJR
python -c "import ui_questoes; print('ui_questoes: OK')"
```

Esperado: sem erros de importação.

- [ ] **Step 6: Commit + push**

```bash
git add ui_questoes.py
git commit -m "feat: ui_questoes — dropdown UFT e Provedor no CORRETOR"
git push origin main
```

---

## Task 12: Classificar competências H01–H30 das novas questões ENEM

**Files:**
- Uses: `classificar_competencias.py` (existente)

Este task é opcional mas recomendado — executar após o upload das questões ENEM simulados para preencher `competencia`.

- [ ] **Step 1: Verificar que GROQ_API_KEY está setado**

```
echo %GROQ_API_KEY%
```

Se vazio: `set GROQ_API_KEY=gsk_SEU_TOKEN_AQUI`

- [ ] **Step 2: Adaptar o script para questões ENEM_SIMULADOS**

O `classificar_competencias.py` atual lê JSONs de `dados/json_v2/` e usa `supabase_client`. Para as novas questões (já no Supabase), rodar a classificação diretamente via Supabase REST:

```
python classificar_competencias.py --fonte ENEM_SIM
```

**Atenção:** `classificar_competencias.py` atual não aceita `--fonte`. Isto requer ajuste manual no script ou rodar via query SQL direta no Supabase Dashboard:

```sql
-- Conta questões ENEM SIMULADO sem competencia
SELECT COUNT(*) FROM questoes
WHERE fonte = 'ENEM' AND tipo = 'SIMULADO' AND competencia IS NULL;
```

A classificação automática pode ser feita incrementalmente — não bloqueia o restante das tasks.

- [ ] **Step 3: Commit (apenas se o script foi modificado)**

```bash
git add classificar_competencias.py
git commit -m "feat: classificar_competencias — suporte a fonte ENEM_SIM"
```

---

## Self-Review

**Spec coverage check:**
- ✅ DB: coluna `provedor` (Task 1)
- ✅ lib_extrair.py (Task 2)
- ✅ extrair_uft.py (Task 3)
- ✅ extrair_exato_provas.py (Task 4)
- ✅ extrair_enem_simulados.py (Task 5)
- ✅ upload_novas_questoes.py (Task 6)
- ✅ FiltroSidebar — remove tabs, adiciona Fonte chips + Provedor chips (Task 7)
- ✅ questoes/page.tsx — provedor searchParam + UFT query (Task 8)
- ✅ simulado/page.tsx — filtro Fonte (Task 9)
- ✅ data_layer.py — UFT + provedor (Task 10)
- ✅ ui_questoes.py — CORRETOR expansão (Task 11)
- ✅ classificar competências H01-H30 (Task 12)
- ✅ Constraint UNIQUE: `dia='exato'` para UFT/EXATO_P, `dia='simu_dia1/2'` para ENEM simulados

**Placeholder scan:** Nenhum TBD encontrado. Task 12 tem instrução de adaptação manual, mas explica como fazer.

**Type consistency:**
- `provedor: str | None` — usado consistentemente em lib_extrair, data_layer, ui_questoes
- `normalizar_questao_banco()` — assinatura consistente entre Task 2 e Tasks 3/4/5
- `buscar_questoes(fonte, filtros, tipo, provedor)` — assinatura consistente entre Task 10 e Task 11
