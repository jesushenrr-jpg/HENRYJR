"""
extrair_unicamp.py — Extrai questões da 1ª fase da UNICAMP.
Saída: DADOS/json_unicamp/unicamp_{ano}.json

72 questões por edição, 4 alternativas a)/b)/c)/d) (lowercase).
Marcador: QUESTÃO N (com ou sem acento).
Gabarito: linhas alternadas "01\nA\n02\nB\n..." ou tabular "01 A".

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
    """Retorna (pdf_prova, pdf_gabarito) — ignora cópias."""
    pdfs = [
        p for p in ano_pasta.glob("*.pdf")
        if "Cópia de" not in p.name and "copia" not in p.name.lower()
    ]
    prova = next((p for p in pdfs if "gab" not in p.name.lower()), None)
    gab   = next((p for p in pdfs if "gab" in p.name.lower()), None)
    return prova, gab


def parse_gabarito_unicamp(gab_path: Path) -> dict[int, str]:
    """
    Gabarito UNICAMP: linhas alternadas número/letra.
    Exemplo:
        01      → 1: 'A'
        A
        02      → 2: 'B'
        B
    Fallback: tabular "01 A  02 B".
    """
    doc = fitz.open(str(gab_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

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

    # Fallback: tabular "01 A"
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
    Marcador: QUESTÃO N (maiúsculas, com ou sem acento).
    Alternativas: a) b) c) d) (lowercase, parêntese à direita).
    """
    doc = fitz.open(str(prova_path))

    # Concatenar todas as páginas (questões podem cruzar páginas)
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

    # Marcador QUESTÃO: maiúsculas, aceita Ã correto ou garbled (\xc3)
    quest_re = re.compile(r"QUEST.O\s+(\d{1,2})\b", re.IGNORECASE)
    # Alternativas: a) b) c) d) — UNICAMP usa lowercase com parêntese direito
    alt_re   = re.compile(r"^([a-d])\)\s*(.+)", re.IGNORECASE)

    matches = list(quest_re.finditer(texto_total))
    questoes: list[dict] = []

    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 72:
            continue
        inicio = m.start()
        fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto_total)
        bloco = texto_total[m.end():fim]

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
        first_alt_pos = re.search(r"^[a-d]\)", bloco, re.MULTILINE | re.IGNORECASE)
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
    # Tentar pasta com nome exato ou contendo o ano
    pasta = INPUT_DIR / str(ano)
    if not pasta.exists():
        candidatos = [p for p in INPUT_DIR.iterdir() if p.is_dir() and str(ano) in p.name]
        if not candidatos:
            print(f"  ⚠ Pasta {ano} não encontrada em {INPUT_DIR}")
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

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    anos = [args.ano] if args.ano else ANOS_UNICAMP

    print(f"UNICAMP — {len(anos)} anos a processar")
    total = 0
    for ano in anos:
        qs = processar_ano(ano)
        total += len(qs)
    print(f"\n✓ Total: {total} questões UNICAMP → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
