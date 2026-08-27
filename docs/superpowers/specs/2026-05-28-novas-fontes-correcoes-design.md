# Novas Fontes + Correções de Extração — Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corrigir gaps de extração em UFT, EXATO Provas e PAES; adicionar suporte a UNICAMP, FUVEST e UNESP como novas fontes; atualizar plataforma frontend.

**Architecture:** Três arcos independentes e sequenciais: (A) correções nos extratores existentes, (B) novos extratores para três vestibulares, (C) atualização do upload script e do frontend. Cada arco produz questões prontas para o Supabase e para a plataforma.

**Tech Stack:** Python + PyMuPDF (extração texto), `lib_extrair.py` (parser base), `upload_novas_questoes.py` (Supabase), Next.js 14 + TypeScript (frontend).

---

## Contexto e Convenções

### Estrutura de pastas
```
DADOS/
├── UFT_PROVAS/          # 2018–2024 (sem 2020), 1ª/2ª edição
├── EXATO_PROVAS/        # 2024, 2025 1ª ed., 2025 2ª ed.
├── PAES_PROVAS/         # 2019–2025 (arquivos planos, não subpastas)
├── UNICAMP_PROVAS/      # 2015–2024, 2026 (subpastas por ano)
├── FUVEST_PROVAS/       # 2015–2026 (subpastas ano/1ª FASE e 2ª FASE)
├── UNESP_PROVAS/        # 2017–2025 (subpastas por ano/fase)
├── json_uft/            # output UFT
├── json_exato_provas/   # output EXATO provas
├── json_paes/           # output PAES
├── json_unicamp/        # output UNICAMP (criar)
├── json_fuvest/         # output FUVEST (criar)
└── json_unesp/          # output UNESP (criar)
```

### Convenções Supabase para fontes novas

| Campo | UNICAMP | FUVEST | UNESP |
|-------|---------|--------|-------|
| `fonte` | `'UNICAMP'` | `'FUVEST'` | `'UNESP'` |
| `tipo` | `'PROVA'` | `'PROVA'` | `'PROVA'` |
| `dia` | `'dia1'` | `'dia1'` | `'dia1'` |
| `ano` | 2015–2026 | 2015–2026 | 2017–2025 |
| `evento` | `null` | `null` | `null` / `'1_EDICAO'` / `'2_EDICAO'` |
| `area` | `null` | `null` | `null` |
| `competencia` | `null` | `null` | `null` |
| `provedor` | `null` | `null` | `null` |

### Quantidades esperadas

| Fonte | Edições | Questões/edição | Total estimado | Alternativas |
|-------|---------|-----------------|----------------|--------------|
| UNICAMP 1ª fase | 11 | 72 | ~792q | A–D (4) |
| FUVEST 1ª fase | 12 | 90 | ~1.080q | A–E (5) |
| UNESP 1ª fase | ~9 | 90 | ~810q | A–E (5) |

---

## Arco A — Correções nos Extratores Existentes

### A1: UFT — corrigir regex uppercase QUESTÃO

**Problema:** O PDF da UFT usa `QUESTÃO 01` (uppercase, com Ã Unicode U+00C3 U+00A3). O parser de texto em `lib_extrair.py` (`_parse_questoes_texto`) falha em detectá-lo, caindo para Gemini Vision que exaure o RPD e deixa gaps.

**Arquivos:** `extrair_uft.py` e/ou `lib_extrair.py`

**Fix:** No regex de detecção de marcadores de questão, normalizar o texto com `unicodedata.normalize('NFC', texto)` e usar `re.IGNORECASE` combinado com pattern `QUEST[ÃA]O\s*(\d+)`. Verificar também o pattern para `Questão` lowercase.

**Arquivos com gaps a re-extrair:**
- `uft_2018_manha` — faltando Q11–Q14
- `uft_2018_tarde` — faltando Q4–Q9
- `uft_2021_manha_1_EDICAO` — faltando Q4–Q7, Q17–Q22+
- `uft_2021_tarde_1_EDICAO` — faltando Q29–Q36
- `uft_2022_manha_1_EDICAO` e `_2_EDICAO` — ~8q cada
- `uft_2023_manha_1_EDICAO` — faltando Q9–Q11
- `uft_2023_tarde_2_EDICAO` — faltando Q10–Q15
- `uft_2024_tarde` — faltando Q18–Q20

**Após correção:** Re-extrair com `--pasta <ano>` para cada arquivo afetado. O `restaurar_uft_do_supabase.py` garante que só sobrescreve se Supabase tiver menos questões. Após re-extração, rodar `upload_novas_questoes.py --fonte UFT`.

### A2: EXATO Provas — adicionar leitura do GAB.pdf

**Problema:** O extrator `extrair_exato_provas.py` extrai enunciados e alternativas mas não lê o `GAB.pdf` disponível em cada pasta. Resultado: 0/222 questões têm gabarito.

**Adicionalmente:** `exato_prova_2024_tarde.json` falta Q22–Q27 (6q); `exato_prova_2025_manha_2_EDICAO.json` falta Q31–Q34 (4q).

**Fix:**
1. Após extração de enunciados, abrir o `GAB.pdf` da mesma pasta
2. Parsear o gabarito: buscar tabela ou lista com padrão `NN [A-E]` ou `QUESTÃO NN: [A-E]`
3. Mapear gabarito por número de questão no JSON
4. Fazer `PATCH` no Supabase para as 222q existentes (adicionar campo `gabarito`)
5. Re-extrair os dois arquivos com gaps e fazer upload das questões novas

### A3: PAES 2020–2023 — corrigir parser cross-page

**Problema:** Nas provas PAES 2020–2023, o marcador `Questão 01` aparece no final de uma página e o texto da questão está na página seguinte — sem repetir o número. O parser atual atribui esse texto à questão errada.

**Estatística dos gaps:**
- 2020: 35/59 sem enunciado (59%)
- 2021 dia1: 25/43 sem enunciado (58%)
- 2021 dia2: 24/43 sem enunciado (56%)
- 2022: 28/60 sem enunciado (47%)
- 2023: 33/60 sem enunciado (55%)

**Fix em `extrair_paes.py`:**
- Ao processar páginas, concatenar todo o texto em um único bloco antes de parsear
- Usar regex multi-linha que detecta `Questão N` como início de seção (não de página)
- Alternativamente: ao final de uma página, se a última questão detectada tiver enunciado vazio, carregar a próxima página como continuação

**Após correção:** Re-extrair `paes_2020_dia1`, `paes_2021_dia1`, `paes_2021_dia2`, `paes_2022_dia1`, `paes_2023_dia1`. Fazer upload apenas das questões cujo enunciado mudou (PATCH no Supabase).

---

## Arco B — Novos Extratores

### B1: extrair_unicamp.py

**Fonte:** `DADOS/UNICAMP_PROVAS/{ano}/` com arquivos `prova_*.pdf` e `gabarito_*.pdf` (nomes variados por ano).

**Estrutura da prova:**
- 72 questões por edição, 4 alternativas a)/b)/c)/d) (lowercase sem parêntese final)
- Marcador: `QUESTÃO N` no início de seção dentro da página
- Anos disponíveis: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026 (sem 2025)
- Alguns anos têm múltiplas versões de prova (S/X/Y/Z), pegar a primeira disponível

**Estrutura do gabarito:**
- Formato: `01\nA\n02\nB\n...` (pares número/letra em linhas alternadas)
- Alguns anos têm versão única (90 pares); outros têm 4 versões em colunas paralelas
- Para anos com versão única: mapear diretamente
- Para anos com múltiplas versões: identificar versão do PDF de prova (letra no nome do arquivo) e usar a coluna correspondente

**Output:** `DADOS/json_unicamp/unicamp_{ano}.json`

**Alternativas:** normalizar para A/B/C/D (uppercase). Campo `gabarito` aceita A/B/C/D.

**Identificação de pasta/arquivo:**
```python
def localizar_prova(ano_pasta: Path) -> tuple[Path | None, Path | None]:
    """Retorna (pdf_prova, pdf_gabarito) para um ano dado."""
    pdfs = [p for p in ano_pasta.glob('*.pdf') if 'Cópia de' not in p.name]
    prova = next((p for p in pdfs if 'gab' not in p.name.lower()), None)
    gab   = next((p for p in pdfs if 'gab' in p.name.lower()), None)
    return prova, gab
```

### B2: extrair_fuvest.py

**Fonte:** `DADOS/FUVEST_PROVAS/{ano}/1 FASE/` (ou `1ª FASE/`). Ignorar `2 FASE/` e `SIMULADO/`.

**Estrutura da prova:**
- 90 questões por edição, 5 alternativas (A)(B)(C)(D)(E)
- Marcador: número de dois dígitos isolado em linha própria: `\n04 \n` precedendo o texto
- Versão da prova: letra identificada na capa (V, K, Q, X, Z) e no nome do arquivo (`prova_V.pdf`)
- Anos disponíveis: 2015–2026 (excluir 2026 Simulado e 2027 Simulado — estes são simulados, não provas oficiais)

**Estrutura do gabarito (formato 2015):**
```
PROVA V    PROVA K    PROVA Q    PROVA X    PROVA Z
V 01- E    K 01- E    Q 01- C    X 01- E    Z 01- D
V 02- D    K 02- C    Q 02- A    X 02- C    Z 02- B
```
Regex: `([VKQXZ]) (\d{2})- ([A-E])` → filtrar pelo prefixo da versão da prova.

**Formato gabarito 2023+:**
```
1 \nE \n \n46 \nC \n
```
Estrutura tabular com 4 colunas (V1/V2/V3/V4). Identificar versão da prova pelo nome do PDF (`prova_V.pdf` → versão V → primeira coluna).

**Output:** `DADOS/json_fuvest/fuvest_{ano}.json`

**Lógica de identificação de versão:**
```python
def versao_da_prova(pdf_path: Path) -> str:
    """Extrai letra de versão do nome do arquivo ou da capa do PDF."""
    # Tenta pelo nome: fuvest2024_1fase_prova_V.pdf → 'V'
    m = re.search(r'_([VKQXYZ])\d?\.pdf$', pdf_path.name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Fallback: ler primeira página do PDF e procurar letra grande
    # (implementação com fitz)
    return 'V'  # default
```

### B3: extrair_unesp.py

**Fonte:** `DADOS/UNESP_PROVAS/{ano}/1ª FASE/`. Ignorar `2ª FASE/` e `REDAÇÃO/`.

**Estrutura da prova:**
- 90 questões por edição, 5 alternativas (A)(B)(C)(D)(E)
- Marcador: `Questão N` (mixed case)
- Anos/semestres: 2017, 2018, 2019, 2020, 2021, 2022 (Biológicas + Humanas/Exatas como versões), 2023, 2024.1, 2025.1, 2025.2
- Para anos com duas versões de prova (Biológicas / Humanas e Exatas): usar a versão "Humanas e Exatas" como padrão (ou ambas se tiverem questões diferentes — verificar)

**Evento para anos com múltiplos semestres:**
- Pasta `2024.1` → `ano=2024, evento='1_EDICAO'`
- Pasta `2025.1` → `ano=2025, evento='1_EDICAO'`
- Pasta `2025.2` → `ano=2025, evento='2_EDICAO'`

**Estrutura do gabarito:**
- Formato simples: `Questão 1: A` ou tabela com padrão `1\nA\n2\nB\n...`
- Verificar por ano (formato varia)

**Output:** `DADOS/json_unesp/unesp_{ano}[_{evento}].json`

---

## Arco C — Upload e Frontend

### C1: upload_novas_questoes.py — adicionar UNICAMP, FUVEST, UNESP

Adicionar ao dicionário `FONTES`:
```python
FONTES = {
    # ...existentes...
    "UNICAMP": BASE / "json_unicamp",
    "FUVEST":  BASE / "json_fuvest",
    "UNESP":   BASE / "json_unesp",
}
```

Adicionar aos choices do argparse: `choices=[..., "UNICAMP", "FUVEST", "UNESP"]`

O script já suporta os campos `evento`, `provedor`, `area` com lógica de `COALESCE` — não precisa de alteração na lógica de upload.

### C2: Frontend — lib/provas.ts

Adicionar objetos para as três novas fontes:
```typescript
{ fonte: 'FUVEST',   label: 'FUVEST',   tipo: 'PROVA', anos: [2015,2016,...,2026] },
{ fonte: 'UNICAMP',  label: 'UNICAMP',  tipo: 'PROVA', anos: [2015,2016,...,2024,2026] },
{ fonte: 'UNESP',    label: 'UNESP',    tipo: 'PROVA', anos: [2017,2018,...,2025] },
```

### C3: Frontend — FiltroSidebar.tsx

Adicionar chips `[FUVEST]`, `[UNICAMP]`, `[UNESP]` na seção de fontes.

Filtros condicionais para cada fonte:
- **FUVEST**: Ano
- **UNICAMP**: Ano
- **UNESP**: Ano + Edição (1ª/2ª, somente para anos com múltiplas edições)

### C4: Frontend — questoes/page.tsx e simulado/page.tsx

Replicar tratamento existente de `?fonte=UFT` para as três novas fontes. O simulado deve permitir selecionar FUVEST/UNICAMP/UNESP com filtro de ano.

### C5: CLAUDE.md

Atualizar com:
- Novas pastas em Estrutura de Pastas
- Totais de questões por fonte
- Novos scripts na lista de ferramentas locais
- Status e pendências

---

## Ordem de Execução

```
A1 (UFT fix) → re-extrair → upload
A2 (EXATO Provas gabarito) → re-extrair → upload
A3 (PAES fix) → re-extrair → upload
B1 (UNICAMP) → extrair → upload
B2 (FUVEST) → extrair → upload
B3 (UNESP) → extrair → upload
C1 (upload script) → C2+C3+C4 (frontend) → C5 (CLAUDE.md)
```

Os arcos A e B são independentes entre si (diferentes pastas/JSONs). O Arco C só começa após A e B estarem completos.

---

## Questões em Aberto / Decisões Tomadas

| Decisão | Escolha |
|---------|---------|
| Competência H01–H30 | ❌ Não classificar para nenhuma das novas fontes |
| Questões discursivas | ❌ Descartar — só 1ª fase objetiva |
| UNESP 2022 (Biológicas vs Humanas/Exatas) | Usar Humanas/Exatas como padrão |
| FUVEST versão | Identificar pelo nome do arquivo PDF → coluna correspondente no gabarito |
| `area` por questão | `null` — provas gerais sem estrutura de área por questão |
| UNICAMP 4 vs 5 alternativas | 4 alternativas (A–D) — não A–E |
