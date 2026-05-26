"""
extrair_enem_simulados.py — Extrai simulados preditivos ENEM.
Saída: DADOS/json_enem_simulados/{provedor}_{ano}_{evento}_{dia}.json

Estrutura esperada:
  DADOS/ENEM_SIMULADOS/{Provedor Ano}/{Simulado X}/
    - Arquivos com nomes variados (ver comentários no código)

IMPORTANTE: usa dia='simu_dia1'/'simu_dia2' (não 'dia1'/'dia2') para evitar
conflito de UNIQUE(ano, dia, numero) com questões ENEM reais do mesmo ano.

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


def normalizar_evento(nome_subpasta: str) -> str:
    """
    Extrai número do simulado e retorna 'SIM_NN'.
    'Simulado 00-2023' → 'SIM_00'
    'FB 01' → 'SIM_01'
    'Ciclo 01' → 'SIM_01'
    'SAS 06' → 'SIM_06'
    'SOMOS 03' → 'SIM_03'
    '01' (número puro) → 'SIM_01'
    """
    m = re.search(r'\b0*(\d+)\b', nome_subpasta)
    if m:
        num = int(m.group(1))
        return f"SIM_{num:02d}"
    return "SIM_01"


def classificar_arquivo(nome: str) -> tuple[str | None, str | None]:
    """
    Classifica um arquivo PDF como ('prova'/'gabarito', 'simu_dia1'/'simu_dia2').
    Retorna (None, None) se não reconhecido.

    Padrões de nome encontrados nas pastas:
    - "simu 00_2023 - 1º dia - bernoulli.pdf"         → prova, dia1
    - "Gab - simu 00_2023 - 1º dia - bernoulli.pdf"   → gabarito, dia1
    - "1º dia Bernoulli 00 -2024.pdf"                  → prova, dia1
    - "gab 1º dia Bernoulli 00 -2024.pdf"              → gabarito, dia1
    - "1 SAS 2023 - DIA 1 PROVA.pdf"                   → prova, dia1
    - "1 SAS 2023 - DIA 1 GABARITO.pdf"                → gabarito, dia1
    - "Simu 1º dia - SAS 01-2024.pdf"                  → prova, dia1
    - "GAB 1º dia - SAS 01-2024.pdf"                   → gabarito, dia1
    - "DIA 1 SOMOS 02-2023.pdf"                        → prova, dia1
    - "GAB DIA 1 SOMOS 02-2023.pdf"                    → gabarito, dia1
    - "SOMOS 1º dia - 01-2024 @wagnernamed.pdf"        → prova, dia1
    - "gab SOMOS 1º dia - 01-2024 @wagnernamed.pdf"    → gabarito, dia1
    - "1º_Poliedro_Enem_2023_-_1º_Dia_-_Prova.pdf"     → prova, dia1
    - "1º_Poliedro_Enem_2023_-_1º_Dia_-_Resolução.pdf" → gabarito, dia1
    - "1º Poliedro 2024 - prova d1 - @wagnernamed.pdf"  → prova, dia1
    - "1º Poliedro 2024 - gab D1 - @wagnernamed.pdf"    → gabarito, dia1
    - "1º Poliedro 2024 - D1 resolução - @wagnernamed.pdf" → gabarito, dia1
    - "Simulado 01 - DIA 1 FARIAS BRITO .pdf"          → prova, dia1
    - "Gabarito Dia 01 - Simulado 01 - FARIAS BRITO .pdf" → gabarito, dia1
    """
    n = nome.lower()

    # ── Detecta dia ──
    dia = None
    # Padrões dia1: "1º dia", "1 dia", "dia 1", "dia1", "d1", "d_1"
    if re.search(r'1[°º°\s]*dia|dia\s*1\b|d[_\-\s]?1\b|1[°º°\s]*_?dia', n):
        dia = "simu_dia1"
    # Padrões dia2: "2º dia", "2 dia", "dia 2", "dia2", "d2", "d_2"
    elif re.search(r'2[°º°\s]*dia|dia\s*2\b|d[_\-\s]?2\b|2[°º°\s]*_?dia', n):
        dia = "simu_dia2"

    # ── Detecta tipo (gabarito tem precedência sobre prova) ──
    tipo = None
    if re.search(r'\bgab\b|gabarito|resolu[cç]', n):
        tipo = "gabarito"
    elif re.search(r'\bprova\b|simu|sim[_\s]?\d|\bdia\b|poliedro|somos|sas|berno|farias', n):
        tipo = "prova"

    return tipo, dia


def processar_subpasta(subpasta: Path, provedor: str, ano: int, evento: str) -> list[dict]:
    """Processa uma subpasta (um simulado) e retorna questões dia1 + dia2."""
    pdfs = sorted(list(subpasta.glob("*.pdf")) + list(subpasta.glob("*.PDF")))
    if not pdfs:
        print(f"    ⚠ Sem PDFs em {subpasta.name}")
        return []

    # Organiza arquivos por (tipo, dia)
    arquivos: dict[tuple[str, str], Path] = {}
    for pdf in pdfs:
        tipo, dia = classificar_arquivo(pdf.name)
        if tipo and dia:
            # Não sobrescreve se já existe (toma o primeiro encontrado)
            if (tipo, dia) not in arquivos:
                arquivos[(tipo, dia)] = pdf

    # Se não classificou, tenta heurística por posição na lista ordenada
    if not arquivos:
        provas   = [p for p in pdfs if not re.search(r'gab|resolu', p.name.lower())]
        gabars   = [p for p in pdfs if re.search(r'gab|resolu', p.name.lower())]
        for i, p in enumerate(provas[:2]):
            dia = f"simu_dia{i+1}"
            arquivos[("prova", dia)] = p
        for i, g in enumerate(gabars[:2]):
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

    print(f"\n{'='*50}")
    print(f"{pasta.name} → provedor={provedor}, ano={ano}")
    subpastas = sorted(p for p in pasta.iterdir() if p.is_dir())
    resultado = []
    for subpasta in subpastas:
        evento = normalizar_evento(subpasta.name)
        qs = processar_subpasta(subpasta, provedor, ano, evento)
        resultado.extend(qs)

    return resultado


def main():
    parser = argparse.ArgumentParser(description="Extrai simulados ENEM preditivos para JSON")
    parser.add_argument("--provedor", help="Processar só esta pasta (ex: 'Bernoulli 2024')")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    pastas = sorted(p for p in INPUT_DIR.iterdir() if p.is_dir())
    if args.provedor:
        pastas = [p for p in pastas if args.provedor.lower() in p.name.lower()]

    print(f"ENEM_SIMULADOS — {len(pastas)} pastas a processar")
    total = 0
    for pasta in pastas:
        qs = processar_pasta_provedor(pasta)
        total += len(qs)

    print(f"\n✓ Total: {total} questões ENEM_SIMULADOS → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
