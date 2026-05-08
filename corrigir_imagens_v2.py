import fitz
import os
import json
import re
import shutil
from pathlib import Path

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
PASTA_PROVAS  = r"C:\Projetos\henryjr\dados\provas"
PASTA_IMAGENS = r"C:\Projetos\henryjr\dados\imagens"
PASTA_JSON    = r"C:\Projetos\henryjr\dados\json"
ESCALA        = 3
MARGEM_TOPO   = 8
MARGEM_BAIXO  = 20

# ─── DETECÇÃO DE COLUNAS ──────────────────────────────────────────────────────
def detectar_largura_pagina(pagina):
    return pagina.rect.width

def detectar_colunas(pagina):
    """
    Detecta se a página tem layout de 1 ou 2 colunas.
    Retorna: (num_colunas, x_divisor)
    """
    largura = pagina.rect.width
    blocos = pagina.get_text("dict")["blocks"]

    xs_texto = []
    for bloco in blocos:
        if bloco["type"] != 0:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                if span["text"].strip():
                    xs_texto.append(span["bbox"][0])

    if not xs_texto:
        return 1, largura

    # Verifica se há texto significativo em duas regiões distintas
    metade = largura / 2
    esquerda = sum(1 for x in xs_texto if x < metade * 0.7)
    direita   = sum(1 for x in xs_texto if x > metade * 1.1)

    if esquerda > 3 and direita > 3:
        return 2, metade
    return 1, largura

# ─── DETECÇÃO DE QUESTÕES ─────────────────────────────────────────────────────
def encontrar_questoes_pagina(pagina):
    """
    Detecta todos os marcadores de questão com posição (x, y) e número.
    Suporta todos os padrões do ENEM 2009-2024.
    """
    blocos = pagina.get_text("dict")["blocks"]
    questoes = {}  # num_q -> (x, y)
    spans = []

    for bloco in blocos:
        if bloco["type"] != 0:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                texto = span["text"].strip()
                x = span["bbox"][0]
                y = span["bbox"][1]
                spans.append((texto, x, y, span["bbox"]))

    for i, (texto, x, y, bbox) in enumerate(spans):
        num_q = None

        # Padrão 1: "QUESTÃO 01" ou "QUESTÃO 1" — 2011-2024
        m = re.match(r'^QUEST[ÃA]O\s+0*(\d+)$', texto, re.IGNORECASE)
        if m:
            num_q = int(m.group(1))

        # Padrão 2: "Questão 01" tamanho ~11 — 2019-2021
        if not num_q:
            m = re.match(r'^[Qq]uest[ãa]o\s+0*(\d+)$', texto.strip())
            if m:
                num_q = int(m.group(1))

        # Padrão 3: "Questão" isolado + número próximo — 2009
        if not num_q:
            if re.match(r'^[Qq]uest[ãa]o$', texto.strip()):
                for j in range(i+1, min(i+8, len(spans))):
                    prox, px, py, _ = spans[j]
                    if abs(py - y) > 25:
                        break
                    m2 = re.match(r'^0*(\d+)$', prox.strip())
                    if m2:
                        num_q = int(m2.group(1))
                        break

        if num_q and 1 <= num_q <= 185:
            # Guarda a posição mais alta (menor y) para cada questão
            if num_q not in questoes or y < questoes[num_q][1]:
                questoes[num_q] = (x, y)

    return questoes  # {num_q: (x, y)}

# ─── RECORTE ──────────────────────────────────────────────────────────────────
def recortar_questao(pagina, x_col, largura_col, y_inicio, y_fim, escala):
    """
    Recorta uma região específica da página (coluna + faixa vertical).
    """
    altura_pag = pagina.rect.height
    largura_pag = pagina.rect.width

    x0 = max(0, x_col - 5)
    x1 = min(largura_pag, x_col + largura_col + 5)
    y0 = max(0, y_inicio - MARGEM_TOPO)
    y1 = min(altura_pag, y_fim + MARGEM_BAIXO)

    if (y1 - y0) < 20 or (x1 - x0) < 20:
        return None

    clip = fitz.Rect(x0, y0, x1, y1)
    mat  = fitz.Matrix(escala, escala)
    pix  = pagina.get_pixmap(matrix=mat, clip=clip, alpha=False, colorspace=fitz.csRGB)
    return pix

def verificar_e_corrigir_negativo(pix):
    total = min(300, pix.width) * min(5, pix.height)
    if total == 0:
        return pix
    escuros = 0
    for x in range(0, min(pix.width, 300)):
        for y in range(0, min(pix.height, 5)):
            r, g, b = pix.pixel(x, y)[:3]
            if (r + g + b) / 3 < 50:
                escuros += 1
    if escuros / total > 0.6:
        samples = bytearray(pix.samples)
        for i in range(len(samples)):
            samples[i] = 255 - samples[i]
        return fitz.Pixmap(pix.colorspace, pix.width, pix.height, bytes(samples), False)
    return pix

# ─── PROCESSAMENTO PRINCIPAL ──────────────────────────────────────────────────
def processar_ano(ano):
    pasta_ano_img = os.path.join(PASTA_IMAGENS, str(ano))
    caminho_json  = os.path.join(PASTA_JSON, f"enem_{ano}.json")

    if not os.path.exists(caminho_json):
        print(f"   ⚠️  JSON não encontrado")
        return

    if os.path.exists(pasta_ano_img):
        shutil.rmtree(pasta_ano_img)

    with open(caminho_json, encoding="utf-8") as f:
        questoes_json = json.load(f)

    idx_questoes = {q["numero"]: q for q in questoes_json}
    imagens_geradas = 0
    negativos = 0

    for dia in ["dia1", "dia2"]:
        caminho_pdf = os.path.join(PASTA_PROVAS, str(ano), f"{dia}.pdf")
        if not os.path.exists(caminho_pdf):
            continue

        pasta_dia = os.path.join(pasta_ano_img, dia)
        Path(pasta_dia).mkdir(parents=True, exist_ok=True)

        doc = fitz.open(caminho_pdf)

        # ── Passa 1: mapeia TODAS as questões em TODAS as páginas ─────
        # mapa_global: num_q -> (num_pag, x, y)
        mapa_global = {}
        layout_pagina = {}  # num_pag -> (num_cols, x_divisor)

        for num_pag in range(len(doc)):
            pagina = doc[num_pag]
            layout_pagina[num_pag] = detectar_colunas(pagina)
            questoes_pag = encontrar_questoes_pagina(pagina)
            for num_q, (x, y) in questoes_pag.items():
                if num_q not in mapa_global:
                    mapa_global[num_q] = (num_pag, x, y)

        # Ordena questões por página e posição vertical
        questoes_sorted = sorted(
            mapa_global.items(),
            key=lambda v: (v[1][0], v[1][2])
        )

        # ── Passa 2: recorta cada questão ─────────────────────────────
        for i, (num_q, (num_pag, x_q, y_q)) in enumerate(questoes_sorted):
            pagina      = doc[num_pag]
            largura_pag = pagina.rect.width
            altura_pag  = pagina.rect.height

            num_cols, x_divisor = layout_pagina[num_pag]

            # Define coluna da questão atual
            if num_cols == 2:
                na_esquerda = x_q < x_divisor
                x_col       = 0 if na_esquerda else x_divisor + 2
                largura_col = (x_divisor - 2) if na_esquerda else (largura_pag - x_divisor - 2)
            else:
                na_esquerda = True
                x_col       = 0
                largura_col = largura_pag

            # ── Encontra y_fim e se há continuação na página seguinte ──
            y_fim           = altura_pag
            continua_prox   = True  # assume que continua até encontrar próxima questão

            for j in range(i + 1, len(questoes_sorted)):
                prox_q, (prox_pag, prox_x, prox_y) = questoes_sorted[j]

                if prox_pag == num_pag:
                    # Próxima questão na mesma página
                    if num_cols == 2:
                        mesma_col = (prox_x < x_divisor) == na_esquerda
                    else:
                        mesma_col = True

                    if mesma_col and prox_y > y_q:
                        y_fim         = prox_y
                        continua_prox = False
                        break
                else:
                    # Próxima questão está em outra página
                    # y_fim vai até o fim desta página
                    y_fim         = altura_pag
                    continua_prox = (prox_pag == num_pag + 1)
                    break

            # ── Recorta página atual ───────────────────────────────────
            pixmaps = []
            pix1 = recortar_questao(pagina, x_col, largura_col, y_q, y_fim, ESCALA)
            if pix1 and pix1.height >= 30:
                pixmaps.append(pix1)

            # ── Se questão continua na próxima página, captura lá ─────
            if continua_prox and num_pag + 1 < len(doc):
                prox_pagina      = doc[num_pag + 1]
                largura_prox     = prox_pagina.rect.width
                altura_prox      = prox_pagina.rect.height
                num_cols_p, xdiv = layout_pagina.get(num_pag + 1, (1, largura_prox))

                # Coluna correspondente na próxima página
                if num_cols_p == 2:
                    x_col_p     = 0 if na_esquerda else xdiv + 2
                    larg_col_p  = (xdiv - 2) if na_esquerda else (largura_prox - xdiv - 2)
                else:
                    x_col_p    = 0
                    larg_col_p = largura_prox

                # y_fim na próxima página = início da próxima questão nela
                y_fim_prox = altura_prox
                questoes_prox = encontrar_questoes_pagina(prox_pagina)
                for qn, (qx, qy) in sorted(questoes_prox.items(), key=lambda v: v[1][1]):
                    if qn != num_q and qy > 20:
                        if num_cols_p == 2:
                            mesma_col_p = (qx < xdiv) == na_esquerda
                        else:
                            mesma_col_p = True
                        if mesma_col_p:
                            y_fim_prox = qy
                            break

                pix2 = recortar_questao(
                    prox_pagina, x_col_p, larg_col_p, 0, y_fim_prox, ESCALA
                )
                if pix2 and pix2.height >= 30:
                    pixmaps.append(pix2)

            if not pixmaps:
                continue

            # ── Une os pixmaps verticalmente se houver continuação ─────
            if len(pixmaps) == 1:
                pix_final = pixmaps[0]
            else:
                # Junta as duas partes verticalmente
                largura  = max(p.width for p in pixmaps)
                altura   = sum(p.height for p in pixmaps)
                pix_final = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, largura, altura), False)
                pix_final.set_rect(pix_final.irect, (255, 255, 255))  # fundo branco

                y_offset = 0
                for p in pixmaps:
                    # Copia pixels manualmente linha a linha
                    src_samples = p.samples
                    n = p.n  # canais (3 para RGB)
                    for row in range(p.height):
                        for col in range(p.width):
                            pixel = p.pixel(col, row)
                            pix_final.set_pixel(col, y_offset + row, pixel[:3])
                    y_offset += p.height

            # Corrige negativo
            antes = pix_final
            pix_final = verificar_e_corrigir_negativo(pix_final)
            if pix_final is not antes:
                negativos += 1

            if pix_final.height < 60:
                continue

            nome = f"q{num_q:03d}_1.jpg"
            pix_final.save(os.path.join(pasta_dia, nome))
            imagens_geradas += 1

            if num_q in idx_questoes:
                idx_questoes[num_q]["imagens"]    = [f"{ano}/{dia}/q{num_q:03d}_1.jpg"]
                idx_questoes[num_q]["tem_imagem"] = True

        doc.close()

    # Limpa referências de questões sem imagem gerada
    for q in questoes_json:
        num = q["numero"]
        dia = q.get("dia", "dia1")
        if not os.path.exists(os.path.join(pasta_ano_img, dia, f"q{num:03d}_1.jpg")):
            q["imagens"]    = []
            q["tem_imagem"] = False

    # Salva JSON
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(questoes_json, f, ensure_ascii=False, indent=2)

    return imagens_geradas, negativos

def corrigir_todos():
    print("\n" + "="*60)
    print("  CORREÇÃO DE IMAGENS v2 — DETECÇÃO DE COLUNAS")
    print("="*60)

    anos = sorted([
        d for d in os.listdir(PASTA_PROVAS)
        if os.path.isdir(os.path.join(PASTA_PROVAS, d)) and d.isdigit()
    ])

    print(f"\nAnos: {', '.join(anos)}\n")

    resumo = []
    for ano in anos:
        print(f"📅 {ano}...", end=" ", flush=True)
        resultado = processar_ano(ano)
        if resultado:
            imgs, negs = resultado
            neg_str = f" | {negs} negativos" if negs else ""
            print(f"✅ {imgs} imagens{neg_str}")
            resumo.append((ano, imgs, negs))
        else:
            print("⚠️  pulado")

    print(f"\n{'='*60}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"\n{'ANO':<8} {'IMAGENS':<12} {'NEGATIVOS'}")
    print("─" * 32)
    for ano, imgs, negs in resumo:
        neg = str(negs) if negs else "—"
        print(f"{ano:<8} {imgs:<12} {neg}")
    total = sum(i for _, i, _ in resumo)
    print(f"\n  Total de imagens geradas: {total}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n⚠️  Este script vai substituir TODAS as imagens.")
    print("   Gabaritos do 2010 serão preservados.")
    ok = input("\nDeseja continuar? (s/n): ").strip().lower()
    if ok == "s":
        corrigir_todos()
    else:
        print("Cancelado.\n")