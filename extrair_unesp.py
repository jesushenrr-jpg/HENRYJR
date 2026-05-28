"""
extrair_unesp.py — Extrai questões da 1ª fase da UNESP (2017–2025).
Saída: DADOS/json_unesp/unesp_{ano}[_{evento}].json

90 questões por edição, 5 alternativas (A)(B)(C)(D)(E) ou A)/B)/...
Marcador: "Questão N" (mixed case).
Anos com múltiplos semestres: pasta "2024.1" → evento='1_EDICAO'.

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
        return int(m_semestre.group(1)), f"{m_semestre.group(2)}_EDICAO"
    m_ano = re.match(r'(\d{4})', nome)
    if m_ano:
        return int(m_ano.group(1)), None
    return 0, None


def localizar_pasta_1fase(ano_dir: Path) -> Path | None:
    """Localiza a subpasta de 1ª fase dentro do diretório do ano."""
    for nome in ["1ª FASE", "1 FASE", "1a FASE", "1° FASE", "PRIMEIRA FASE",
                 "1ª fase", "1 fase", "1° fase", "primeira fase"]:
        p = ano_dir / nome
        if p.exists() and p.is_dir():
            return p
    # Busca flexível
    for p in sorted(ano_dir.iterdir()):
        if p.is_dir() and re.search(r"(?:1[ªa°]?\s*|primeira\s+)fase", p.name, re.IGNORECASE):
            if not p.name.startswith("2"):
                return p
    # Fallback: se o próprio diretório tiver PDFs (ex: 2024.2 Inverno sem subpasta)
    if list(ano_dir.glob("*.pdf")):
        return ano_dir
    return None


def localizar_pdfs_unesp(fase_dir: Path) -> tuple[Path | None, Path | None]:
    """
    Retorna (pdf_prova, pdf_gabarito).
    Para anos com versão 'Humanas e Exatas' vs 'Biológicas': prefere 'Humanas'.
    Busca recursiva quando PDFs estão em subpastas (ex: 2022 tem Área Humanas e Exatas/).
    """
    # Tenta PDFs diretos primeiro; se não houver, busca recursivamente
    pdfs = list(fase_dir.glob("*.pdf"))
    if not pdfs:
        pdfs = list(fase_dir.glob("**/*.pdf"))

    gab = next((p for p in pdfs if "gab" in p.name.lower()), None)
    provas = [p for p in pdfs if "gab" not in p.name.lower()]

    if not provas:
        return None, gab

    # Preferência: "Humanas" ou "Exatas" (vs "Biológicas")
    prova_humanas = next(
        (p for p in provas if re.search(r'human|exata', p.name, re.IGNORECASE)),
        None
    )
    prova = prova_humanas or provas[0]
    return prova, gab


def parse_gabarito_unesp(gab_path: Path) -> dict[int, str]:
    """
    Extrai gabarito UNESP. Suporta múltiplos formatos:
    - Padrão principal: '1  -  D' ou '1 - D' (com espaços variáveis)
    - 'Questão 1: A' ou 'Questão 1 - A'
    - Tabular '01 A'
    - Linhas alternadas '01\\nA'
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

    resultado: dict[int, str] = {}

    # Formato principal UNESP: "1  -  D" ou "1 - D"
    pat_dash = re.compile(r'^(\d{1,2})\s*-\s*([A-E])\b', re.MULTILINE | re.IGNORECASE)
    for m in pat_dash.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 90:
            resultado[num] = m.group(2).upper()

    if len(resultado) >= 5:
        return resultado

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

    # Linhas alternadas "01\nA"
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
    Alternativas: (A) ou A) — 5 opções A-E.
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
            if o <= off:
                p = pg
        return p

    quest_re = re.compile(r'Quest[ãa]o\s+(\d{1,2})\b', re.IGNORECASE)
    alt_re   = re.compile(r'^\(?([A-E])\)?(?:[.)]\s*|[ \t]+)(.+)', re.IGNORECASE)

    matches = list(quest_re.finditer(texto_total))
    questoes: list[dict] = []

    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 90:
            continue
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
            continue  # discursiva ou sem alternativas extraíveis — descartar

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


def coletar_pastas(input_dir: Path) -> list[Path]:
    """
    Retorna lista de pastas processáveis, expandindo edições internas.
    Ex.: UNESP_PROVAS/2024/ contém 2024.1/ e 2024.2/ → retorna ambas.
    Ex.: UNESP_PROVAS/2017/ é processada diretamente.
    """
    resultado: list[Path] = []
    for p in sorted(input_dir.iterdir()):
        if not p.is_dir():
            continue
        ano, _ = parse_pasta_unesp(p.name)
        if not ano:
            continue
        # Verificar se tem subpastas de edição (ex: 2024.1/, 2025.2 (Inverno)/)
        edicoes = [
            sub for sub in sorted(p.iterdir())
            if sub.is_dir() and re.match(r'\d{4}\.\d', sub.name)
        ]
        if edicoes:
            resultado.extend(edicoes)
        else:
            resultado.append(p)
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Extrai questões UNESP 1ª fase")
    parser.add_argument("--pasta", help="Processar só esta pasta (ex: '2024.1')")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    pastas = coletar_pastas(INPUT_DIR)
    if args.pasta:
        pastas = [p for p in pastas if args.pasta in p.name]

    if not pastas:
        print("Nenhuma pasta encontrada.")
        sys.exit(1)

    print(f"UNESP — {len(pastas)} pastas a processar")
    total = 0
    for pasta in pastas:
        qs = processar_pasta(pasta)
        total += len(qs)
    print(f"\n✓ Total: {total} questões UNESP → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
