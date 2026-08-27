"""
patch_uft_dia.py — Corrige o campo 'dia' nos JSONs UFT já gerados.

Os JSONs foram gerados com dia='exato', mas a constraint UNIQUE exige que
MANHA e TARDE tenham dias distintos para não conflitar.
Nova regra: dia = turno.lower() → 'manha' ou 'tarde'.

Uso: python patch_uft_dia.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = Path(r"C:\PROJETOS\HENRYJR\DADOS\json_uft")


def main():
    jsons = sorted(OUTPUT_DIR.glob("*.json"))
    print(f"Corrigindo {len(jsons)} arquivos UFT...")
    total = 0
    for f in jsons:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = 0
        for q in data:
            if q.get("dia") == "exato":
                turno = q.get("turno", "")
                if turno == "MANHA":
                    q["dia"] = "manha"
                    changed += 1
                elif turno == "TARDE":
                    q["dia"] = "tarde"
                    changed += 1
                else:
                    # Infere do nome do arquivo: uft_2019_manha.json
                    if "manha" in f.name.lower():
                        q["dia"] = "manha"
                    elif "tarde" in f.name.lower():
                        q["dia"] = "tarde"
                    changed += 1
        if changed:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  {f.name}: {changed} questoes atualizadas (exato → manha/tarde)")
        else:
            print(f"  {f.name}: sem alteracoes ({len(data)} questoes)")
        total += changed

    print(f"\nTotal corrigido: {total} questoes")


if __name__ == "__main__":
    main()
