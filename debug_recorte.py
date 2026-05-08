import fitz
import os
import re

PASTA_PROVAS = r"C:\Projetos\henryjr\dados\provas"

def debug_ano(ano, dia="dia1", max_pags=6):
    caminho_pdf = os.path.join(PASTA_PROVAS, ano, f"{dia}.pdf")
    if not os.path.exists(caminho_pdf):
        print(f"\n{ano}/{dia}: arquivo nao encontrado")
        return

    doc = fitz.open(caminho_pdf)

    print(f"\n{'='*60}")
    print(f"  DEBUG: {ano} -- {dia}.pdf")
    print(f"{'='*60}")

    for num_pag in range(1, min(max_pags, len(doc))):
        pagina = doc[num_pag]
        altura = pagina.rect.height
        blocos = pagina.get_text("dict")["blocks"]

        print(f"\n  Pagina {num_pag+1} (altura={altura:.0f}pt):")

        for bloco in blocos:
            if bloco["type"] != 0:
                continue
            for linha in bloco["lines"]:
                for span in linha["spans"]:
                    texto = span["text"].strip()
                    if not texto:
                        continue
                    y = span["bbox"][1]
                    tamanho = span["size"]

                    eh_questao = bool(re.search(
                        r'QUEST[ÃA]O\s*\d+|^[Qq]uest[ãa]o$', texto
                    ))
                    eh_titulo = tamanho >= 10 and len(texto) < 30

                    if eh_questao or eh_titulo:
                        flag = "[QUESTAO]" if eh_questao else "[titulo]"
                        print(f"    y={y:6.1f} | size={tamanho:4.1f} | {flag} | {repr(texto)}")

    doc.close()
    
# Testa 2 anos: um que funcionou e um que não funcionou
# Testa todos os anos
# Testa todos os anos e os dois dias
anos = ["2009","2010","2011","2012","2013","2014","2015",
        "2016","2017","2018","2019","2020","2021","2022","2023","2024"]
for ano in anos:
    for dia in ["dia1", "dia2"]:
        debug_ano(ano, dia)