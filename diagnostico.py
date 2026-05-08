import json
import os

PASTA_JSON   = r"C:\Projetos\henryjr\dados\json"
PASTA_PROVAS = r"C:\Projetos\henryjr\dados\provas"

def diagnosticar():
    print("\n" + "="*60)
    print("  DIAGNÓSTICO — BANCO DE QUESTÕES ENEM")
    print("="*60)

    # ── Verifica arquivos presentes em cada pasta de ano ──────────────
    print("\n📁 ARQUIVOS POR ANO:")
    print(f"{'ANO':<8} {'dia1':<8} {'dia2':<8} {'gab_dia1':<12} {'gab_dia2'}")
    print("─" * 50)

    anos = sorted([
        d for d in os.listdir(PASTA_PROVAS)
        if os.path.isdir(os.path.join(PASTA_PROVAS, d)) and d.isdigit()
    ])

    for ano in anos:
        pasta = os.path.join(PASTA_PROVAS, ano)
        arquivos = os.listdir(pasta)

        tem_dia1  = "✅" if "dia1.pdf"          in arquivos else "❌"
        tem_dia2  = "✅" if "dia2.pdf"          in arquivos else "❌"
        tem_gab1  = "✅" if "gabarito_dia1.pdf" in arquivos else "❌"
        tem_gab2  = "✅" if "gabarito_dia2.pdf" in arquivos else "❌"

        print(f"{ano:<8} {tem_dia1:<8} {tem_dia2:<8} {tem_gab1:<12} {tem_gab2}")

    # ── Verifica questões sem gabarito por ano ────────────────────────
    print("\n\n❓ QUESTÕES SEM GABARITO POR ANO:")
    print(f"{'ANO':<8} {'QTD SEM GABARITO':<20} NÚMEROS")
    print("─" * 60)

    for ano in anos:
        caminho = os.path.join(PASTA_JSON, f"enem_{ano}.json")
        if not os.path.exists(caminho):
            continue

        with open(caminho, encoding="utf-8") as f:
            questoes = json.load(f)

        sem_gab = [q["numero"] for q in questoes if not q["gabarito"]]

        if sem_gab:
            numeros = ", ".join(str(n) for n in sorted(sem_gab)[:10])
            if len(sem_gab) > 10:
                numeros += f"... (+{len(sem_gab)-10} mais)"
            print(f"{ano:<8} {len(sem_gab):<20} {numeros}")

    # ── Verifica estrutura de uma questão de exemplo ──────────────────
    print("\n\n🔍 EXEMPLO DE QUESTÃO EXTRAÍDA (2023, Q.1):")
    print("─" * 60)

    caminho_2023 = os.path.join(PASTA_JSON, "enem_2023.json")
    if os.path.exists(caminho_2023):
        with open(caminho_2023, encoding="utf-8") as f:
            questoes = json.load(f)

        q = next((q for q in questoes if q["numero"] == 1), questoes[0])
        print(f"  Número:      {q['numero']}")
        print(f"  Ano:         {q['ano']}")
        print(f"  Área:        {q['area']}")
        print(f"  Gabarito:    {q['gabarito']}")
        print(f"  Tem imagem:  {q['tem_imagem']} ({len(q['imagens'])} arquivo(s))")
        print(f"  Alternativas:{list(q['alternativas'].keys())}")
        print(f"  Enunciado:   {q['enunciado'][:120]}...")

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    diagnosticar()