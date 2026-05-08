"""
Completa o banco de questões ENEM com alternativas faltando.

Estratégia para cada questão com alternativas vazias:
1. Acha a questão no PDF pelos blocos de texto
2. Determina onde as alternativas começam:
   - Primeiro tenta: abaixo do último bloco de texto extractável
   - Fallback: 60% da região da questão
3. Renderiza em ~300 DPI e aplica OCR
4. Parseia A-E do resultado
5. Questões onde OCR falha → candidatas a imagens_alternativas

Uso:
  py completar_alternativas.py --ano 2011
  py completar_alternativas.py          # todos os anos
  py completar_alternativas.py --dry-run
"""

import json, re, os, sys, argparse
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ.setdefault("TESSDATA_PREFIX", r"C:\PROJETOS\HENRYJR\tessdata")

PASTA_PROVAS    = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_JSON      = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_PENDENTES = Path(r"C:\PROJETOS\HENRYJR\dados\pendentes_imagens")

ZOOM   = 300 / 72
LETRAS = "ABCDE"
ANOS_SKIP = {2010}
_OCR_CFG  = "--oem 1 --psm 6"


# ────────────────────────────────────────────────────────────────────────────
# Localizar questão no PDF
# ────────────────────────────────────────────────────────────────────────────

def encontrar_questao_pdf(doc, num: int):
    """Retorna (pag_idx, y_ini_pt, y_fim_pt, ultimo_bloco_y_bot_pt) ou None."""
    pat_curr = re.compile(rf"QUEST[AÃ]O\s+0*{num}\b", re.IGNORECASE)
    pat_prox = re.compile(rf"QUEST[AÃ]O\s+0*{num + 1}\b", re.IGNORECASE)

    for pag_idx in range(len(doc)):
        pag    = doc[pag_idx]
        blocos = pag.get_text("blocks")
        H      = pag.rect.height

        y_curr = y_prox = last_bot = None
        for b in blocos:
            btxt  = b[4].strip()
            y_top = b[1]
            y_bot = b[3]
            if pat_curr.match(btxt) and y_curr is None:
                y_curr = y_top
            if y_curr is not None and y_prox is None:
                if pat_prox.match(btxt):
                    y_prox = y_top
                    break
                # Registra o fundo do último bloco extractável (= acima das alts)
                if y_top >= y_curr:
                    last_bot = y_bot

        if y_curr is not None:
            y_fim = y_prox if y_prox else H
            return (pag_idx, y_curr, y_fim, last_bot)

    return None


def renderizar(doc, pag_idx, y_ini_pt, y_fim_pt):
    """Renderiza região (em pontos PDF) como PIL Image a ~300 DPI."""
    pag  = doc[pag_idx]
    clip = fitz.Rect(0, max(0, y_ini_pt - 2),
                     pag.rect.width, min(pag.rect.height, y_fim_pt + 4))
    mat  = fitz.Matrix(ZOOM, ZOOM)
    pix  = pag.get_pixmap(matrix=mat, clip=clip, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


# ────────────────────────────────────────────────────────────────────────────
# OCR e parsing de alternativas
# ────────────────────────────────────────────────────────────────────────────

def ocr(img: Image.Image) -> str:
    return pytesseract.image_to_string(img, lang="por", config=_OCR_CFG)


def limpar(txt: str) -> str:
    txt = re.sub(r"[^\S\n]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


_PT_WORDS = frozenset("""
a o de da do e em é no na um uma que para por com se ao os as não mas mais
seu sua ou há já bem pode são ser ter foi estar também como quando muito
isso tem pelo pela todo toda mesmo parte após onde entre sobre cada até
ele ela eles elas nos lhe lhes num numa pelos pelas dos das pelo à às
pela ser uma foi este esta esse essa aquele aquela dois duas três quatro
cinco seis sete oito nove dez sendo feita feito sendo usado sendo sendo
""".split())


def _coerente(alts: dict, min_pt: int = 3) -> bool:
    """
    Verifica se o conjunto de alternativas parece texto legível (não OCR garbage).
    Critérios:
    1. Nenhum token > 18 chars (garbage strings longas)
    2. Não mais de 45% de tokens de 1 char (diagramas/notações musicais)
    3. Pelo menos 2 das 5 alternativas contêm ao menos 1 palavra portuguesa comum
    """
    all_tokens = []
    for v in alts.values():
        all_tokens.extend(v.split())
    if not all_tokens:
        return False
    # Token muito longo = string garbage
    if any(len(t) > 18 for t in all_tokens):
        return False
    # Muitos tokens de 1 char = OCR de imagem (globalmente ou por alternativa)
    singles = sum(1 for t in all_tokens if len(t) == 1)
    if singles / len(all_tokens) > 0.45:
        return False
    for v in alts.values():
        toks = v.split()
        if len(toks) >= 4:
            s = sum(1 for t in toks if len(t) == 1)
            if s / len(toks) > 0.60:
                return False
    # Pelo menos 2 alternativas com pelo menos 1 palavra portuguesa comum
    pt_count = sum(
        1 for v in alts.values()
        if any(
            len(t) >= 3 and t.lower().rstrip(".,;:!?") in _PT_WORDS
            for t in v.split()
        )
    )
    if pt_count < min_pt:
        return False
    return True


def parsear_alternativas(txt: str, min_pt: int = 3) -> dict | None:
    """
    Tenta extrair A-E de um bloco de texto OCR das alternativas.
    Usa múltiplas heurísticas em cascata.
    """
    txt = limpar(txt)
    if not txt:
        return None

    # ── Heurística 1: "A)" "B)" ... ou "A." "B." na margem ──────────────────
    pat = re.compile(r"(?m)^[\s]{0,4}([A-E])[\.)\s]\s*(.{4,})")
    matches = pat.findall(txt)
    if len(matches) >= 5:
        alts = {}
        for letra, texto in matches[:5]:
            alts[letra] = re.sub(r"\s+", " ", texto.strip())
        if set(alts) == set(LETRAS) and _coerente(alts, min_pt):
            return alts

    # ── Heurística 2: dividir em partes por linha em branco ─────────────────
    partes = re.split(r"\n\s*\n", txt)
    partes = [p.strip() for p in partes if p.strip() and len(p.strip()) >= 4]
    if len(partes) == 5:
        alts = {LETRAS[i]: p for i, p in enumerate(partes)}
        if _coerente(alts, min_pt):
            return alts

    # ── Heurística 3: exatamente 5 linhas com conteúdo ≥ 5 chars ────────────
    linhas = [l.strip() for l in txt.split("\n") if l.strip() and len(l.strip()) >= 5]
    if len(linhas) == 5:
        alts = {LETRAS[i]: l for i, l in enumerate(linhas)}
        if _coerente(alts, min_pt):
            return alts

    # ── Heurística 4: pegar as primeiras 5 linhas longas ────────────────────
    if len(linhas) >= 5:
        candidatas = linhas[:5]
        if all(len(c) >= 5 for c in candidatas):
            alts = {LETRAS[i]: c for i, c in enumerate(candidatas)}
            if _coerente(alts, min_pt):
                return alts

    return None


# ────────────────────────────────────────────────────────────────────────────
# Processar questão
# ────────────────────────────────────────────────────────────────────────────

def processar_questao(doc, num: int, tem_imagem: bool = False):
    loc = encontrar_questao_pdf(doc, num)
    if loc is None:
        return {"status": "nao_encontrada"}

    pag_idx, y_ini_pt, y_fim_pt, last_bot_pt = loc
    alt_height_pt = y_fim_pt - y_ini_pt

    # Determinar y_start_pt das alternativas:
    # Usar o fundo do último bloco extractável + pequena margem.
    # Se não houver referência, usar 55% da altura.
    if last_bot_pt and last_bot_pt > y_ini_pt:
        y_alt_start_pt = last_bot_pt + 2   # 2pt de margem
    else:
        y_alt_start_pt = y_ini_pt + alt_height_pt * 0.55

    # Garantir que temos pelo menos 60pt de região para OCR
    if (y_fim_pt - y_alt_start_pt) < 40:
        y_alt_start_pt = y_ini_pt + alt_height_pt * 0.45

    # Renderizar só a região das alternativas
    img_alts = renderizar(doc, pag_idx, y_alt_start_pt, y_fim_pt)

    # OCR
    txt = ocr(img_alts)
    alts = parsear_alternativas(txt)

    if alts and len(alts) == 5 and all(len(v) >= 3 for v in alts.values()):
        return {"status": "texto_ocr", "alternativas": alts, "img": img_alts}

    # Segunda tentativa: renderizar mais acima (40% da região)
    y_alt_start2_pt = y_ini_pt + alt_height_pt * 0.40
    if y_alt_start2_pt < y_alt_start_pt - 10:
        img_alts2 = renderizar(doc, pag_idx, y_alt_start2_pt, y_fim_pt)
        txt2 = ocr(img_alts2)
        alts2 = parsear_alternativas(txt2)
        if alts2 and len(alts2) == 5 and all(len(v) >= 3 for v in alts2.values()):
            return {"status": "texto_ocr", "alternativas": alts2, "img": img_alts2}

    # Falhou → candidata a imagem visual
    img_full = renderizar(doc, pag_idx, y_ini_pt, y_fim_pt)
    return {"status": "candidata_imagem", "img": img_full}


# ────────────────────────────────────────────────────────────────────────────
# Loop por ano
# ────────────────────────────────────────────────────────────────────────────

def processar_ano(ano: int, dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"  ANO {ano}")
    print(f"{'='*60}")

    json_path = PASTA_JSON / f"enem_{ano}.json"
    if not json_path.exists():
        print(f"  JSON não encontrado")
        return []

    with open(json_path, encoding="utf-8") as f:
        questoes = json.load(f)

    candidatas = [q for q in questoes if not q.get("alternativas")]
    print(f"  Candidatas (alternativas vazias): {len(candidatas)}")
    if not candidatas:
        return []

    por_dia: dict[str, list] = {}
    for q in candidatas:
        por_dia.setdefault(q["dia"], []).append(q)

    stats    = {}
    pendentes = []

    for dia, qs in sorted(por_dia.items()):
        pdf_path = PASTA_PROVAS / str(ano) / f"{dia}.pdf"
        if not pdf_path.exists():
            print(f"  PDF não encontrado: {pdf_path.name}")
            continue

        print(f"\n  [{dia}] {len(qs)} questões")
        doc = fitz.open(str(pdf_path))

        for q in qs:
            num = q["numero"]
            tem_img = bool(q.get("tem_imagem") or q.get("imagens"))
            res = processar_questao(doc, num, tem_imagem=tem_img)
            status = res["status"]
            stats[status] = stats.get(status, 0) + 1

            if status == "texto_ocr":
                alts = res["alternativas"]
                print(f"    Q{num:03d} ✓  A={alts.get('A','')[:55]}")
                if not dry_run:
                    for qj in questoes:
                        if qj["numero"] == num:
                            qj["alternativas"] = alts
                            qj["confianca"] = max(float(qj.get("confianca") or 0), 0.6)
                            break

            elif status == "candidata_imagem":
                print(f"    Q{num:03d} ?  OCR falhou → candidata a imagem visual")
                pendentes.append({"ano": ano, "dia": dia, "numero": num})
                if not dry_run and res.get("img"):
                    d = PASTA_PENDENTES / str(ano) / dia
                    d.mkdir(parents=True, exist_ok=True)
                    res["img"].save(str(d / f"q{num:03d}_full.jpg"), "JPEG", quality=92)
            else:
                print(f"    Q{num:03d} ✗  não encontrada no PDF")

        doc.close()

    if not dry_run and stats.get("texto_ocr", 0) > 0:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(questoes, f, ensure_ascii=False, indent=2)
        print(f"\n  JSON salvo: {stats.get('texto_ocr',0)} questões atualizadas")

    print(f"  Resumo: {stats}")
    return pendentes


# ────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano",     type=int, help="Processar apenas este ano")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    PASTA_PENDENTES.mkdir(parents=True, exist_ok=True)

    anos = [args.ano] if args.ano else list(range(2009, 2025))
    anos = [a for a in anos if a not in ANOS_SKIP]

    todos_pendentes = []
    for ano in anos:
        p = processar_ano(ano, dry_run=args.dry_run)
        todos_pendentes.extend(p)

    if todos_pendentes and not args.dry_run:
        out = PASTA_JSON / "candidatas_imagens_alternativas.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(todos_pendentes, f, ensure_ascii=False, indent=2)
        print(f"\nCandidatas a imagens_alternativas ({len(todos_pendentes)}): {out}")

    print(f"\n{'='*60}\n  CONCLUÍDO\n{'='*60}")


if __name__ == "__main__":
    main()
