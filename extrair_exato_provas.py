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

import fitz
from lib_extrair import extrair_questoes_pdf, normalizar_questao_banco

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "EXATO_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_exato_provas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_pasta(nome: str) -> tuple[int, str | None]:
    """
    '2024'             → (2024, None)
    '2025 - 1º EDIÇÃO' → (2025, '1_EDICAO')
    '2025 - 2º EDIÇÃO' → (2025, '2_EDICAO')
    """
    m_edicao = re.search(r'(\d+)[°º]', nome)
    m_ano    = re.match(r'(\d{4})', nome)
    ano      = int(m_ano.group(1)) if m_ano else 0
    edicao   = f"{m_edicao.group(1)}_EDICAO" if m_edicao else None
    return ano, edicao


def parse_gabarito_exato_provas(gab_pdf: Path) -> tuple[dict, dict]:
    """
    Extrai gabaritos MANHÃ e TARDE do GAB.pdf das provas EXATO.

    Formato real do PDF:
        PROVA MANHÃ
        01
        02
        ...
        10
        C
        B
        ...
        B
        11
        ...
        PROVA TARDE
        01
        02
        ...

    Estratégia:
    1. Dividir o texto nas seções MANHÃ / TARDE
    2. Para cada seção: ler linhas e agrupar números (NN) e respostas ([A-E]|ANULADA)
       alternando em blocos de 10
    """
    doc = fitz.open(str(gab_pdf))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()
    texto = re.sub(r'[\x80-\x9f]', '', texto)

    def _parsear_secao(bloco: str) -> dict[int, str | None]:
        """Parseia uma seção (MANHÃ ou TARDE) do gabarito."""
        linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
        numeros: list[int] = []
        respostas: list[str | None] = []

        for linha in linhas:
            if re.match(r'^\d{1,2}$', linha):
                n = int(linha)
                if 1 <= n <= 60:
                    numeros.append(n)
            elif re.match(r'^[A-Ea-e]$', linha):
                respostas.append(linha.upper())
            elif re.match(r'^ANULADA$', linha, re.IGNORECASE):
                respostas.append(None)

        # Parear: os primeiros len(respostas) números com as respostas
        resultado: dict[int, str | None] = {}
        for i, resp in enumerate(respostas):
            if i < len(numeros):
                resultado[numeros[i]] = resp

        return resultado

    # Dividir nas seções MANHÃ e TARDE
    manh_re = re.compile(r'PROVA\s+MANH[Ãa]', re.IGNORECASE)
    tard_re  = re.compile(r'PROVA\s+TARDE',    re.IGNORECASE)

    m_manh = manh_re.search(texto)
    m_tard = tard_re.search(texto)

    if m_manh and m_tard:
        if m_manh.start() < m_tard.start():
            bloco_manh = texto[m_manh.end():m_tard.start()]
            bloco_tard = texto[m_tard.end():]
        else:
            bloco_tard = texto[m_tard.end():m_manh.start()]
            bloco_manh = texto[m_manh.end():]
    elif m_manh:
        bloco_manh = texto[m_manh.end():]
        bloco_tard = ""
    elif m_tard:
        bloco_tard = texto[m_tard.end():]
        bloco_manh = ""
    else:
        # Sem cabeçalhos — tentar parsear tudo como MANHÃ
        bloco_manh = texto
        bloco_tard = ""

    gab_manh = _parsear_secao(bloco_manh)
    gab_tard = _parsear_secao(bloco_tard) if bloco_tard else {}

    return gab_manh, gab_tard


def processar_pasta(pasta: Path) -> list[dict]:
    ano, edicao = parse_pasta(pasta.name)
    if not ano:
        print(f"  ⚠ Não foi possível detectar ano em: {pasta.name}")
        return []

    # Gabarito: aceita GAB.pdf, GAB PROVISÓRIO.pdf, GAB PROVISORIO.pdf
    gab_pdf = None
    for nome_gab in ["GAB.pdf", "GAB PROVISÓRIO.pdf", "GAB PROVISORIO.pdf",
                     "GAB PROVISÓRIO.pdf"]:
        p = pasta / nome_gab
        if p.exists():
            gab_pdf = p
            break

    # Ler gabaritos separados por turno
    if gab_pdf:
        gab_manh, gab_tard = parse_gabarito_exato_provas(gab_pdf)
        print(f"  Gabarito: {gab_pdf.name} | MANHÃ={len(gab_manh)}q | TARDE={len(gab_tard)}q")
    else:
        gab_manh, gab_tard = {}, {}
        print(f"  ⚠ Gabarito não encontrado em {pasta.name}")

    resultado = []
    for turno_variantes, turno_val, gabarito_map in [
        (["MANHÃ.pdf", "MANHÃ.PDF", "MANHA.pdf", "MANHA.PDF"], "MANHA", gab_manh),
        (["TARDE.pdf", "TARDE.PDF", "tarde.pdf"],                "TARDE", gab_tard),
    ]:
        prova_pdf = None
        for nome in turno_variantes:
            p = pasta / nome
            if p.exists():
                prova_pdf = p
                break

        if not prova_pdf:
            print(f"  ⚠ Não encontrado turno {turno_val} em {pasta.name}")
            continue

        print(f"\n  [{pasta.name}] {turno_val}")
        questoes_brutas = extrair_questoes_pdf(prova_pdf)
        n_gab = sum(1 for v in gabarito_map.values() if v is not None)
        print(f"    → {len(questoes_brutas)} questões | {len(gabarito_map)} gabaritos ({n_gab} com letra)")

        questoes_turno = []
        for idx, q in enumerate(questoes_brutas):
            numero_local = q.get("numero", idx + 1)
            row = normalizar_questao_banco(
                q=q,
                fonte="EXATO",
                tipo="PROVA",
                ano=ano,
                turno=turno_val,
                evento=None,
                provedor=None,
                dia=f"exato_{turno_val.lower()}",
                gabarito_map=gabarito_map,
                numero_global=numero_local,
            )
            questoes_turno.append(row)

        sufixo = f"_{edicao}" if edicao else ""
        out = OUTPUT_DIR / f"exato_prova_{ano}_{turno_val.lower()}{sufixo}.json"
        out.write_text(json.dumps(questoes_turno, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    → Salvo: {out.name} ({len(questoes_turno)} questões)")
        resultado.extend(questoes_turno)

    return resultado


def main():
    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    pastas = sorted(INPUT_DIR.iterdir())
    print(f"EXATO_PROVAS — {len(pastas)} pastas")
    total = 0
    for pasta in pastas:
        if pasta.is_dir():
            qs = processar_pasta(pasta)
            total += len(qs)
    print(f"\n✓ Total: {total} questões EXATO_PROVAS → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
