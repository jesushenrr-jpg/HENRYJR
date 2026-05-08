"""
Extração de imagens para as questões do ENEM 2010 com alternativas visuais.

Para questões cuja alternativas são imagens/fórmulas estruturais/diagramas,
o OCR não consegue extrair o texto — então salvamos a região da questão como
imagem e atualizamos o JSON com os campos imagens/tem_imagem.

Questões alvo: Q080, Q084, Q102, Q136, Q137, Q142
"""

import fitz
import json
import os
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ.setdefault("TESSDATA_PREFIX", r"C:\PROJETOS\HENRYJR\tessdata")

PASTA_PROVAS  = r"C:\PROJETOS\HENRYJR\dados\PROVAS\2010"
PASTA_IMAGENS = Path(r"C:\PROJETOS\HENRYJR\dados\imagens\2010")
JSON_PATH     = r"C:\PROJETOS\HENRYJR\dados\json_v2\enem_2010.json"
ZOOM          = 300 / 72   # ~300 DPI
LANG          = "por"

# Questões incompletas por dia
TARGETS = {
    "dia1": {80, 84},
    "dia2": {102, 136, 137, 142},
}


def ocr_col(img: Image.Image) -> str:
    return pytesseract.image_to_string(img, lang=LANG, config="--oem 1 --psm 6")


def ocr_col_data(img: Image.Image):
    """Retorna DataFrame-like com bboxes de cada palavra."""
    return pytesseract.image_to_data(
        img, lang=LANG, config="--oem 1 --psm 6",
        output_type=pytesseract.Output.DICT
    )


def encontrar_y_questao(data: dict, num: int) -> int | None:
    """
    Encontra o y-topo do cabeçalho 'Questão N' na saída do image_to_data.
    Retorna None se não encontrado.
    """
    textos = data["text"]
    tops   = data["top"]
    n_items = len(textos)

    for i, tok in enumerate(textos):
        if not tok:
            continue
        if re.match(r'QUEST[AÃ]O', tok.strip(), re.IGNORECASE):
            # Verifica se o próximo token não-vazio é o número
            for j in range(i + 1, min(i + 4, n_items)):
                prox = textos[j].strip()
                if prox == str(num):
                    return tops[i]
    return None


def encontrar_y_proxima_questao(data: dict, num_atual: int) -> int | None:
    """Encontra o y-topo da questão seguinte (num_atual+1 ou maior)."""
    textos = data["text"]
    tops   = data["top"]
    n_items = len(textos)

    for i, tok in enumerate(textos):
        if not tok:
            continue
        if re.match(r'QUEST[AÃ]O', tok.strip(), re.IGNORECASE):
            for j in range(i + 1, min(i + 4, n_items)):
                prox = textos[j].strip()
                if prox.isdigit() and int(prox) > num_atual:
                    return tops[i]
    return None


def extrair_regiao_questao(
    col_img: Image.Image,
    num: int,
    data: dict,
    margem_topo: int = 20,
) -> Image.Image | None:
    """
    Recorta a região da coluna que contém a questão N.
    Do cabeçalho da questão até o cabeçalho da próxima, ou fim da coluna.
    """
    y_inicio = encontrar_y_questao(data, num)
    if y_inicio is None:
        return None

    y_inicio = max(0, y_inicio - margem_topo)
    y_fim    = encontrar_y_proxima_questao(data, num)

    largura, altura = col_img.size
    if y_fim is None or y_fim <= y_inicio:
        y_fim = altura  # vai até o fim da coluna

    return col_img.crop((0, y_inicio, largura, y_fim))


def processar_dia(dia: str, targets: set) -> dict:
    """
    Varre todas as páginas do dia, extrai imagens das questões alvo.
    Retorna dict {num: path_relativo}.
    """
    caminho_pdf = os.path.join(PASTA_PROVAS, f"{dia}.pdf")
    if not os.path.exists(caminho_pdf):
        print(f"  ⚠️  {caminho_pdf} não encontrado")
        return {}

    pasta_dia = PASTA_IMAGENS / dia
    pasta_dia.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(caminho_pdf)
    n_pags = len(doc)
    print(f"  📄 {dia}.pdf — {n_pags} páginas")

    encontrados = {}
    pendentes   = set(targets)

    for pag_idx in range(n_pags):
        if not pendentes:
            break

        pag = doc[pag_idx]
        mat = fitz.Matrix(ZOOM, ZOOM)
        pix = pag.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        largura, altura = img.size
        meio = largura // 2
        mg   = int(largura * 0.01)

        colunas = [
            ("esq", img.crop((0,           0, meio + mg, altura))),
            ("dir", img.crop((meio - mg,   0, largura,  altura))),
        ]

        for nome_col, col_img in colunas:
            if not pendentes:
                break

            # OCR rápido para checar se algum alvo está nesta coluna
            txt_simples = ocr_col(col_img)

            alvos_aqui = set()
            for num in pendentes:
                if re.search(rf'QUEST[AÃ]O\s+{num}\b', txt_simples, re.IGNORECASE):
                    alvos_aqui.add(num)

            if not alvos_aqui:
                continue

            # OCR detalhado para obter bounding boxes
            print(f"     Pag {pag_idx+1} {nome_col}: encontrou Q{sorted(alvos_aqui)}")
            data = ocr_col_data(col_img)

            for num in alvos_aqui:
                regiao = extrair_regiao_questao(col_img, num, data)
                if regiao is None:
                    print(f"       ⚠️  Não conseguiu isolar a região de Q{num:03d}")
                    # Fallback: salva a coluna inteira
                    regiao = col_img

                nome_arq = f"q{num:03d}_1.jpg"
                caminho_saida = pasta_dia / nome_arq
                regiao.save(str(caminho_saida), "JPEG", quality=92)
                rel = f"2010/{dia}/{nome_arq}"
                encontrados[num] = rel
                pendentes.discard(num)
                print(f"       ✅ Q{num:03d} → {caminho_saida}")

    doc.close()

    if pendentes:
        print(f"  ⚠️  Não encontrou: Q{sorted(pendentes)}")

    return encontrados


def atualizar_json(encontrados_por_dia: dict):
    """Atualiza o JSON com os caminhos de imagem das questões extraídas."""
    with open(JSON_PATH, encoding="utf-8") as f:
        questoes = json.load(f)

    # Mapa rápido
    todas = {}
    for dia, enc in encontrados_por_dia.items():
        todas.update(enc)

    atualizadas = 0
    for q in questoes:
        num = q["numero"]
        if num in todas:
            img_rel = todas[num]
            if img_rel not in q.get("imagens", []):
                q.setdefault("imagens", []).insert(0, img_rel)
            q["tem_imagem"] = True
            atualizadas += 1

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    print(f"\n  JSON atualizado: {atualizadas} questões com nova imagem")


def main():
    print("=" * 60)
    print("  EXTRAÇÃO DE IMAGENS — QUESTÕES COM ALTERNATIVAS VISUAIS")
    print("=" * 60)

    todos_encontrados = {}

    for dia, targets in TARGETS.items():
        print(f"\n── {dia.upper()} — alvos: Q{sorted(targets)} ──")
        enc = processar_dia(dia, targets)
        todos_encontrados[dia] = enc

    print("\n── Atualizando JSON ──")
    atualizar_json(todos_encontrados)

    print("\n" + "=" * 60)
    print("  CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    main()
