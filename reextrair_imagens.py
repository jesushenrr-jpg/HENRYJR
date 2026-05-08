"""
Reextração de imagens ENEM 2009-2024 por renderização de página.

Abordagem:
  - Detecta blocos de imagem raster via get_text("dict") type==1
  - Exige sobreposição mínima de 30pt para associar imagem à questão
    (evita captura de bordas de imagens de questões vizinhas em layout 2 colunas)
  - Renderiza a região completa (union bbox + padding) a 300 DPI via page.get_pixmap()
  - Salva como JPEG qualidade 92

Resolve:
  ✓ Imagens em negativo  → page.get_pixmap() renderiza corretamente (não extrai bytes crus)
  ✓ Tirinhas cortadas    → captura a union de TODOS os blocos como 1 imagem por questão
  ✓ .jpx pretos (2009)   → renderização nativa do PyMuPDF decodifica JPX corretamente
  ✓ Barcodes             → filtro por proporção (w<=70pt, h>=150pt)
  ✓ Falsos positivos col → sobreposição mínima de 30pt filtra vazamentos do layout 2 col

Fases:
  1. Limpa imagens existentes (disco + referências nos JSONs)
  2. Extrai imagens de cada PDF ano/dia
  3. Atualiza JSONs com novos caminhos
"""

import json, re, sys, shutil
from pathlib import Path
from collections import defaultdict

import fitz
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Constantes ────────────────────────────────────────────────────────────────
PASTA_PROVAS = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_JSON   = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_IMG    = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")

ZOOM        = 300 / 72   # 300 DPI
JPEG_Q      = 92
PAD_PT      = 12         # padding ao redor da zona (pontos PDF)
MIN_FILL    = 0.012      # fração mínima de pixels não-brancos para aceitar zona
BC_W        = 70         # barcode: largura máxima (pt)
BC_H        = 150        # barcode: altura mínima (pt)
TINY        = 20         # min(w,h) mínimo — filtra bullets e ícones decorativos (pt)
MIN_OVERLAP = 30         # sobreposição mínima (pt) para associar imagem à questão

PAT_Q = re.compile(r"QUEST.O\s+0*(\d{1,3})\b", re.IGNORECASE)


# ── Mapeamento de questões no PDF ─────────────────────────────────────────────
def mapear_questoes(doc) -> dict[int, tuple[int, float, float]]:
    """Retorna {num: (pag_idx, y_start, y_end)} para todas as questões no PDF."""
    items = []

    for pi in range(len(doc)):
        pag = doc[pi]
        for blk in pag.get_text("dict")["blocks"]:
            if blk.get("type") != 0:
                continue
            txt = " ".join(
                sp.get("text", "")
                for ln in blk.get("lines", [])
                for sp in ln.get("spans", [])
            )
            m = PAT_Q.search(txt)
            if m:
                num = int(m.group(1))
                items.append((pi, blk["bbox"][1], num))

    if not items:
        return {}

    items.sort(key=lambda x: (x[0], x[1]))

    seen, unique = set(), []
    for it in items:
        if it[2] not in seen:
            seen.add(it[2])
            unique.append(it)

    result = {}
    for i, (pi, y0, num) in enumerate(unique):
        if i + 1 < len(unique):
            np_, ny, _ = unique[i + 1]
            y_end = ny if np_ == pi else doc[pi].rect.height
        else:
            y_end = doc[pi].rect.height
        result[num] = (pi, y0, y_end)

    return result


# ── Detecção de imagens raster ────────────────────────────────────────────────
def _ok(r: fitz.Rect, y0: float, y1: float) -> bool:
    """True se o rect é válido e tem sobreposição suficiente com [y0, y1]."""
    if r.width <= BC_W and r.height >= BC_H:
        return False   # barcode
    if min(r.width, r.height) < TINY:
        return False   # elemento decorativo minúsculo
    # Sobreposição mínima com a região da questão
    overlap = min(r.y1, y1) - max(r.y0, y0)
    return overlap >= MIN_OVERLAP


def zona_imagem(pag, y0: float, y1: float) -> "fitz.Rect | None":
    """
    Determina a zona de imagem raster na região [y0, y1].
    Usa get_text('dict') type==1 que reporta posições visíveis (após clipping).
    Retorna fitz.Rect (union + padding) ou None.
    """
    rects = []
    for blk in pag.get_text("dict")["blocks"]:
        if blk.get("type") != 1:
            continue
        r = fitz.Rect(blk["bbox"])
        if r.y1 <= y0 or r.y0 >= y1:
            continue
        if _ok(r, y0, y1):
            rects.append(r)

    if not rects:
        return None

    W = pag.rect.width
    ux0 = max(0,  min(r.x0 for r in rects) - PAD_PT)
    uy0 = max(y0, min(r.y0 for r in rects) - PAD_PT)
    ux1 = min(W,  max(r.x1 for r in rects) + PAD_PT)
    uy1 = min(y1, max(r.y1 for r in rects) + PAD_PT)
    zona = fitz.Rect(ux0, uy0, ux1, uy1)
    return zona if zona.height >= 5 and zona.width >= 5 else None


# ── Renderização ──────────────────────────────────────────────────────────────
def tem_conteudo(pag, zona: fitz.Rect) -> bool:
    """Renderiza a zona em 72 DPI e verifica fração de pixels não-brancos."""
    try:
        pix = pag.get_pixmap(matrix=fitz.Matrix(1, 1), clip=zona, alpha=False)
        if pix.width < 2 or pix.height < 2:
            return False
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        return float((arr.min(axis=2) < 248).mean()) >= MIN_FILL
    except Exception:
        return False


def renderizar(pag, zona: fitz.Rect) -> "Image.Image | None":
    """Renderiza a zona a 300 DPI. Retorna None se sem conteúdo visual."""
    if not tem_conteudo(pag, zona):
        return None
    try:
        mat = fitz.Matrix(ZOOM, ZOOM)
        pix = pag.get_pixmap(matrix=mat, clip=zona, alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    except Exception as e:
        print(f"      ERRO render: {e}")
        return None


# ── Processamento por PDF ─────────────────────────────────────────────────────
def processar_pdf(ano: int, dia: str, questoes: list) -> dict:
    """
    Extrai imagens do PDF para as questões do dia.
    Modifica questoes in-place. Retorna estatísticas.
    """
    pdf = PASTA_PROVAS / str(ano) / f"{dia}.pdf"
    if not pdf.exists():
        return {"sem_pdf": 1}

    qs = [q for q in questoes if q.get("dia") == dia]
    stats: dict[str, int] = defaultdict(int)
    stats["total"] = len(qs)

    try:
        doc = fitz.open(str(pdf))
    except Exception as e:
        print(f"    ERRO ao abrir PDF: {e}")
        return {"erro": 1}

    mapa = mapear_questoes(doc)
    print(f"    {len(qs)} questões / {len(mapa)} localizadas no PDF")

    pasta = PASTA_IMG / str(ano) / dia
    pasta.mkdir(parents=True, exist_ok=True)

    for q in qs:
        num = q["numero"]
        q["imagens"] = []
        q["tem_imagem"] = False

        if num not in mapa:
            stats["nao_loc"] += 1
            continue

        pi, y0, y1 = mapa[num]
        pag = doc[pi]

        zona = zona_imagem(pag, y0, y1)
        if zona is None:
            stats["sem_img"] += 1
            continue

        img = renderizar(pag, zona)
        if img is None:
            stats["vazia"] += 1
            continue

        rel = f"{ano}/{dia}/q{num:03d}_1.jpg"
        out = PASTA_IMG / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out), "JPEG", quality=JPEG_Q)

        q["imagens"] = [rel]
        q["tem_imagem"] = True
        stats["salvas"] += 1
        print(f"      Q{num:03d} ✓  {img.width}×{img.height}px")

    doc.close()
    return dict(stats)


# ── Limpeza ───────────────────────────────────────────────────────────────────
def limpar():
    """Remove todas as imagens do disco e limpa referências nos JSONs."""
    print("Limpando disco...")
    if PASTA_IMG.exists():
        n = sum(1 for f in PASTA_IMG.rglob("*") if f.is_file())
        shutil.rmtree(PASTA_IMG)
        print(f"  {n} arquivos removidos")
    PASTA_IMG.mkdir(parents=True, exist_ok=True)

    print("Limpando JSONs...")
    for jp in sorted(PASTA_JSON.glob("enem_*.json")):
        with open(jp, encoding="utf-8") as f:
            qs = json.load(f)
        for q in qs:
            q["imagens"] = []
            q["tem_imagem"] = False
            q.pop("imagens_alternativas", None)
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(qs, f, ensure_ascii=False, indent=2)
        print(f"  {jp.name}: {len(qs)} questões limpas")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 72)
    print("  REEXTRAÇÃO DE IMAGENS ENEM 2009-2024")
    print("=" * 72)

    print("\n── FASE 1: LIMPEZA ──────────────────────────────────────────────────")
    limpar()

    print("\n── FASE 2: EXTRAÇÃO ─────────────────────────────────────────────────")

    total: dict[str, int] = defaultdict(int)

    for ano in range(2009, 2025):
        jp = PASTA_JSON / f"enem_{ano}.json"
        if not jp.exists():
            continue

        with open(jp, encoding="utf-8") as f:
            questoes = json.load(f)

        for dia in ["dia1", "dia2"]:
            print(f"\n  {ano} / {dia}")
            stats = processar_pdf(ano, dia, questoes)
            for k, v in stats.items():
                total[k] += v
            print(f"  → salvas={stats.get('salvas', 0)}  "
                  f"sem_img={stats.get('sem_img', 0)}  "
                  f"nao_loc={stats.get('nao_loc', 0)}")

        with open(jp, "w", encoding="utf-8") as f:
            json.dump(questoes, f, ensure_ascii=False, indent=2)
        print(f"  JSON salvo: {jp.name}")

    print(f"\n{'=' * 72}")
    print(f"  RESULTADO FINAL:")
    print(f"    imagens salvas  : {total.get('salvas', 0)}")
    print(f"    sem imagem      : {total.get('sem_img', 0)}")
    print(f"    não localizadas : {total.get('nao_loc', 0)}")
    print(f"    zonas vazias    : {total.get('vazia', 0)}")
    print(f"    PDFs ausentes   : {total.get('sem_pdf', 0)}")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
