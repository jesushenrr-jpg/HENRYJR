import fitz
import json
import os
import re
from pathlib import Path

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
PASTA_PROVAS = r"C:\Projetos\henryjr\dados\provas\2010"
PASTA_JSON   = r"C:\Projetos\henryjr\dados\json"

# Sensibilidade da detecção de verde
# Aumente se estiver errando (ex: 30), diminua se não detectar (ex: 10)
LIMIAR_PIXELS_VERDES = 15

# Resolução de renderização (2 = alta qualidade, 3 = máxima)
ESCALA = 2

# ─── DETECÇÃO DE VERDE ────────────────────────────────────────────────────────
def contar_pixels_verdes(pix, rect, margem=20):
    """
    Conta pixels verdes em uma região retangular do pixmap.
    rect = (x0, y0, x1, y1) já em coordenadas do pixmap (escalonadas).
    margem = área extra ao redor da letra para capturar o círculo.
    """
    x0 = max(0, int(rect[0] - margem))
    y0 = max(0, int(rect[1] - margem))
    x1 = min(pix.width,  int(rect[2] + margem))
    y1 = min(pix.height, int(rect[3] + margem))

    verdes = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixel = pix.pixel(x, y)
            r, g, b = pixel[0], pixel[1], pixel[2]
            # Verde: canal G dominante, R e B baixos
            if g > 100 and g > r * 1.3 and g > b * 1.3:
                verdes += 1
    return verdes

# ─── EXTRAÇÃO POR PÁGINA ──────────────────────────────────────────────────────
def extrair_gabarito_pagina(pagina, escala):
    """
    Analisa uma página e retorna dicionário {numero_questao: letra_gabarito}.
    """
    gabarito_pagina = {}

    # Renderiza a página
    mat = fitz.Matrix(escala, escala)
    pix = pagina.get_pixmap(matrix=mat)

    # Extrai blocos de texto com posição
    blocos = pagina.get_text("dict")["blocks"]

    # Mapeia posição de cada texto na página
    # Estrutura: [(texto, x0, y0, x1, y1), ...]
    textos_posicao = []
    for bloco in blocos:
        if bloco["type"] != 0:  # Apenas blocos de texto
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                texto = span["text"].strip()
                if texto:
                    bbox = span["bbox"]
                    textos_posicao.append((texto, bbox[0], bbox[1], bbox[2], bbox[3]))

    # Encontra números de questão na página
    numeros_questao = []
    for texto, x0, y0, x1, y1 in textos_posicao:
        # Padrão: "Questão 103" ou só o número
        match = re.search(r'[Qq]uest[ãa]o\s*(\d+)', texto)
        if match:
            numeros_questao.append((int(match.group(1)), x0, y0))
            continue
        # Número isolado que pode ser questão (1-185)
        match2 = re.match(r'^(\d{1,3})$', texto)
        if match2:
            num = int(match2.group(1))
            if 1 <= num <= 185:
                numeros_questao.append((num, x0, y0))

    # Para cada questão encontrada, procura as alternativas A-E
    for num_q, qx, qy in numeros_questao:
        # Define região de busca: abaixo e próxima ao número da questão
        # Alternativas geralmente ficam nos próximos 300 pontos verticais
        alternativas_encontradas = {}

        for texto, x0, y0, x1, y1 in textos_posicao:
            # Verifica se é uma letra de alternativa (A, B, C, D ou E isolada)
            if texto not in ["A", "B", "C", "D", "E",
                             "a", "b", "c", "d", "e"]:
                continue

            # Verifica se está na região da questão (abaixo do número)
            # Tolerância horizontal generosa, vertical limitada
            if not (qx - 400 <= x0 <= qx + 400 and qy <= y0 <= qy + 400):
                continue

            letra = texto.upper()

            # Converte coordenadas para o pixmap escalonado
            px0 = x0 * escala
            py0 = y0 * escala
            px1 = x1 * escala
            py1 = y1 * escala

            # Conta pixels verdes ao redor desta letra
            verdes = contar_pixels_verdes(pix, (px0, py0, px1, py1), margem=25)
            alternativas_encontradas[letra] = verdes

        # A alternativa com mais pixels verdes é o gabarito
        if alternativas_encontradas:
            letra_correta = max(alternativas_encontradas, key=alternativas_encontradas.get)
            max_verdes = alternativas_encontradas[letra_correta]

            # Só aceita se encontrou verde suficiente
            if max_verdes >= LIMIAR_PIXELS_VERDES:
                gabarito_pagina[num_q] = letra_correta

    return gabarito_pagina

# ─── PROCESSAMENTO PRINCIPAL ──────────────────────────────────────────────────
def extrair_gabarito_2010():
    print("\n" + "="*60)
    print("  EXTRAÇÃO GABARITO 2010 — DETECÇÃO POR COR")
    print("="*60)

    gabarito_completo = {}

    for dia in ["dia1", "dia2"]:
        caminho = os.path.join(PASTA_PROVAS, f"gabarito_{dia}.pdf")

        if not os.path.exists(caminho):
            print(f"\n❌ Arquivo não encontrado: {caminho}")
            continue

        print(f"\n📖 Processando gabarito_{dia}.pdf...")
        doc = fitz.open(caminho)
        gabarito_dia = {}

        for num_pag, pagina in enumerate(doc):
            resultado = extrair_gabarito_pagina(pagina, ESCALA)
            if resultado:
                gabarito_dia.update(resultado)
                print(f"   Página {num_pag+1}: {len(resultado)} gabarito(s) detectado(s) "
                      f"→ questões {sorted(resultado.keys())}")

        doc.close()
        print(f"   ✅ Total {dia}: {len(gabarito_dia)} gabaritos extraídos")
        gabarito_completo.update(gabarito_dia)

    # ── Relatório ──────────────────────────────────────────────────────
    print(f"\n📊 Total geral: {len(gabarito_completo)} gabaritos")

    if gabarito_completo:
        print("\n   Prévia (primeiras 20 questões):")
        for num in sorted(gabarito_completo.keys())[:20]:
            print(f"   Q{num:03d} → {gabarito_completo[num]}")

    # ── Atualiza o JSON de 2010 ────────────────────────────────────────
    caminho_json = os.path.join(PASTA_JSON, "enem_2010.json")

    if not os.path.exists(caminho_json):
        print(f"\n❌ JSON de 2010 não encontrado: {caminho_json}")
        return

    with open(caminho_json, encoding="utf-8") as f:
        questoes = json.load(f)

    # Aplica os gabaritos extraídos
    atualizadas = 0
    for q in questoes:
        num = q["numero"]
        if num in gabarito_completo and not q["gabarito"]:
            q["gabarito"] = gabarito_completo[num]
            atualizadas += 1

    # Salva o JSON atualizado
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    sem_gabarito = [q["numero"] for q in questoes if not q["gabarito"]]

    print(f"\n✅ JSON de 2010 atualizado!")
    print(f"   Gabaritos preenchidos: {atualizadas}")
    print(f"   Questões ainda sem gabarito: {len(sem_gabarito)}")

    if sem_gabarito:
        print(f"   Números: {sorted(sem_gabarito)}")
        print("\n   ⚠️  Para as questões restantes, rode o script")
        print("   com LIMIAR_PIXELS_VERDES menor (ex: 8) e tente novamente.")
    else:
        print("   🎉 Todos os gabaritos de 2010 preenchidos!")

    print("\n" + "="*60 + "\n")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    extrair_gabarito_2010()