import fitz
import os
import re

PASTA_PROVAS = r"C:\Projetos\henryjr\dados\provas"

# Testa um PDF de cada ano que zerou
ANOS_TESTAR = ["2009", "2011", "2012", "2013", "2014", "2015",
               "2016", "2017", "2018", "2022", "2023", "2024"]

def investigar():
    print("\n" + "="*60)
    print("  INVESTIGAÇÃO DE PADRÕES DE TEXTO POR ANO")
    print("="*60)

    for ano in ANOS_TESTAR:
        caminho_pdf = os.path.join(PASTA_PROVAS, ano, "dia1.pdf")
        if not os.path.exists(caminho_pdf):
            print(f"\n{ano}: ❌ dia1.pdf não encontrado")
            continue

        doc = fitz.open(caminho_pdf)

        # Pega texto das páginas 2, 3 e 4 (primeiras com questões)
        candidatos = []
        for num_pag in range(1, min(5, len(doc))):
            pagina = doc[num_pag]
            blocos = pagina.get_text("dict")["blocks"]
            for bloco in blocos:
                if bloco["type"] != 0:
                    continue
                for linha in bloco["lines"]:
                    for span in linha["spans"]:
                        texto = span["text"].strip()
                        # Captura qualquer coisa que pareça marcador de questão
                        if re.search(r'[Qq]uest|QUEST|Q\.?\s*\d', texto):
                            candidatos.append(repr(texto))

        doc.close()

        print(f"\n{ano}:")
        if candidatos:
            for c in candidatos[:8]:  # Mostra até 8 exemplos
                print(f"  → {c}")
        else:
            print(f"  ⚠️  Nenhum padrão de questão encontrado nas primeiras páginas")

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    investigar()