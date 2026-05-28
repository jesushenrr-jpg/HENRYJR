# Arco A — Correções nos Extratores: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir gaps de extração em UFT (C1 control chars), EXATO Provas (leitura de gabarito) e PAES (re-extração com código já corrigido).

**Architecture:** Três correções independentes em Python + re-extração dos JSONs afetados + upsert com merge no Supabase para atualizar registros existentes.

**Tech Stack:** Python + PyMuPDF (fitz), `lib_extrair.py`, `extrair_uft.py`, `extrair_exato_provas.py`, `extrair_paes.py`, `upload_novas_questoes.py`, Supabase PostgREST.

---

## Contexto

- `DADOS/json_uft/` — JSONs locais com questões extraídas (local é autoritativo para re-extração)
- `DADOS/json_exato_provas/` — 222q, 0/222 com gabarito
- `DADOS/json_paes/` — questões PAES, 41-59% sem enunciado em 2020–2023
- Supabase: UNIQUE index 6-col `(fonte, ano, dia, numero, evento, provedor)` — impede inserção de duplicatas; para atualizar registros existentes precisa de `resolution=merge-duplicates`

---

## Task A0: Adicionar flag `--merge` em `upload_novas_questoes.py`

**Files:**
- Modify: `upload_novas_questoes.py`

- [ ] **Step 1: Ler o arquivo atual**

Confirmar linha que define `HDR` (atualmente linha ~38):
```python
HDR = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates,return=minimal",
}
```

- [ ] **Step 2: Mover `Prefer` para ser dinâmico**

Substituir o bloco `HDR` e `main()` de forma que o `Prefer` seja definido após parsear `--merge`:

```python
# ─── Header base (sem Prefer — definido em main() após parsear --merge) ───
HDR_BASE = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
}
HDR = {**HDR_BASE}  # será atualizado em main()
```

No início de `main()`, antes de qualquer uso de `HDR`:

```python
parser.add_argument("--merge", action="store_true",
                    help="Atualiza campos de questões existentes (merge-duplicates)")
# ...dentro de main() após args = parser.parse_args():
HDR["Prefer"] = (
    "resolution=merge-duplicates,return=minimal"
    if args.merge
    else "resolution=ignore-duplicates,return=minimal"
)
```

- [ ] **Step 3: Verificar que o script ainda funciona no dry-run**

```
python upload_novas_questoes.py --dry-run --fonte PAES
```

Esperado: lista questões sem erros de importação.

- [ ] **Step 4: Commit parcial**

```
git add upload_novas_questoes.py
git commit -m "feat: add --merge flag to upload_novas_questoes for upsert updates"
```

---

## Task A1: Corrigir C1 control chars — UFT

**Problema:** PDFs UFT codificam `QUESTÃO` com caractere C1 (U+0083) intercalado em `Ã O`, fazendo o regex `Q_RE = re.compile(r"(?:QUESTÃO|Questão)\s+(\d+)")` falhar. O parser cai para Vision, exaure o RPD e deixa gaps.

**Files:**
- Modify: `lib_extrair.py` — `extrair_texto_pagina()` (linha 80)

- [ ] **Step 1: Adicionar limpeza de C1 em `extrair_texto_pagina`**

```python
# lib_extrair.py — linha 80
def extrair_texto_pagina(doc: fitz.Document, page_num: int) -> str:
    """Extrai texto de uma página específica. Remove C1 control chars (U+0080–U+009F)
    que fontes customizadas (ex.: UFT) intercalam em caracteres Unicode compostos."""
    texto = doc[page_num].get_text()
    # Remove C1 control characters (U+0080–U+009F) — causa de false-negative no regex Q_RE para UFT
    return re.sub(r'[\x80-\x9f]', '', texto)
```

- [ ] **Step 2: Verificar que o regex Q_RE agora detecta QUESTÃO em texto UFT**

```python
# Teste manual rápido (rodar no terminal Python):
import re
texto = "QUESTÃ\x83O 01\nTexto da questão aqui"
texto_limpo = re.sub(r'[\x80-\x9f]', '', texto)
print(re.search(r"(?:QUESTÃO|Questão)\s+(\d+)", texto_limpo, re.IGNORECASE))
# Esperado: <re.Match object ... match='QUESTÃO 01' ...>
```

- [ ] **Step 3: Re-extrair arquivos UFT com gaps**

Configurar API key antes:
```powershell
$env:GROQ_API_KEY = "GROQ_API_KEY_REDACTED"
$env:GEMINI_API_KEY = "AIzaSyCct5xBRPpFdvCX5BGCTuGnHgBGwPqaLBE"
```

Re-extrair em sequência (cada `--pasta` processa MANHÃ + TARDE daquela edição):
```powershell
python extrair_uft.py --pasta "2018"
python extrair_uft.py --pasta "2021 - 1"
python extrair_uft.py --pasta "2022 - 1"
python extrair_uft.py --pasta "2022 - 2"
python extrair_uft.py --pasta "2023 - 1"
python extrair_uft.py --pasta "2023 - 2"
python extrair_uft.py --pasta "2024"
```

Esperado por arquivo: questão count >= quantidade anterior no JSON local.

Arquivos a verificar após extração (mínimos esperados):

| Arquivo | Mínimo esperado |
|---------|----------------|
| `uft_2018_manha.json` | 40q |
| `uft_2018_tarde.json` | 36q |
| `uft_2021_manha_1_EDICAO.json` | 36q |
| `uft_2021_tarde_1_EDICAO.json` | 36q |
| `uft_2022_manha_1_EDICAO.json` | 36q |
| `uft_2022_manha_2_EDICAO.json` | 36q |
| `uft_2023_manha_1_EDICAO.json` | 36q |
| `uft_2023_tarde_2_EDICAO.json` | 36q |
| `uft_2024_tarde.json` | 36q |

Verificar rapidamente:
```python
import json, pathlib
for f in sorted(pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\json_uft").glob("*.json")):
    n = len(json.loads(f.read_text(encoding="utf-8")))
    print(f"{f.name}: {n}q")
```

- [ ] **Step 4: Upload UFT com merge**

```powershell
python upload_novas_questoes.py --fonte UFT --merge
```

Esperado: `X inseridas | 0 erros` onde X inclui as questões novas + updates das existentes.

- [ ] **Step 5: Commit**

```
git add lib_extrair.py DADOS/json_uft/
git commit -m "fix: strip C1 control chars in extrair_texto_pagina — resolve UFT extraction gaps"
```

---

## Task A2: EXATO Provas — corrigir leitura do gabarito

**Problema:** `extrair_exato_provas.py` chama `parse_gabarito(gab_pdf)` mas a função retorna `{}`. Causa provável: o `GAB.pdf` do EXATO Provas tem MANHÃ e TARDE na mesma página com Q1–Q36 para cada turno — os padrões atuais misturam ou a Vision só lê a página 0.

**Files:**
- Modify: `extrair_exato_provas.py`

- [ ] **Step 1: Diagnosticar o GAB.pdf**

Rodar este snippet para ver o texto bruto:

```python
import fitz, pathlib
for pasta in sorted(pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\EXATO_PROVAS").iterdir()):
    if not pasta.is_dir(): continue
    for nome in ["GAB.pdf", "GAB PROVISÓRIO.pdf", "GAB PROVISORIO.pdf"]:
        gab = pasta / nome
        if gab.exists():
            doc = fitz.open(str(gab))
            for i in range(len(doc)):
                t = doc[i].get_text()
                print(f"=== {pasta.name} / {nome} / pag {i} ===")
                print(t[:600])
            doc.close()
            break
```

Esperado: ver o formato real (tabela `01 A 01 B`, ou `MANHÃ / TARDE` em seções, ou `Questão 1: A`).

- [ ] **Step 2: Adicionar parser específico para o formato encontrado**

Se o GAB.pdf tiver **MANHÃ e TARDE em colunas ou seções separadas**, adicionar em `extrair_exato_provas.py`:

```python
import fitz

def parse_gabarito_exato_provas(gab_pdf: Path) -> tuple[dict, dict]:
    """
    Extrai gabaritos MANHÃ e TARDE do GAB.pdf de uma pasta EXATO Provas.
    Retorna (gab_manha, gab_tarde) — cada um é {numero: letra_ou_None}.
    
    Formatos suportados:
    - Duas colunas: "MANHÃ" e "TARDE" como cabeçalhos de coluna
    - Duas seções: bloco com "MANHA" seguido de "TARDE" no mesmo texto
    - Formato tabular: "01 A  01 B" (manha, tarde na mesma linha)
    """
    doc = fitz.open(str(gab_pdf))
    # Ler todas as páginas
    paginas = [doc[i].get_text() for i in range(len(doc))]
    doc.close()
    
    texto_total = "\n".join(paginas)
    texto_total = re.sub(r'[\x80-\x9f]', '', texto_total)
    
    # Tentar detectar seções MANHA / TARDE
    manha_re = re.compile(r'manh[ãa]', re.IGNORECASE)
    tarde_re  = re.compile(r'tarde',   re.IGNORECASE)
    
    manha_pos = [m.start() for m in manha_re.finditer(texto_total)]
    tarde_pos  = [m.start() for m in tarde_re.finditer(texto_total)]
    
    par = re.compile(r'(\d{1,2})\s+([A-E])\b')
    
    if manha_pos and tarde_pos:
        # Separar texto por seção
        # Usar a primeira ocorrência de cada como delimitador
        m0, t0 = manha_pos[0], tarde_pos[0]
        if m0 < t0:
            bloco_manha = texto_total[m0:t0]
            bloco_tarde  = texto_total[t0:]
        else:
            bloco_tarde  = texto_total[t0:m0]
            bloco_manha  = texto_total[m0:]
        
        gab_manha = {int(m.group(1)): m.group(2).upper() for m in par.finditer(bloco_manha) if 1 <= int(m.group(1)) <= 60}
        gab_tarde  = {int(m.group(1)): m.group(2).upper() for m in par.finditer(bloco_tarde)  if 1 <= int(m.group(1)) <= 60}
        
        if len(gab_manha) >= 5 and len(gab_tarde) >= 5:
            return gab_manha, gab_tarde
    
    # Fallback: tentar parser genérico — retorna o mesmo para ambos os turnos
    # (situação de GAB único para prova de turno único)
    gab_generico = {int(m.group(1)): m.group(2).upper() for m in par.finditer(texto_total) if 1 <= int(m.group(1)) <= 60}
    return gab_generico, gab_generico
```

- [ ] **Step 3: Integrar `parse_gabarito_exato_provas` em `processar_pasta`**

Substituir o trecho que lê o gabarito em `processar_pasta`:

```python
# Antes:
gabarito_map = parse_gabarito(gab_pdf) if gab_pdf else {}

# Depois:
gab_manha, gab_tarde = parse_gabarito_exato_provas(gab_pdf) if gab_pdf else ({}, {})
# No loop de turno, usar o mapa correto:
gabarito_map = gab_manha if turno_val == "MANHA" else gab_tarde
```

O `import parse_gabarito` pode ser mantido (usado em outros extratores) ou removido do import de `extrair_exato_provas.py`.

- [ ] **Step 4: Re-extrair todas as pastas EXATO Provas**

```powershell
$env:GEMINI_API_KEY = "AIzaSyCct5xBRPpFdvCX5BGCTuGnHgBGwPqaLBE"
python extrair_exato_provas.py
```

Verificar contagem de gabaritos nos JSONs:
```python
import json, pathlib
for f in sorted(pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\json_exato_provas").glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    com_gab = sum(1 for q in data if q.get("gabarito"))
    print(f"{f.name}: {len(data)}q, {com_gab} com gabarito")
```

Esperado: a maioria das questões agora tem gabarito.

- [ ] **Step 5: Upload EXATO Provas com merge**

```powershell
python upload_novas_questoes.py --fonte EXATO_P --merge
```

Esperado: 222+ questões atualizadas, sem erros.

- [ ] **Step 6: Commit**

```
git add extrair_exato_provas.py DADOS/json_exato_provas/
git commit -m "fix: add per-turno gabarito parsing for EXATO Provas — 222q now have gabarito"
```

---

## Task A3: Re-extrair PAES 2020–2023

**Contexto:** O `extrair_paes.py` atual já concatena todas as páginas via `texto_total` antes de buscar marcadores `Questão NN`. Isso resolve o bug de cross-page. Os JSONs em disco foram gerados por uma versão anterior — precisam de re-extração.

**Files:**
- Run: `extrair_paes.py` para anos 2020–2023
- Run: `upload_novas_questoes.py --fonte PAES --merge`

- [ ] **Step 1: Confirmar que o código atual já concatena páginas**

Verificar linha ~190 de `extrair_paes.py`:
```python
texto_total = ""
for pag, texto in blocos:
    texto_total += texto
```
Deve estar presente. Se não, adicionar antes de `quest_re.finditer`.

- [ ] **Step 2: Re-extrair anos com maior gap**

```powershell
python extrair_paes.py --ano 2020
python extrair_paes.py --ano 2021
python extrair_paes.py --ano 2022
python extrair_paes.py --ano 2023
```

Verificar contagem por arquivo:
```python
import json, pathlib
for f in sorted(pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\json_paes").glob("*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    com_enunciado = sum(1 for q in data if q.get("enunciado"))
    print(f"{f.name}: {len(data)}q, {com_enunciado} com enunciado")
```

Esperado (após correção):
- `paes_2020_dia1.json`: ~59q, ≥45 com enunciado (melhora de 24 → ~59)
- `paes_2021_dia1.json`: ~43q, ≥35 com enunciado
- `paes_2021_dia2.json`: ~43q, ≥35 com enunciado
- `paes_2022_dia1.json`: ~60q, ≥45 com enunciado
- `paes_2023_dia1.json`: ~60q, ≥45 com enunciado

- [ ] **Step 3: Upload PAES com merge**

```powershell
python upload_novas_questoes.py --fonte PAES --merge
```

Esperado: questões PAES 2020–2023 com enunciados preenchidos no Supabase.

- [ ] **Step 4: Commit**

```
git add DADOS/json_paes/
git commit -m "fix: re-extract PAES 2020-2023 — recover ~145 missing enunciados via full-text concatenation"
```

---

## Checklist de Conclusão do Arco A

- [ ] `lib_extrair.py`: C1 control chars removidos em `extrair_texto_pagina`
- [ ] UFT: todos os 9 arquivos com gaps re-extraídos com contagem >= mínimo esperado
- [ ] UFT: upload com `--merge` concluído
- [ ] EXATO Provas: `parse_gabarito_exato_provas` adicionado e funcionando
- [ ] EXATO Provas: 222q têm gabarito no Supabase
- [ ] PAES 2020–2023: JSONs re-extraídos com enunciados recuperados
- [ ] PAES: upload com `--merge` concluído
