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

# Resolução de renderização (3 = ~216 DPI, boa qualidade)
ESCALA = 3

# Margem extra acima e abaixo do recorte da questão (em pontos PDF)
MARGEM_TOPO   = 5
MARGEM_BAIXO  = 15

# Tamanho mínimo de recorte para considerar válido (em pixels)
ALTURA_MINIMA = 80

# Anos protegidos (não re-extraem imagens — gabarito manual)
ANOS_PROTEGIDOS = []  # 2009 já foi tratado separadamente

# ─── FUNÇÕES ──────────────────────────────────────────────────────────────────
def encontrar_questoes_na_pagina(pagina):
    """
    Retorna lista de (numero_questao, y_inicio) ordenada por posição vertical.
    Reconhece todos os padrões do ENEM 2009-2024.
    """
    blocos = pagina.get_text("dict")["blocks"]
    vistas = {}
    spans_com_posicao = []

    # Coleta todos os spans com posição
    for bloco in blocos:
        if bloco["type"] != 0:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                texto = span["text"].strip()
                y_pos = span["bbox"][1]
                spans_com_posicao.append((texto, y_pos, span["bbox"]))

    # Padrão 1: "QUESTÃO 01" ou "QUESTÃO 1" — tudo no mesmo span (2011-2024)
    for texto, y_pos, bbox in spans_com_posicao:
        match = re.match(r'^QUEST[ÃA]O\s+0*(\d+)$', texto.strip(), re.IGNORECASE)
        if match:
            num_q = int(match.group(1))
            if 1 <= num_q <= 185:
                if num_q not in vistas or y_pos < vistas[num_q]:
                    vistas[num_q] = y_pos

    # Padrão 2: "Questão" isolado + número no próximo span (2009)
    # Procura spans com "Questão" isolado e busca número próximo abaixo
    if not vistas:
        for i, (texto, y_pos, bbox) in enumerate(spans_com_posicao):
            if re.match(r'^[Qq]uest[ãa]o$', texto.strip()):
                # Procura número nos próximos 5 spans na mesma região vertical
                for j in range(i + 1, min(i + 6, len(spans_com_posicao))):
                    prox_texto, prox_y, prox_bbox = spans_com_posicao[j]
                    if abs(prox_y - y_pos) > 30:
                        break
                    match_num = re.match(r'^0*(\d+)$', prox_texto.strip())
                    if match_num:
                        num_q = int(match_num.group(1))
                        if 1 <= num_q <= 185:
                            if num_q not in vistas or y_pos < vistas[num_q]:
                                vistas[num_q] = y_pos
                        break

    # Filtra falsos positivos: "O reconhecimento da paisagem em questão"
    # Já tratado pelo ^ e $ nos padrões acima

    return sorted(vistas.items(), key=lambda x: x[1])

def recortar_questao(pagina, y_inicio, y_fim, escala):
    """
    Renderiza e recorta a região vertical de y_inicio até y_fim da página.
    Retorna um Pixmap recortado com fundo branco garantido.
    """
    altura_pagina = pagina.rect.height
    largura_pagina = pagina.rect.width

    # Aplica margens com limites da página
    y0 = max(0, y_inicio - MARGEM_TOPO)
    y1 = min(altura_pagina, y_fim + MARGEM_BAIXO)

    if (y1 - y0) < 10:
        return None

    # Define o clip (região a renderizar)
    clip = fitz.Rect(0, y0, largura_pagina, y1)

    # Renderiza com fundo branco explícito
    mat = fitz.Matrix(escala, escala)
    pix = pagina.get_pixmap(matrix=mat, clip=clip, alpha=False, colorspace=fitz.csRGB)

    return pix

def verificar_negativo(pix):
    """
    Verifica se a imagem está invertida (negativo).
    Imagens normais de prova têm fundo claro (pixels claros dominantes).
    """
    # Amostra pixels do topo da imagem (geralmente fundo)
    pixels_claros = 0
    pixels_escuros = 0
    amostras = min(500, pix.width * 5)

    for x in range(0, min(pix.width, amostras)):
        for y in range(0, min(5, pix.height)):
            pixel = pix.pixel(x, y)
            brilho = (pixel[0] + pixel[1] + pixel[2]) / 3
            if brilho > 200:
                pixels_claros += 1
            elif brilho < 50:
                pixels_escuros += 1

    # Se maioria escura, provavelmente é negativo
    total = pixels_claros + pixels_escuros
    if total > 0 and pixels_escuros / total > 0.7:
        return True
    return False

def inverter_imagem(pix):
    """
    Inverte as cores de um Pixmap (corrige negativo).
    """
    import array
    samples = bytearray(pix.samples)
    for i in range(len(samples)):
        samples[i] = 255 - samples[i]
    return fitz.Pixmap(pix.colorspace, pix.width, pix.height, bytes(samples), False)

# ─── PROCESSAMENTO PRINCIPAL ──────────────────────────────────────────────────
def corrigir_imagens_todos_anos():
    print("\n" + "="*60)
    print("  CORREÇÃO DE IMAGENS — TODOS OS ANOS")
    print("  Estratégia: Recorte por região de questão")
    print("="*60)

    anos = sorted([
        d for d in os.listdir(PASTA_PROVAS)
        if os.path.isdir(os.path.join(PASTA_PROVAS, d)) and d.isdigit()
    ])

    print(f"\n📚 Anos a processar: {', '.join(anos)}")

    resumo = []

    for ano in anos:
        print(f"\n{'─'*50}")
        print(f"📅 ANO: {ano}")

        pasta_ano_imagens = os.path.join(PASTA_IMAGENS, ano)
        caminho_json = os.path.join(PASTA_JSON, f"enem_{ano}.json")

        if not os.path.exists(caminho_json):
            print(f"   ⚠️  JSON não encontrado, pulando...")
            continue

        # Carrega questões do JSON
        with open(caminho_json, encoding="utf-8") as f:
            questoes = json.load(f)

        # Limpa imagens antigas do ano (exceto 2009 que já foi tratado)
        if ano != "2009" and os.path.exists(pasta_ano_imagens):
            shutil.rmtree(pasta_ano_imagens)
            print(f"   🗑️  Imagens antigas removidas")

        total_imagens   = 0
        total_negativos = 0
        questoes_com_img = 0

        for dia in ["dia1", "dia2"]:
            caminho_pdf = os.path.join(PASTA_PROVAS, ano, f"{dia}.pdf")

            if not os.path.exists(caminho_pdf):
                print(f"   ⚠️  {dia}.pdf não encontrado")
                continue

            pasta_dia = os.path.join(pasta_ano_imagens, dia)
            Path(pasta_dia).mkdir(parents=True, exist_ok=True)

            doc = fitz.open(caminho_pdf)

            # Mapeia todas as questões e suas posições em todas as páginas
            mapa_questoes = {}  # num_q -> (num_pag, y_inicio)

            for num_pag in range(len(doc)):
                pagina = doc[num_pag]
                questoes_pag = encontrar_questoes_na_pagina(pagina)
                for num_q, y_pos in questoes_pag:
                    if num_q not in mapa_questoes:
                        mapa_questoes[num_q] = (num_pag, y_pos)

            # Para cada questão, determina y_fim e extrai recorte
            questoes_ordenadas = sorted(mapa_questoes.items(), key=lambda x: (x[1][0], x[1][1]))

            for i, (num_q, (num_pag, y_inicio)) in enumerate(questoes_ordenadas):
                pagina = doc[num_pag]
                altura_pagina = pagina.rect.height

                # y_fim = início da próxima questão na mesma página, ou fim da página
                y_fim = altura_pagina
                if i + 1 < len(questoes_ordenadas):
                    prox_q, (prox_pag, prox_y) = questoes_ordenadas[i + 1]
                    if prox_pag == num_pag:
                        y_fim = prox_y

                # Só salva se a região tiver altura suficiente
                altura_regiao = y_fim - y_inicio
                if altura_regiao < 30:
                    continue

                # Renderiza o recorte
                pix = recortar_questao(pagina, y_inicio, y_fim, ESCALA)
                if pix is None:
                    continue

                # Verifica e corrige negativo
                eh_negativo = verificar_negativo(pix)
                if eh_negativo:
                    pix = inverter_imagem(pix)
                    total_negativos += 1

                # Só salva se tiver altura mínima em pixels
                if pix.height < ALTURA_MINIMA:
                    continue

                nome_arquivo = f"q{num_q:03d}_1.jpg"
                caminho_saida = os.path.join(pasta_dia, nome_arquivo)
                pix.save(caminho_saida)
                total_imagens += 1

            doc.close()

        # Atualiza o JSON com os novos caminhos de imagem
        for q in questoes:
            num   = q["numero"]
            dia   = q.get("dia", "dia1")
            pasta = os.path.join(pasta_ano_imagens, dia)
            nome  = f"q{num:03d}_1.jpg"
            caminho_completo = os.path.join(pasta, nome)

            if os.path.exists(caminho_completo):
                q["imagens"]    = [f"{ano}/{dia}/q{num:03d}_1.jpg"]
                q["tem_imagem"] = True
                questoes_com_img += 1
            else:
                q["imagens"]    = []
                q["tem_imagem"] = False

        # Salva JSON atualizado (protege 2010)
        if ano == "2010":
            print(f"   ⚠️  2010 protegido — JSON de imagens atualizado, gabaritos mantidos")

        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(questoes, f, ensure_ascii=False, indent=2)

        print(f"   ✅ Imagens geradas:      {total_imagens}")
        print(f"   ✅ Questões com imagem:  {questoes_com_img}")
        if total_negativos:
            print(f"   🔄 Negativos corrigidos: {total_negativos}")

        resumo.append({
            "ano": ano,
            "imagens": total_imagens,
            "com_imagem": questoes_com_img,
            "negativos": total_negativos
        })

    # ── Relatório final ────────────────────────────────────────────────
    print(f"\n\n{'='*60}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"\n{'ANO':<8} {'IMAGENS':<12} {'COM IMAGEM':<14} {'NEGATIVOS'}")
    print("─" * 48)
    for r in resumo:
        neg = f"{r['negativos']}" if r['negativos'] > 0 else "—"
        print(f"{r['ano']:<8} {r['imagens']:<12} {r['com_imagem']:<14} {neg}")
    print(f"\n✅ Correção concluída para todos os anos!")
    print(f"{'='*60}\n")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n⚠️  Este script vai substituir TODAS as imagens extraídas.")
    print("   Os JSONs serão atualizados com os novos caminhos.")
    print("   O gabarito do 2010 será preservado.")
    confirmar = input("\nDeseja continuar? (s/n): ").strip().lower()
    if confirmar == "s":
        corrigir_imagens_todos_anos()
    else:
        print("\nOperação cancelada.\n")