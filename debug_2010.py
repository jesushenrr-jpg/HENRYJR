import fitz
import os

CAMINHO = r"C:\Projetos\henryjr\dados\provas\2010\gabarito_dia1.pdf"

doc = fitz.open(CAMINHO)

# Analisa as 3 primeiras páginas
for num_pag in range(min(3, len(doc))):
    pagina = doc[num_pag]
    print(f"\n{'='*50}")
    print(f"PÁGINA {num_pag + 1}")
    print(f"{'='*50}")

    # Todo o texto extraído
    texto = pagina.get_text()
    print(f"\n--- TEXTO BRUTO (primeiros 800 caracteres) ---")
    print(repr(texto[:800]))

    # Blocos com posição
    print(f"\n--- SPANS COM POSIÇÃO (primeiros 20) ---")
    blocos = pagina.get_text("dict")["blocks"]
    count = 0
    for bloco in blocos:
        if bloco["type"] != 0:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                texto_span = span["text"].strip()
                if texto_span:
                    print(f"  '{texto_span}' → bbox: {[round(x,1) for x in span['bbox']]}")
                    count += 1
                    if count >= 20:
                        break
            if count >= 20:
                break
        if count >= 20:
            break

doc.close()