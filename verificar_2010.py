import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("dados/json_v2/enem_2010.json", encoding="utf-8") as f:
    qs = json.load(f)

# Q007 amostra
q7 = next(q for q in qs if q["numero"] == 7)
print("=== Q007 ===")
for p in q7["enunciado"][:4]:
    print(f"  {p[:110]}")
for k, v in q7["alternativas"].items():
    print(f"  [{k}] {v[:90]}")
print(f"  Gabarito: {q7['gabarito']}")

# Qualidade geral
print()
print("=== RESUMO ===")
com_5  = sum(1 for q in qs if len(q["alternativas"]) == 5)
com_4  = sum(1 for q in qs if len(q["alternativas"]) == 4)
com_3  = sum(1 for q in qs if len(q["alternativas"]) == 3)
com_02 = sum(1 for q in qs if len(q["alternativas"]) <= 2)
print(f"  5 alternativas: {com_5}/180")
print(f"  4 alternativas: {com_4}")
print(f"  3 alternativas: {com_3}")
print(f"  0-2 alternativas: {com_02}")

# Lista das incompletas
incompletas = [q for q in qs if len(q["alternativas"]) < 5]
print(f"\n=== QUESTOES INCOMPLETAS ({len(incompletas)}) ===")
for q in incompletas:
    n_alts = len(q["alternativas"])
    chaves = list(q["alternativas"].keys())
    print(f"  Q{q['numero']:03d} ({q['dia']}) — {n_alts} alt: {chaves}")
