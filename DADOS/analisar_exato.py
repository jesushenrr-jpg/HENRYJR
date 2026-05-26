"""
Script para extrair texto das primeiras pÃ¡ginas de todos os PDFs EXATO
e gerar um relatÃ³rio de anÃ¡lise.
"""
import pdfplumber
import os
import json
import hashlib

PASTA = r"C:\PROJETOS\HENRYJR\DADOS\\EXATO_SIMULADOS"

arquivos = sorted([f for f in os.listdir(PASTA) if f.endswith('.pdf')])
print(f"Total de arquivos: {len(arquivos)}\n")

resultados = {}

for nome in arquivos:
    caminho = os.path.join(PASTA, nome)
    try:
        with pdfplumber.open(caminho) as pdf:
            n_paginas = len(pdf.pages)
            # Extrai texto das primeiras 3 pÃ¡ginas
            texto = ""
            for i in range(min(3, n_paginas)):
                t = pdf.pages[i].extract_text() or ""
                texto += t + "\n---PAGINA---\n"

            # Hash das primeiras 2000 chars para detectar duplicatas
            h = hashlib.md5(texto[:2000].encode('utf-8', errors='ignore')).hexdigest()

            resultados[nome] = {
                "paginas": n_paginas,
                "texto_inicio": texto[:3000],
                "hash_inicio": h
            }
            print(f"OK: {nome} ({n_paginas} pgs)".encode('ascii', errors='replace').decode())
    except Exception as e:
        resultados[nome] = {
            "paginas": 0,
            "texto_inicio": f"ERRO: {e}",
            "hash_inicio": "ERRO"
        }
        print(f"ERRO: {nome} - {e}".encode('ascii', errors='replace').decode())

# Salvar para anÃ¡lise
with open(r"C:\PROJETOS\HENRYJR\DADOS\exato_textos.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print("\nSalvo em exato_textos.json")

