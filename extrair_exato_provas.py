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
    '2024'             → (2024, None)
    '2025 - 1º EDIÇÃO' → (2025, '1_EDICAO')
    '2025 - 2º EDIÇÃO' → (2025, '2_EDICAO')
    """
    m_edicao = re.search(r'(\d+)[°º]', nome)
    m_ano    = re.match(r'(\d{4})', nome)
    ano      = int(m_ano.group(1)) if m_ano else 0
    edicao   = f"{m_edicao.group(1)}_EDICAO" if m_edicao else None
    return ano, edicao


def processar_pasta(pasta: Path) -> list[dict]:
    ano, edicao = parse_pasta(pasta.name)
    if not ano:
        print(f"  ⚠ Não foi possível detectar ano em: {pasta.name}")
        return []

    resultado = []
    for turno_variantes, turno_val in [
        (["MANHÃ.pdf", "MANHÃ.PDF", "MANHA.pdf", "MANHA.PDF"], "MANHA"),
        (["TARDE.pdf", "TARDE.PDF", "TARDE.pdf", "tarde.pdf"],  "TARDE"),
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

        # Gabarito: aceita GAB.pdf ou GAB PROVISÓRIO.pdf
        gab_pdf = None
        for nome_gab in ["GAB.pdf", "GAB PROVISÓRIO.pdf", "GAB PROVISORIO.pdf"]:
            p = pasta / nome_gab
            if p.exists():
                gab_pdf = p
                break

        print(f"\n  [{pasta.name}] {turno_val}")
        questoes_brutas = extrair_questoes_pdf(prova_pdf)
        gabarito_map    = parse_gabarito(gab_pdf) if gab_pdf else {}
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
                evento=None,      # EXATO provas não têm evento (diferente dos simulados)
                provedor=None,
                dia="exato",
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
        import sys; sys.exit(1)

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
