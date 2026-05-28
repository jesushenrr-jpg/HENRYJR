# Arco B — Novos Extratores: UNICAMP, FUVEST, UNESP

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar três novos scripts de extração — `extrair_unicamp.py`, `extrair_fuvest.py`, `extrair_unesp.py` — e extrair ~2.700 questões de 1ª fase objetiva de UNICAMP, FUVEST e UNESP.

**Architecture:** Cada extrator segue o padrão já estabelecido: PyMuPDF para texto + gabarito, normalização para o schema Supabase, saída em JSON. Nenhum campo `competencia`, `area` ou `provedor` (são provas gerais). Upload via `upload_novas_questoes.py` (requer Arco C1 primeiro).

**Tech Stack:** Python + PyMuPDF (`fitz`), `lib_extrair.py`, regex, `upload_novas_questoes.py`.

---

## Contexto e Convenções

### Supabase para novas fontes

| Campo | UNICAMP | FUVEST | UNESP |
|-------|---------|--------|-------|
| `fonte` | `'UNICAMP'` | `'FUVEST'` | `'UNESP'` |
| `tipo` | `'PROVA'` | `'PROVA'` | `'PROVA'` |
| `dia` | `'dia1'` | `'dia1'` | `'dia1'` |
| `evento` | `None` | `None` | `None` / `'1_EDICAO'` / `'2_EDICAO'` |
| `area` | `None` | `None` | `None` |
| `competencia` | `None` | `None` | `None` |
| `provedor` | `None` | `None` | `None` |
| alternativas | A–D (4) | A–E (5) | A–E (5) |

### Saída

```
DADOS/json_unicamp/unicamp_{ano}.json
DADOS/json_fuvest/fuvest_{ano}.json
DADOS/json_unesp/unesp_{ano}.json           # sem evento
DADOS/json_unesp/unesp_{ano}_1_EDICAO.json # para 2024.1, 2025.1
DADOS/json_unesp/unesp_{ano}_2_EDICAO.json # para 2025.2
```

### Quantidades esperadas

| Fonte | Anos | Qs/edição | Total estimado |
|-------|------|-----------|----------------|
| UNICAMP | 11 (2015–2026 sem 2025) | 72 | ~792q |
| FUVEST | 12 (2015–2026) | 90 | ~1.080q |
| UNESP | ~9 edições (2017–2025) | 90 | ~810q |

---

## Task B1: Criar `extrair_unicamp.py`

**Fonte:** `DADOS/UNICAMP_PROVAS/{ano}/`

**Estrutura da prova:**
- 72 questões, alternativas `a)` `b)` `c)` `d)` (lowercase, sem parêntese final)
- Marcador: `QUESTÃO N` ou `Questão N` no texto
- Anos: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026

**Estrutura do gabarito:** linhas alternadas `01\nA\n02\nB\n...`

**Files:**
- Create: `extrair_unicamp.py`
- Create: `DADOS/json_unicamp/` (pasta — criada pelo script)

- [ ] **Step 1: Criar `extrair_unicamp.py`**

```python
"""
extrair_unicamp.py — Extrai questões da 1ª fase da UNICAMP.
Saída: DADOS/json_unicamp/unicamp_{ano}.json

Uso:
    python extrair_unicamp.py
    python extrair_unicamp.py --ano 2024
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "UNICAMP_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_unicamp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Anos disponíveis (sem 2025)
ANOS_UNICAMP = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026]


def localizar_pdfs(ano_pasta: Path) -> tuple[Path | None, Path | None]:
    """Retorna (pdf_prova, pdf_gabarito) ou (None, None)."""
    pdfs = [p for p in ano_pasta.glob("*.pdf") if "Cópia de" not in p.name and "copia" not in p.name.lower()]
    prova = next((p for p in pdfs if "gab" not in p.name.lower()), None)
    gab   = next((p for p in pdfs if "gab" in p.name.lower()),  None)
    return prova, gab


def parse_gabarito_unicamp(gab_path: Path) -> dict[int, str]:
    """
    Gabarito UNICAMP: linhas alternadas número/letra.
    Ex:
        01
        A
        02
        B
    Retorna {1: 'A', 2: 'B', ...}
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()

    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    resultado: dict[int, str] = {}

    i = 0
    while i < len(linhas) - 1:
        m_num = re.match(r"^(\d{1,2})$", linhas[i])
        if m_num:
            num = int(m_num.group(1))
            letra = linhas[i + 1].strip().upper()
            if 1 <= num <= 72 and re.match(r"^[A-D]$", letra):
                resultado[num] = letra
                i += 2
                continue
        i += 1

    # Fallback: formato tabular "01 A"
    if len(resultado) < 5:
        pat = re.compile(r"(\d{1,2})\s+([A-D])\b")
        resultado = {}
        for m in pat.finditer(texto):
            num = int(m.group(1))
            if 1 <= num <= 72:
                resultado[num] = m.group(2).upper()

    return resultado


def parse_questoes_unicamp(prova_path: Path) -> list[dict]:
    """
    Extrai questões da prova UNICAMP 1ª fase.
    Marcador: QUESTÃO N (maiúsculas) ou Questão N (mixed case).
    Alternativas: a) b) c) d) (lowercase, sem parêntese final).
    """
    doc = fitz.open(str(prova_path))
    # Concatenar todas as páginas
    paginas_texto: list[tuple[int, str]] = []
    for i in range(len(doc)):
        t = re.sub(r'[\x80-\x9f]', '', doc[i].get_text())
        paginas_texto.append((i, t))
    doc.close()

    texto_total = ""
    pag_offsets: list[tuple[int, int]] = []
    for pag, texto in paginas_texto:
        pag_offsets.append((len(texto_total), pag))
        texto_total += texto

    def pagina_de_offset(off: int) -> int:
        p = 0
        for o, pg in pag_offsets:
            if o <= off: p = pg
        return p

    quest_re = re.compile(r"QUEST[ÃA]O\s+(\d{1,2})\b", re.IGNORECASE)
    alt_re   = re.compile(r"^([a-d])\)\s*(.+)", re.IGNORECASE)

    matches = list(quest_re.finditer(texto_total))
    questoes: list[dict] = []

    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 72:
            continue
        inicio = m.start()
        fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto_total)
        bloco = texto_total[inicio + len(m.group()):fim]

        # Extrair alternativas a) b) c) d)
        alternativas: dict[str, str] = {}
        letra_atual: str | None = None
        linhas_atual: list[str] = []

        for linha in bloco.split("\n"):
            m_alt = alt_re.match(linha.strip())
            if m_alt:
                if letra_atual:
                    txt = " ".join(linhas_atual).strip()
                    if txt:
                        alternativas[letra_atual] = txt
                letra_atual = m_alt.group(1).upper()
                linhas_atual = [m_alt.group(2).strip()]
            elif letra_atual:
                l = linha.strip()
                if l:
                    linhas_atual.append(l)

        if letra_atual and linhas_atual:
            txt = " ".join(linhas_atual).strip()
            if txt:
                alternativas[letra_atual] = txt

        if len(alternativas) < 3:
            continue  # questão discursiva ou imagem — descartar

        # Enunciado: linhas antes da primeira alternativa
        first_alt_pos = re.search(r"^[a-d]\)", bloco, re.MULTILINE)
        enunciado_raw = bloco[:first_alt_pos.start()] if first_alt_pos else ""
        paragrafos = [l.strip() for l in enunciado_raw.split("\n") if l.strip()]

        questoes.append({
            "numero":       num,
            "enunciado":    paragrafos,
            "alternativas": alternativas,
            "pagina_pdf":   pagina_de_offset(inicio),
        })

    # Desduplicar: manter o bloco com mais alternativas
    vistos: dict[int, dict] = {}
    for q in questoes:
        n = q["numero"]
        if n not in vistos or len(q["alternativas"]) > len(vistos[n]["alternativas"]):
            vistos[n] = q

    return sorted(vistos.values(), key=lambda q: q["numero"])


def montar_banco(q: dict, ano: int, gabarito_map: dict) -> dict:
    num = q["numero"]
    gabarito = gabarito_map.get(num)
    return {
        "fonte":        "UNICAMP",
        "tipo":         "PROVA",
        "ano":          ano,
        "dia":          "dia1",
        "numero":       num,
        "area":         None,
        "evento":       None,
        "turno":        None,
        "provedor":     None,
        "competencia":  None,
        "enunciado":    q["enunciado"],
        "alternativas": q["alternativas"],
        "gabarito":     gabarito,
        "confianca":    1.0,
        "revisado":     False,
        "anulada":      False,
        "tem_imagem":   False,
        "pagina_pdf":   q["pagina_pdf"],
    }


def processar_ano(ano: int) -> list[dict]:
    pasta = INPUT_DIR / str(ano)
    if not pasta.exists():
        # Tentar nomes alternativos (ex: "2026 - 1ª edição")
        candidatos = [p for p in INPUT_DIR.iterdir() if p.is_dir() and str(ano) in p.name]
        if not candidatos:
            print(f"  ⚠ Pasta {ano} não encontrada")
            return []
        pasta = candidatos[0]

    prova_pdf, gab_pdf = localizar_pdfs(pasta)
    if not prova_pdf:
        print(f"  ⚠ PDF de prova não encontrado em {pasta.name}")
        return []

    print(f"\n  [{ano}] {pasta.name}")
    print(f"  Prova: {prova_pdf.name}")
    questoes = parse_questoes_unicamp(prova_pdf)
    print(f"    {len(questoes)} questões extraídas")

    gabarito_map: dict[int, str] = {}
    if gab_pdf:
        print(f"  Gabarito: {gab_pdf.name}")
        gabarito_map = parse_gabarito_unicamp(gab_pdf)
        print(f"    {len(gabarito_map)} entradas de gabarito")
    else:
        print(f"  ⚠ Gabarito não encontrado")

    registros = [montar_banco(q, ano, gabarito_map) for q in questoes]

    saida = OUTPUT_DIR / f"unicamp_{ano}.json"
    saida.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    n_gab = sum(1 for r in registros if r["gabarito"])
    print(f"    → {len(registros)}q | {n_gab} com gabarito | {saida.name}")
    return registros


def main():
    parser = argparse.ArgumentParser(description="Extrai questões UNICAMP 1ª fase")
    parser.add_argument("--ano", type=int, help="Processar só este ano")
    args = parser.parse_args()

    anos = [args.ano] if args.ano else ANOS_UNICAMP

    print(f"UNICAMP — {len(anos)} anos a processar")
    total = 0
    for ano in anos:
        qs = processar_ano(ano)
        total += len(qs)
    print(f"\n✓ Total: {total} questões UNICAMP → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar que as pastas de prova existem**

```python
import pathlib
base = pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\UNICAMP_PROVAS")
for p in sorted(base.iterdir()):
    if p.is_dir():
        pdfs = list(p.glob("*.pdf"))
        print(f"{p.name}: {[f.name for f in pdfs]}")
```

Ajustar `ANOS_UNICAMP` se algum ano não tiver pasta.

- [ ] **Step 3: Testar com um ano**

```powershell
python extrair_unicamp.py --ano 2024
```

Esperado: `~72q | ~72 com gabarito | unicamp_2024.json`

- [ ] **Step 4: Rodar todos os anos**

```powershell
python extrair_unicamp.py
```

Esperado: ~792 questões totais (11 anos × 72q ≈ 792).

- [ ] **Step 5: Commit**

```
git add extrair_unicamp.py DADOS/json_unicamp/
git commit -m "feat: add extrair_unicamp.py — extract ~792 UNICAMP 1st-phase questions"
```

---

## Task B2: Criar `extrair_fuvest.py`

**Fonte:** `DADOS/FUVEST_PROVAS/{ano}/1 FASE/` ou `1ª FASE/`

**Estrutura da prova:**
- 90 questões, alternativas `(A)(B)(C)(D)(E)`
- Marcador: número de 2 dígitos em linha isolada (ex: `\n04\n`)
- Versão: letra no nome do arquivo (`prova_V.pdf` → versão `V`)

**Estrutura do gabarito (até 2022):**
```
PROVA V    PROVA K    PROVA Q    PROVA X    PROVA Z
V 01- E    K 01- E    Q 01- C    X 01- E    Z 01- D
```

**Estrutura do gabarito (2023+):**
```
1
E
  
46
C
```
Tabular com colunas V1/V2/V3/V4.

**Files:**
- Create: `extrair_fuvest.py`
- Create: `DADOS/json_fuvest/` (pelo script)

- [ ] **Step 1: Criar `extrair_fuvest.py`**

```python
"""
extrair_fuvest.py — Extrai questões da 1ª fase da FUVEST (2015–2026).
Saída: DADOS/json_fuvest/fuvest_{ano}.json

Uso:
    python extrair_fuvest.py
    python extrair_fuvest.py --ano 2024
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "FUVEST_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_fuvest"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ANOS_FUVEST = list(range(2015, 2027))  # 2015–2026


def localizar_pasta_1fase(ano_dir: Path) -> Path | None:
    """Localiza a subpasta '1 FASE' ou '1ª FASE' dentro do diretório do ano."""
    for nome in ["1 FASE", "1ª FASE", "1a FASE", "PRIMEIRA FASE", "1 fase", "1ª fase"]:
        p = ano_dir / nome
        if p.exists() and p.is_dir():
            return p
    # Busca flexível
    for p in ano_dir.iterdir():
        if p.is_dir() and re.search(r"1[ª a]?\s*fase", p.name, re.IGNORECASE):
            if "simulado" not in p.name.lower() and "2" not in p.name[:2]:
                return p
    return None


def versao_do_arquivo(pdf_path: Path) -> str:
    """Extrai letra de versão do nome do arquivo. Ex: 'prova_V.pdf' → 'V'."""
    m = re.search(r'[_\s-]([VKQXYZ])\d?\.pdf$', pdf_path.name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Tenta letra isolada no nome: "fuvest2024V.pdf"
    m = re.search(r'(\d{4})([VKQXYZ])\.pdf$', pdf_path.name, re.IGNORECASE)
    if m:
        return m.group(2).upper()
    return 'V'  # default


def localizar_prova_e_gabarito(fase_dir: Path) -> tuple[Path | None, Path | None, str]:
    """
    Retorna (pdf_prova, pdf_gabarito, versao).
    Ignora PDFs que sejam simulados.
    """
    pdfs = [p for p in fase_dir.glob("*.pdf")
            if "simulado" not in p.name.lower() and "Cópia de" not in p.name]

    prova = None
    gab   = None
    for p in pdfs:
        nome_lower = p.name.lower()
        if "gab" in nome_lower or "gabarito" in nome_lower:
            gab = p
        else:
            prova = p

    if not prova and not gab:
        # Qualquer PDF não-gabarito
        prova = next((p for p in pdfs), None)

    versao = versao_do_arquivo(prova) if prova else 'V'
    return prova, gab, versao


def parse_gabarito_fuvest(gab_path: Path, versao: str) -> dict[int, str]:
    """
    Extrai gabarito FUVEST filtrando pela versão da prova.

    Formato até 2022:
        PROVA V    PROVA K ...
        V 01- E    K 01- E ...

    Formato 2023+:
        1       (coluna V1)
        E
           (coluna V2)
        D
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

    resultado: dict[int, str] = {}

    # Formato clássico: "V 01- E"
    pat_classico = re.compile(
        r'\b' + re.escape(versao) + r'\s+(\d{1,2})-\s*([A-E])\b',
        re.IGNORECASE
    )
    for m in pat_classico.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

    # Formato tabular (2023+): colunas V1/V2/V3/V4
    # Detectar cabeçalhos de coluna
    versoes_ordem = ['V', 'K', 'Q', 'X', 'Z', 'V1', 'V2', 'V3', 'V4']
    col_re = re.compile(r'\b(V1|V2|V3|V4|[VKQXYZ])\b')
    cabecalhos = [(m.start(), m.group(1)) for m in col_re.finditer(texto)]

    if cabecalhos:
        # Encontrar índice da coluna da nossa versão
        nossas_versoes = [v for _, v in cabecalhos if v.upper() in (versao, f'V{versoes_ordem.index(versao)+1}' if versao in versoes_ordem else versao)]
        if nossas_versoes:
            # Usar abordagem simples: dividir texto em blocos por coluna e pegar a nossa
            # Para formato tabular simples (número na linha anterior, letra na linha seguinte)
            linhas = [l.strip() for l in texto.split('\n') if l.strip()]
            # Tentar ler todas as letras em sequência numérica
            num_atual = 0
            for i, linha in enumerate(linhas):
                if re.match(r'^\d{1,2}$', linha):
                    num = int(linha)
                    if 1 <= num <= 90 and num > num_atual:
                        # Próxima linha não vazia deve ser a letra
                        for j in range(i + 1, min(i + 4, len(linhas))):
                            if re.match(r'^[A-E]$', linhas[j], re.IGNORECASE):
                                resultado[num] = linhas[j].upper()
                                num_atual = num
                                break

    return resultado


def parse_questoes_fuvest(prova_path: Path) -> list[dict]:
    """
    Extrai questões da prova FUVEST 1ª fase.
    Marcador: número de 2 dígitos isolado em linha própria.
    Alternativas: (A) texto, (B) texto, ... ou A) texto
    """
    doc = fitz.open(str(prova_path))
    paginas_texto: list[tuple[int, str]] = []
    for i in range(len(doc)):
        t = re.sub(r'[\x80-\x9f]', '', doc[i].get_text())
        paginas_texto.append((i, t))
    doc.close()

    texto_total = ""
    pag_offsets: list[tuple[int, int]] = []
    for pag, texto in paginas_texto:
        pag_offsets.append((len(texto_total), pag))
        texto_total += texto

    def pagina_de_offset(off: int) -> int:
        p = 0
        for o, pg in pag_offsets:
            if o <= off: p = pg
        return p

    # Marcador: linha com apenas 2 dígitos (01 a 90), precedida e seguida de \n
    # Usamos finditer no texto concatenado
    quest_re = re.compile(r'\n(\d{2})\n', re.MULTILINE)
    # Alternativas: (A), A), A.
    alt_re = re.compile(r'^\(?([A-E])\)?\s+(.+)', re.IGNORECASE)

    matches = list(quest_re.finditer(texto_total))
    # Filtrar apenas números 01-90
    matches = [m for m in matches if 1 <= int(m.group(1)) <= 90]

    questoes: list[dict] = []
    for idx, m in enumerate(matches):
        num = int(m.group(1))
        inicio = m.start()
        fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto_total)
        bloco = texto_total[m.end():fim]

        # Extrair alternativas
        alternativas: dict[str, str] = {}
        letra_atual: str | None = None
        linhas_atual: list[str] = []

        for linha in bloco.split("\n"):
            m_alt = alt_re.match(linha.strip())
            if m_alt:
                if letra_atual:
                    txt = " ".join(linhas_atual).strip()
                    if txt:
                        alternativas[letra_atual] = txt
                letra_atual = m_alt.group(1).upper()
                linhas_atual = [m_alt.group(2).strip()]
            elif letra_atual:
                l = linha.strip()
                if l:
                    linhas_atual.append(l)

        if letra_atual and linhas_atual:
            alternativas[letra_atual] = " ".join(linhas_atual).strip()

        if len(alternativas) < 4:
            continue  # discursiva ou imagem — descartar

        # Enunciado
        first_alt_pos = re.search(r'^\(?[A-E]\)', bloco, re.MULTILINE | re.IGNORECASE)
        enunciado_raw = bloco[:first_alt_pos.start()] if first_alt_pos else ""
        paragrafos = [l.strip() for l in enunciado_raw.split("\n") if l.strip()]

        questoes.append({
            "numero":       num,
            "enunciado":    paragrafos,
            "alternativas": alternativas,
            "pagina_pdf":   pagina_de_offset(inicio),
        })

    # Desduplicar
    vistos: dict[int, dict] = {}
    for q in questoes:
        n = q["numero"]
        if n not in vistos or len(q["alternativas"]) > len(vistos[n]["alternativas"]):
            vistos[n] = q

    return sorted(vistos.values(), key=lambda q: q["numero"])


def montar_banco(q: dict, ano: int, gabarito_map: dict) -> dict:
    num = q["numero"]
    return {
        "fonte":        "FUVEST",
        "tipo":         "PROVA",
        "ano":          ano,
        "dia":          "dia1",
        "numero":       num,
        "area":         None,
        "evento":       None,
        "turno":        None,
        "provedor":     None,
        "competencia":  None,
        "enunciado":    q["enunciado"],
        "alternativas": q["alternativas"],
        "gabarito":     gabarito_map.get(num),
        "confianca":    1.0,
        "revisado":     False,
        "anulada":      False,
        "tem_imagem":   False,
        "pagina_pdf":   q["pagina_pdf"],
    }


def processar_ano(ano: int) -> list[dict]:
    ano_dir = INPUT_DIR / str(ano)
    if not ano_dir.exists():
        candidatos = [p for p in INPUT_DIR.iterdir() if p.is_dir() and str(ano) in p.name]
        if not candidatos:
            print(f"  ⚠ Pasta {ano} não encontrada")
            return []
        ano_dir = candidatos[0]

    fase_dir = localizar_pasta_1fase(ano_dir)
    if not fase_dir:
        print(f"  ⚠ Pasta '1 FASE' não encontrada em {ano_dir.name}")
        return []

    prova_pdf, gab_pdf, versao = localizar_prova_e_gabarito(fase_dir)
    if not prova_pdf:
        print(f"  ⚠ PDF de prova não encontrado em {fase_dir}")
        return []

    print(f"\n  [{ano}] versão={versao} | {prova_pdf.name}")
    questoes = parse_questoes_fuvest(prova_pdf)
    print(f"    {len(questoes)} questões extraídas")

    gabarito_map: dict[int, str] = {}
    if gab_pdf:
        gabarito_map = parse_gabarito_fuvest(gab_pdf, versao)
        print(f"    {len(gabarito_map)} gabaritos (versão {versao})")
    else:
        print(f"  ⚠ Gabarito não encontrado")

    registros = [montar_banco(q, ano, gabarito_map) for q in questoes]
    saida = OUTPUT_DIR / f"fuvest_{ano}.json"
    saida.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    n_gab = sum(1 for r in registros if r["gabarito"])
    print(f"    → {len(registros)}q | {n_gab} com gabarito | {saida.name}")
    return registros


def main():
    parser = argparse.ArgumentParser(description="Extrai questões FUVEST 1ª fase")
    parser.add_argument("--ano", type=int, help="Processar só este ano")
    args = parser.parse_args()

    anos = [args.ano] if args.ano else ANOS_FUVEST

    print(f"FUVEST — {len(anos)} anos a processar")
    total = 0
    for ano in anos:
        qs = processar_ano(ano)
        total += len(qs)
    print(f"\n✓ Total: {total} questões FUVEST → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar estrutura de pastas FUVEST**

```python
import pathlib
base = pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\FUVEST_PROVAS")
for ano_dir in sorted(base.iterdir()):
    if not ano_dir.is_dir(): continue
    print(f"\n{ano_dir.name}:")
    for sub in sorted(ano_dir.iterdir()):
        if sub.is_dir():
            print(f"  {sub.name}/")
            for f in sub.glob("*.pdf"):
                print(f"    {f.name}")
```

Ajustar `ANOS_FUVEST` e `localizar_pasta_1fase` se necessário.

- [ ] **Step 3: Testar com 2024**

```powershell
python extrair_fuvest.py --ano 2024
```

Esperado: `~90q | ~90 com gabarito | fuvest_2024.json`

- [ ] **Step 4: Rodar todos os anos**

```powershell
python extrair_fuvest.py
```

Esperado: ~1.080 questões totais.

- [ ] **Step 5: Commit**

```
git add extrair_fuvest.py DADOS/json_fuvest/
git commit -m "feat: add extrair_fuvest.py — extract ~1080 FUVEST 1st-phase questions"
```

---

## Task B3: Criar `extrair_unesp.py`

**Fonte:** `DADOS/UNESP_PROVAS/{ano}/1ª FASE/` ou `1 FASE/`

**Estrutura:**
- 90 questões, alternativas `(A)(B)(C)(D)(E)` ou `A) B) ...`
- Marcador: `Questão N` (mixed case)
- Anos com múltiplos semestres: `2024.1`, `2025.1`, `2025.2`

**Files:**
- Create: `extrair_unesp.py`
- Create: `DADOS/json_unesp/` (pelo script)

- [ ] **Step 1: Criar `extrair_unesp.py`**

```python
"""
extrair_unesp.py — Extrai questões da 1ª fase da UNESP (2017–2025).
Saída: DADOS/json_unesp/unesp_{ano}[_{evento}].json

Uso:
    python extrair_unesp.py
    python extrair_unesp.py --pasta "2024.1"
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "UNESP_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_unesp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_pasta_unesp(nome: str) -> tuple[int, str | None]:
    """
    '2017'   → (2017, None)
    '2024.1' → (2024, '1_EDICAO')
    '2025.1' → (2025, '1_EDICAO')
    '2025.2' → (2025, '2_EDICAO')
    """
    m_semestre = re.match(r'(\d{4})\.(\d)', nome)
    if m_semestre:
        ano = int(m_semestre.group(1))
        sem = m_semestre.group(2)
        return ano, f"{sem}_EDICAO"
    m_ano = re.match(r'(\d{4})', nome)
    if m_ano:
        return int(m_ano.group(1)), None
    return 0, None


def localizar_pasta_1fase(ano_dir: Path) -> Path | None:
    """Localiza a subpasta de 1ª fase dentro do diretório do ano."""
    for nome in ["1ª FASE", "1 FASE", "1a FASE", "1ª fase", "1 fase"]:
        p = ano_dir / nome
        if p.exists() and p.is_dir():
            return p
    for p in ano_dir.iterdir():
        if p.is_dir() and re.search(r"1[ª a]?\s*fase", p.name, re.IGNORECASE):
            if "2" not in p.name[:2]:
                return p
    return None


def localizar_pdfs_unesp(fase_dir: Path) -> tuple[Path | None, Path | None]:
    """
    Retorna (pdf_prova, pdf_gabarito).
    Para anos com versão 'Humanas e Exatas' vs 'Biológicas': prefere 'Humanas'.
    """
    pdfs = list(fase_dir.glob("*.pdf"))

    gab = next((p for p in pdfs if "gab" in p.name.lower()), None)
    provas = [p for p in pdfs if "gab" not in p.name.lower()]

    if not provas:
        return None, gab

    # Preferência: "Humanas" ou "Exatas" (vs "Biológicas")
    prova_humanas = next((p for p in provas if re.search(r'human|exata', p.name, re.IGNORECASE)), None)
    prova = prova_humanas or provas[0]

    return prova, gab


def parse_gabarito_unesp(gab_path: Path) -> dict[int, str]:
    """
    Extrai gabarito UNESP. Suporta múltiplos formatos:
    - 'Questão 1: A'
    - Linhas alternadas '01\\nA'
    - Tabular '01 A'
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

    resultado: dict[int, str] = {}

    # Formato "Questão 1: A" ou "Questão 1 - A"
    pat1 = re.compile(r'Quest[ãa]o\s+(\d{1,2})[:\s-]+([A-E])\b', re.IGNORECASE)
    for m in pat1.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

    # Formato tabular "01 A"
    pat2 = re.compile(r'(\d{1,2})\s+([A-E])\b')
    for m in pat2.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

    # Linhas alternadas
    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    i = 0
    while i < len(linhas) - 1:
        m_num = re.match(r'^(\d{1,2})$', linhas[i])
        if m_num:
            num = int(m_num.group(1))
            letra = linhas[i + 1].strip().upper()
            if 1 <= num <= 90 and re.match(r'^[A-E]$', letra):
                resultado[num] = letra
                i += 2
                continue
        i += 1

    return resultado


def parse_questoes_unesp(prova_path: Path) -> list[dict]:
    """
    Extrai questões da prova UNESP 1ª fase.
    Marcador: 'Questão N' (mixed case).
    """
    doc = fitz.open(str(prova_path))
    paginas_texto: list[tuple[int, str]] = []
    for i in range(len(doc)):
        t = re.sub(r'[\x80-\x9f]', '', doc[i].get_text())
        paginas_texto.append((i, t))
    doc.close()

    texto_total = ""
    pag_offsets: list[tuple[int, int]] = []
    for pag, texto in paginas_texto:
        pag_offsets.append((len(texto_total), pag))
        texto_total += texto

    def pagina_de_offset(off: int) -> int:
        p = 0
        for o, pg in pag_offsets:
            if o <= off: p = pg
        return p

    quest_re = re.compile(r'Quest[ãa]o\s+(\d{1,2})\b', re.IGNORECASE)
    alt_re   = re.compile(r'^\(?([A-E])\)?\s+(.+)', re.IGNORECASE)

    matches = list(quest_re.finditer(texto_total))
    questoes: list[dict] = []

    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 90:
            continue
        inicio = m.start()
        fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto_total)
        bloco = texto_total[m.end():fim]

        # Alternativas
        alternativas: dict[str, str] = {}
        letra_atual: str | None = None
        linhas_atual: list[str] = []

        for linha in bloco.split("\n"):
            m_alt = alt_re.match(linha.strip())
            if m_alt:
                if letra_atual:
                    txt = " ".join(linhas_atual).strip()
                    if txt:
                        alternativas[letra_atual] = txt
                letra_atual = m_alt.group(1).upper()
                linhas_atual = [m_alt.group(2).strip()]
            elif letra_atual:
                l = linha.strip()
                if l:
                    linhas_atual.append(l)

        if letra_atual and linhas_atual:
            alternativas[letra_atual] = " ".join(linhas_atual).strip()

        if len(alternativas) < 4:
            continue  # discursiva — descartar

        first_alt = re.search(r'^\(?[A-E]\)?', bloco, re.MULTILINE | re.IGNORECASE)
        enunciado_raw = bloco[:first_alt.start()] if first_alt else ""
        paragrafos = [l.strip() for l in enunciado_raw.split("\n") if l.strip()]

        questoes.append({
            "numero":       num,
            "enunciado":    paragrafos,
            "alternativas": alternativas,
            "pagina_pdf":   pagina_de_offset(inicio),
        })

    # Desduplicar
    vistos: dict[int, dict] = {}
    for q in questoes:
        n = q["numero"]
        if n not in vistos or len(q["alternativas"]) > len(vistos[n]["alternativas"]):
            vistos[n] = q

    return sorted(vistos.values(), key=lambda q: q["numero"])


def montar_banco(q: dict, ano: int, evento: str | None, gabarito_map: dict) -> dict:
    num = q["numero"]
    return {
        "fonte":        "UNESP",
        "tipo":         "PROVA",
        "ano":          ano,
        "dia":          "dia1",
        "numero":       num,
        "area":         None,
        "evento":       evento,
        "turno":        None,
        "provedor":     None,
        "competencia":  None,
        "enunciado":    q["enunciado"],
        "alternativas": q["alternativas"],
        "gabarito":     gabarito_map.get(num),
        "confianca":    1.0,
        "revisado":     False,
        "anulada":      False,
        "tem_imagem":   False,
        "pagina_pdf":   q["pagina_pdf"],
    }


def processar_pasta(pasta: Path) -> list[dict]:
    ano, evento = parse_pasta_unesp(pasta.name)
    if not ano:
        print(f"  ⚠ Não foi possível detectar ano em: {pasta.name}")
        return []

    fase_dir = localizar_pasta_1fase(pasta)
    if not fase_dir:
        print(f"  ⚠ Subpasta '1ª FASE' não encontrada em {pasta.name}")
        return []

    prova_pdf, gab_pdf = localizar_pdfs_unesp(fase_dir)
    if not prova_pdf:
        print(f"  ⚠ PDF de prova não encontrado em {fase_dir}")
        return []

    print(f"\n  [{pasta.name}] evento={evento}")
    print(f"  Prova: {prova_pdf.name}")
    questoes = parse_questoes_unesp(prova_pdf)
    print(f"    {len(questoes)} questões extraídas")

    gabarito_map: dict[int, str] = {}
    if gab_pdf:
        gabarito_map = parse_gabarito_unesp(gab_pdf)
        print(f"    {len(gabarito_map)} gabaritos")
    else:
        print(f"  ⚠ Gabarito não encontrado")

    registros = [montar_banco(q, ano, evento, gabarito_map) for q in questoes]

    sufixo = f"_{evento}" if evento else ""
    saida = OUTPUT_DIR / f"unesp_{ano}{sufixo}.json"
    saida.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    n_gab = sum(1 for r in registros if r["gabarito"])
    print(f"    → {len(registros)}q | {n_gab} com gabarito | {saida.name}")
    return registros


def main():
    parser = argparse.ArgumentParser(description="Extrai questões UNESP 1ª fase")
    parser.add_argument("--pasta", help="Processar só esta pasta (ex: '2024.1')")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    pastas = sorted(INPUT_DIR.iterdir())
    if args.pasta:
        pastas = [p for p in pastas if args.pasta in p.name]
    pastas = [p for p in pastas if p.is_dir()]

    print(f"UNESP — {len(pastas)} pastas a processar")
    total = 0
    for pasta in pastas:
        qs = processar_pasta(pasta)
        total += len(qs)
    print(f"\n✓ Total: {total} questões UNESP → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar estrutura de pastas UNESP**

```python
import pathlib
base = pathlib.Path(r"C:\PROJETOS\HENRYJR\DADOS\UNESP_PROVAS")
for pasta in sorted(base.iterdir()):
    if not pasta.is_dir(): continue
    print(f"\n{pasta.name}:")
    for sub in sorted(pasta.iterdir()):
        if sub.is_dir():
            print(f"  {sub.name}/")
            for f in sub.glob("*.pdf"):
                print(f"    {f.name}")
```

- [ ] **Step 3: Testar com uma pasta recente**

```powershell
python extrair_unesp.py --pasta "2024"
```

Esperado: `~90q | ~90 com gabarito | unesp_2024.json`

- [ ] **Step 4: Rodar todas as pastas**

```powershell
python extrair_unesp.py
```

Esperado: ~810 questões totais (9 edições × 90q ≈ 810).

- [ ] **Step 5: Commit**

```
git add extrair_unesp.py DADOS/json_unesp/
git commit -m "feat: add extrair_unesp.py — extract ~810 UNESP 1st-phase questions"
```

---

## Task B4: Upload UNICAMP, FUVEST e UNESP

⚠️ **Pré-requisito:** Arco C — Task C1 (`upload_novas_questoes.py` atualizado com as três novas fontes) deve estar concluído antes desta task.

- [ ] **Step 1: Upload UNICAMP**

```powershell
python upload_novas_questoes.py --fonte UNICAMP
```

Esperado: ~792 inseridas | 0 erros.

- [ ] **Step 2: Upload FUVEST**

```powershell
python upload_novas_questoes.py --fonte FUVEST
```

Esperado: ~1.080 inseridas | 0 erros.

- [ ] **Step 3: Upload UNESP**

```powershell
python upload_novas_questoes.py --fonte UNESP
```

Esperado: ~810 inseridas | 0 erros.

- [ ] **Step 4: Commit final de Arco B**

```
git add .
git commit -m "feat: upload UNICAMP, FUVEST, UNESP to Supabase (~2700 questions)"
```

---

## Checklist de Conclusão do Arco B

- [ ] `extrair_unicamp.py` criado e extraindo ≥700 questões
- [ ] `extrair_fuvest.py` criado e extraindo ≥900 questões
- [ ] `extrair_unesp.py` criado e extraindo ≥700 questões
- [ ] Todos os JSONs salvos em `DADOS/json_unicamp/`, `DADOS/json_fuvest/`, `DADOS/json_unesp/`
- [ ] Upload UNICAMP/FUVEST/UNESP concluído (Task B4, após C1)
