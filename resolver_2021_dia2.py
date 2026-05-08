"""
Localiza Q107, Q109 e Q169 no dia2.pdf de 2021 via OCR de página inteira.
O get_text() falha nessas páginas (texto corrompido/imagem); renderizamos
cada página, OCRizamos e buscamos o cabeçalho da questão no resultado.

Depois de localizar a questão, tenta extrair as alternativas normalmente.
Se OCR das alternativas falhar, salva imagem para inspeção manual.
"""

import json, re, sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ.setdefault("TESSDATA_PREFIX", r"C:\PROJETOS\HENRYJR\tessdata")

PASTA_PROVAS = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_JSON   = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_IMGS   = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")
PASTA_PEND   = Path(r"C:\PROJETOS\HENRYJR\dados\pendentes_imagens")

ZOOM     = 300 / 72       # ~300 DPI
ZOOM_SCN = 150 / 72       # ~150 DPI para scan rápido de página
LETRAS   = "ABCDE"

_PT_WORDS = frozenset("""
a o de da do e em é no na um uma que para por com se ao os as não mas mais
seu sua ou há já bem pode são ser ter foi estar também como quando muito
isso tem pelo pela todo toda mesmo parte após onde entre sobre cada até
ele ela eles elas nos lhe lhes num numa pelos pelas dos das pelo à às
pela ser uma foi este esta esse essa aquele aquela dois duas três quatro
cinco seis sete oito nove dez sendo feita feito sendo usado sendo sendo
""".split())


def _coerente(alts: dict, min_pt: int = 3) -> bool:
    all_tokens = []
    for v in alts.values():
        all_tokens.extend(v.split())
    if not all_tokens:
        return False
    if any(len(t) > 18 for t in all_tokens):
        return False
    singles = sum(1 for t in all_tokens if len(t) == 1)
    if singles / len(all_tokens) > 0.45:
        return False
    for v in alts.values():
        toks = v.split()
        if len(toks) >= 4:
            s = sum(1 for t in toks if len(t) == 1)
            if s / len(toks) > 0.60:
                return False
    pt_count = sum(
        1 for v in alts.values()
        if any(len(t) >= 3 and t.lower().rstrip(".,;:!?") in _PT_WORDS for t in v.split())
    )
    return pt_count >= min_pt


def renderizar(pag, y_ini_pt=None, y_fim_pt=None, zoom=ZOOM):
    H = pag.rect.height
    W = pag.rect.width
    y0 = max(0, (y_ini_pt or 0) - 2)
    y1 = min(H, (y_fim_pt or H) + 4)
    clip = fitz.Rect(0, y0, W, y1)
    mat  = fitz.Matrix(zoom, zoom)
    pix  = pag.get_pixmap(matrix=mat, clip=clip, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def ocr_texto(img: Image.Image) -> str:
    return pytesseract.image_to_string(img, lang="por", config="--oem 1 --psm 6")


def limpar(txt: str) -> str:
    txt = re.sub(r"[^\S\n]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def parsear_alternativas(txt: str) -> dict | None:
    txt = limpar(txt)
    if not txt:
        return None

    pat = re.compile(r"(?m)^[\s]{0,4}([A-E])[\.)\s]\s*(.{4,})")
    matches = pat.findall(txt)
    if len(matches) >= 5:
        alts = {}
        for letra, texto in matches[:5]:
            alts[letra] = re.sub(r"\s+", " ", texto.strip())
        if set(alts) == set(LETRAS) and _coerente(alts):
            return alts

    partes = re.split(r"\n\s*\n", txt)
    partes = [p.strip() for p in partes if p.strip() and len(p.strip()) >= 4]
    if len(partes) == 5:
        alts = {LETRAS[i]: p for i, p in enumerate(partes)}
        if _coerente(alts):
            return alts

    linhas = [l.strip() for l in txt.split("\n") if l.strip() and len(l.strip()) >= 5]
    if len(linhas) == 5:
        alts = {LETRAS[i]: l for i, l in enumerate(linhas)}
        if _coerente(alts):
            return alts

    if len(linhas) >= 5:
        alts = {LETRAS[i]: linhas[i] for i in range(5)}
        if _coerente(alts):
            return alts

    return None


def scan_pagina_ocr(pag):
    """OCR rápido da página inteira (150 DPI) para encontrar cabeçalhos."""
    img = renderizar(pag, zoom=ZOOM_SCN)
    return pytesseract.image_to_string(img, lang="por", config="--oem 1 --psm 6")


def localizar_questao_por_ocr(doc, num: int):
    """
    Escaneia cada página via OCR (150 DPI) buscando 'QUESTAO {num}' ou
    'Questao {num}'. Retorna (pag_idx, y_frac_ini, y_frac_fim) em fração
    da altura da página, aproximada pelo offset de linha no texto OCR.
    """
    pat_curr = re.compile(rf"QUEST[AÃ]O\s+0*{num}\b", re.IGNORECASE)
    pat_prox = re.compile(rf"QUEST[AÃ]O\s+0*{num + 1}\b", re.IGNORECASE)

    for pag_idx in range(len(doc)):
        pag = doc[pag_idx]
        txt = scan_pagina_ocr(pag)

        if not pat_curr.search(txt):
            continue

        print(f"    Página {pag_idx + 1}: encontrou Q{num} via OCR de página")

        # Usar OCR detalhado (por palavra) para estimar y
        img_150 = renderizar(pag, zoom=ZOOM_SCN)
        data = pytesseract.image_to_data(
            img_150, lang="por", config="--oem 1 --psm 6",
            output_type=pytesseract.Output.DICT,
        )

        H_img = img_150.height
        H_pt  = pag.rect.height
        scale = H_pt / H_img   # pts por pixel 150dpi

        # Achar y_pt do cabeçalho da questão atual e próxima
        n_words = len(data["text"])
        y_curr = y_prox = None

        # Concatenar palavras por linha para detectar padrão multi-token
        linhas_por_y: dict[int, list] = {}
        for i in range(n_words):
            conf = int(data["conf"][i])
            if conf < 0:
                continue
            top = data["top"][i]
            linhas_por_y.setdefault(top, []).append((i, data["text"][i]))

        for top_y in sorted(linhas_por_y):
            linha_txt = " ".join(t for _, t in linhas_por_y[top_y])
            if pat_curr.search(linha_txt) and y_curr is None:
                y_curr = int(top_y * scale)
            if y_curr is not None and pat_prox.search(linha_txt) and y_prox is None:
                y_prox = int(top_y * scale)
                break

        if y_curr is None:
            # Estimativa: questão ocupa metade inferior da página
            y_curr = int(H_pt * 0.5)
            y_prox = H_pt
            print(f"    AVISO: y exato não encontrado — usando estimativa")

        y_fim = y_prox if y_prox else H_pt
        print(f"    y_curr={y_curr:.0f}pt  y_fim={y_fim:.0f}pt  (de {H_pt:.0f}pt)")
        return (pag_idx, y_curr, y_fim)

    return None


def processar_questao_2021(doc, num: int, pasta_saida: Path):
    loc = localizar_questao_por_ocr(doc, num)
    if loc is None:
        print(f"    Q{num:03d} ✗  não encontrada (OCR de página também falhou)")
        return None

    pag_idx, y_ini, y_fim = loc
    pag = doc[pag_idx]
    alt_height = y_fim - y_ini

    # Tentativa 1: seção inferior (60%)
    y_alt = y_ini + alt_height * 0.60
    img1  = renderizar(pag, y_alt, y_fim)
    txt1  = ocr_texto(img1)
    alts  = parsear_alternativas(txt1)
    if alts:
        print(f"    Q{num:03d} ✓  via OCR (tentativa 1)  A={alts.get('A','')[:55]}")
        return {"status": "texto_ocr", "alternativas": alts}

    # Tentativa 2: seção inferior mais ampla (40%)
    y_alt2 = y_ini + alt_height * 0.40
    img2   = renderizar(pag, y_alt2, y_fim)
    txt2   = ocr_texto(img2)
    alts2  = parsear_alternativas(txt2)
    if alts2:
        print(f"    Q{num:03d} ✓  via OCR (tentativa 2)  A={alts2.get('A','')[:55]}")
        return {"status": "texto_ocr", "alternativas": alts2}

    # Falhou → salva imagem completa da questão para inspeção
    img_full = renderizar(pag, y_ini, y_fim)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    out_path = pasta_saida / f"q{num:03d}_full.jpg"
    img_full.save(str(out_path), "JPEG", quality=92)
    print(f"    Q{num:03d} ?  OCR de alternativas falhou → {out_path.name}")
    return {"status": "candidata_imagem"}


def main():
    ano  = 2021
    dia  = "dia2"
    nums = [107, 109, 169]

    pdf_path  = PASTA_PROVAS / str(ano) / f"{dia}.pdf"
    json_path = PASTA_JSON / f"enem_{ano}.json"
    pasta_out = PASTA_PEND / str(ano) / dia

    print("=" * 60)
    print(f"  RESOLVER 2021 dia2 — Q107, Q109, Q169")
    print("=" * 60)

    doc = fitz.open(str(pdf_path))
    with open(json_path, encoding="utf-8") as f:
        questoes = json.load(f)

    atualizados = 0

    for num in nums:
        print(f"\n  Procurando Q{num:03d}...")
        res = processar_questao_2021(doc, num, pasta_out)
        if res and res["status"] == "texto_ocr":
            for q in questoes:
                if q["numero"] == num:
                    q["alternativas"] = res["alternativas"]
                    q["confianca"]    = max(float(q.get("confianca") or 0), 0.65)
                    atualizados += 1
                    break

    doc.close()

    if atualizados > 0:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(questoes, f, ensure_ascii=False, indent=2)
        print(f"\n  JSON salvo: {atualizados} questões atualizadas")

    print(f"\n{'='*60}\n  CONCLUÍDO\n{'='*60}")


if __name__ == "__main__":
    main()
