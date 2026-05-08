"""
Corrige as áreas das questões do ENEM 2009.

Estrutura correta (conforme cabeçalhos das páginas do PDF):
  dia1: Q001–045 → Ciências da Natureza e suas Tecnologias
        Q046–090 → Ciências Humanas e suas Tecnologias
  dia2: Q091–135 → Linguagens, Códigos e suas Tecnologias
        Q136–180 → Matemática e suas Tecnologias

Aplica correção em ambos os JSONs: dados/json e dados/json_v2.
"""

import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CORRECOES_DIA1 = {
    range(1, 46):  "Ciencias da Natureza e suas Tecnologias",
    range(46, 91): "Ciencias Humanas e suas Tecnologias",
}
CORRECOES_DIA2 = {
    range(91, 136):  "Linguagens, Codigos e suas Tecnologias",
    range(136, 181): "Matematica e suas Tecnologias",
}


def area_correta(numero: int, dia: str) -> str | None:
    mapa = CORRECOES_DIA1 if dia == "dia1" else CORRECOES_DIA2
    for intervalo, area in mapa.items():
        if numero in intervalo:
            return area
    return None


def corrigir_json(caminho: Path) -> dict:
    with open(caminho, encoding="utf-8") as f:
        questoes = json.load(f)

    trocas = 0
    for q in questoes:
        num = q["numero"]
        dia = q.get("dia", "")
        correto = area_correta(num, dia)
        if correto and q.get("area") != correto:
            print(f"  Q{num:03d} ({dia}): '{q.get('area')}' → '{correto}'")
            q["area"] = correto
            trocas += 1

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    return {"trocas": trocas}


def main():
    base = Path(r"C:\PROJETOS\HENRYJR\dados")
    targets = [
        base / "json"    / "enem_2009.json",
        base / "json_v2" / "enem_2009.json",
    ]

    print("=" * 60)
    print("  CORREÇÃO DE ÁREAS — ENEM 2009")
    print("=" * 60)

    for p in targets:
        if not p.exists():
            print(f"\n[AVISO] Não encontrado: {p}")
            continue
        print(f"\n{p.relative_to(base.parent)}")
        stats = corrigir_json(p)
        print(f"  → {stats['trocas']} área(s) corrigida(s)")

    print("\n" + "=" * 60)
    print("  CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    main()
