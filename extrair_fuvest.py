"""
extrair_fuvest.py — Extrai questões da 1ª fase da FUVEST (2015–2026).
Saída: DADOS/json_fuvest/fuvest_{ano}.json

90 questões por edição, 5 alternativas (A)(B)(C)(D)(E) ou A) B) ...
Marcador: número de 2 dígitos isolado em linha própria.
Gabarito: multi-versão — versão identificada pelo nome do arquivo de prova.

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
    """Localiza a subpasta '1 FASE' ou variantes dentro do diretório do ano."""
    for nome in ["1 FASE", "1ª FASE", "1a FASE", "1 ° FASE", "1° FASE",
                 "PRIMEIRA FASE", "PROVA - PRIMEIRA FASE",
                 "1 fase", "1ª fase"]:
        p = ano_dir / nome
        if p.exists() and p.is_dir():
            return p
    # Busca flexível
    for p in sorted(ano_dir.iterdir()):
        if p.is_dir() and re.search(r"(?:1\s*[ªa°]?\s*|primeira\s+|prova.*primeira\s+)fase", p.name, re.IGNORECASE):
            if "simulado" not in p.name.lower() and not p.name.startswith("2"):
                return p
    return None


def versao_do_arquivo(pdf_path: Path) -> str:
    """Extrai letra de versão do nome do arquivo. Ex: 'prova_V.pdf' → 'V'."""
    # Padrão: _V.pdf, _V1.pdf, fuvest2024V.pdf
    m = re.search(r'[_\s-]([VKQXYZ])\d*\.pdf$', pdf_path.name, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r'(\d{4})([VKQXYZ])\d*\.pdf$', pdf_path.name, re.IGNORECASE)
    if m:
        return m.group(2).upper()
    # Qualquer letra maiúscula isolada no nome
    m = re.search(r'\b([VKQXYZ])\b', pdf_path.stem, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return 'V'  # default


def localizar_prova_e_gabarito(fase_dir: Path) -> tuple[Path | None, Path | None, str]:
    """Retorna (pdf_prova, pdf_gabarito, versao_da_prova)."""
    pdfs = [
        p for p in fase_dir.glob("*.pdf")
        if "simulado" not in p.name.lower() and "Cópia de" not in p.name
    ]

    prova: Path | None = None
    gab:   Path | None = None

    for p in pdfs:
        nome_lower = p.name.lower()
        if "gab" in nome_lower or "gabarito" in nome_lower:
            gab = p
        elif prova is None:
            prova = p

    versao = versao_do_arquivo(prova) if prova else 'V'
    return prova, gab, versao


def parse_gabarito_fuvest(gab_path: Path, versao: str) -> dict[int, str]:
    """
    Extrai gabarito FUVEST filtrando pela versão da prova.

    Formato clássico (até ~2022):
        PROVA V    PROVA K    ...
        V 01- E    K 01- E    ...
        V 02- D    K 02- C    ...

    Formato tabular (2023+):
        1          (colunas V1/V2/V3/V4)
        E
           (V2)
        D
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

    resultado: dict[int, str] = {}

    # Formato clássico: "V 01- E" ou "V01-E"
    pat_classico = re.compile(
        r'\b' + re.escape(versao) + r'\s*(\d{1,2})\s*-\s*([A-E])\b',
        re.IGNORECASE
    )
    for m in pat_classico.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

    # Formato alternativo: "V 01- E" com espaço antes do número
    pat_alt = re.compile(
        r'\b' + re.escape(versao) + r'\s+(\d{2})-\s*([A-E])\b',
        re.IGNORECASE
    )
    for m in pat_alt.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

    # Formato tabular (2023+): tentar ler sequencialmente números e letras
    # O gabarito neste formato tem colunas paralelas V1/V2/V3/V4
    # Pegar a 1ª coluna completa (V / V1)
    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    num_atual = 0
    col_num = 0  # posição na coluna

    # Detectar cabeçalhos de versão para saber em qual coluna estamos
    # Simplificação: pegar apenas os primeiros 90 pares (número, letra) em sequência
    i = 0
    while i < len(linhas) and len(resultado) < 90:
        # Número isolado (1-90) — possivelmente início de questão
        m_num = re.match(r'^(\d{1,2})$', linhas[i])
        if m_num:
            num = int(m_num.group(1))
            if 1 <= num <= 90:
                # Procurar a letra correspondente nas próximas linhas
                for j in range(i + 1, min(i + 5, len(linhas))):
                    m_letra = re.match(r'^([A-E])$', linhas[j], re.IGNORECASE)
                    if m_letra:
                        if num not in resultado:  # pegar só a 1ª ocorrência (versão V)
                            resultado[num] = m_letra.group(1).upper()
                        break
        i += 1

    return resultado


def parse_questoes_fuvest(prova_path: Path) -> list[dict]:
    """
    Extrai questões da prova FUVEST 1ª fase.
    Marcador: número de 2 dígitos em linha própria (01-90).
    Alternativas: (A) texto, A) texto, A. texto
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
            if o <= off:
                p = pg
        return p

    # Marcador: \n(número de 2 dígitos)\n — isolado numa linha.
    # Formatos suportados: "01 " (2024), "{01}" (2025), "01" (padrão antigo)
    quest_re = re.compile(r'\n\{?(\d{2})\}? *\n')
    # Alternativas: (A), A), A.
    alt_re   = re.compile(r'^\(?([A-E])\)?(?:[.)]\s*|[ \t]+)(.+)', re.IGNORECASE)

    matches = [m for m in quest_re.finditer(texto_total) if 1 <= int(m.group(1)) <= 90]

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
            txt = " ".join(linhas_atual).strip()
            if txt:
                alternativas[letra_atual] = txt

        if len(alternativas) < 4:
            continue  # discursiva ou imagem — descartar

        # Enunciado
        first_alt = re.search(r'^\(?[A-E]\)?(?:[.)]\s*|[ \t])', bloco, re.MULTILINE | re.IGNORECASE)
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

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    anos = [args.ano] if args.ano else ANOS_FUVEST

    print(f"FUVEST — {len(anos)} anos a processar")
    total = 0
    for ano in anos:
        qs = processar_ano(ano)
        total += len(qs)
    print(f"\n✓ Total: {total} questões FUVEST → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
