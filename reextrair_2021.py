"""
Re-extração do ENEM 2021 via OCR (PyMuPDF + Tesseract).

O PDF de 2021 usa fonte customizada que impede extração de texto normal.
Esta abordagem renderiza cada página a 300 DPI e usa Tesseract (Portuguese)
para recuperar o texto.

Estrutura especial dia1:
  - Q001–Q005 versão inglês  (opção inglês)
  - Q001–Q005 versão espanhol (opção espanhol)
  - Q006–Q090 questões comuns

O v1 armazena as 95 entradas de dia1 nessa ordem exata.
Usamos contagem de ocorrências para mapear OCR → v1.

Preserva do JSON v1: gabarito, area, dia, imagens/tem_imagem, revisado/confianca.
Saída: dados/json_v2/enem_2021.json
"""

import json, os, re, sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Configuração Tesseract ────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\PROJETOS\HENRYJR\tessdata"

PASTA_PROVAS  = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_JSON    = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_JSON_V1 = Path(r"C:\PROJETOS\HENRYJR\dados\json")

ZOOM     = 300 / 72
TESS_CFG = "--psm 1 --oem 1"

PAT_Q = re.compile(r"Quest[aã]o\s+0*(\d{1,3})\b", re.IGNORECASE)

LIXO_PATS = [
    re.compile(r"enem.*?202[01]", re.IGNORECASE),
    re.compile(r"Exame Nacional do Ensino M"),
    re.compile(r"Quest[oõ]es de \d+ a \d+"),
    re.compile(r"\bLC\b.*\bdia\b", re.IGNORECASE),
    re.compile(r"\bCN\b.*\bdia\b", re.IGNORECASE),
    re.compile(r"\bCH\b.*\bdia\b", re.IGNORECASE),
    re.compile(r"\bMT\b.*\bdia\b", re.IGNORECASE),
    re.compile(r"caderno\s+\d+\s*[-–]", re.IGNORECASE),
    re.compile(r"LINGUAGENS,?\s+C[ÓO]DIGOS", re.IGNORECASE),
    re.compile(r"CI[EÊ]NCIAS\s+(DA|HUMANAS)", re.IGNORECASE),
    re.compile(r"MATEM[ÁA]TICA\s+E\s+SUAS", re.IGNORECASE),
    re.compile(r"^\s*[\*\|\(\)]{2,}"),           # barcodes
    re.compile(r"^\s*[\dO\s]{6,}\s*$"),            # só dígitos/O
]


# ── OCR ───────────────────────────────────────────────────────────────────────

def ocr_pdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    partes = []
    n = len(doc)
    for i, pag in enumerate(doc):
        mat = fitz.Matrix(ZOOM, ZOOM)
        pix = pag.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        texto = pytesseract.image_to_string(img, lang="por", config=TESS_CFG)
        partes.append(texto)
        print(f"    OCR página {i+1}/{n}...", end="\r")
    doc.close()
    print()
    return "\n".join(partes)


# ── Limpeza ───────────────────────────────────────────────────────────────────

def _e_lixo(linha: str) -> bool:
    s = linha.strip()
    if not s:
        return False   # linhas em branco são separadores de parágrafo — preservar
    if len(s) < 3:
        return True
    for pat in LIXO_PATS:
        if pat.search(s):
            return True
    alpha = sum(1 for c in s if c.isalnum() or c.isspace())
    return alpha / len(s) < 0.4


# ── Divisão por questão (ordenada, preserva duplicatas) ───────────────────────

def dividir_questoes(texto: str) -> list[tuple[int, list[str]]]:
    """
    Retorna lista ORDENADA de (num, linhas) incluindo questões com número
    repetido (versão inglês e espanhol de Q001-Q005).
    """
    resultado: list[tuple[int, list[str]]] = []
    atual_num: int | None = None
    atual_linhas: list[str] = []

    for linha in texto.splitlines():
        m = PAT_Q.match(linha.strip())
        if m:
            if atual_num is not None:
                resultado.append((atual_num, atual_linhas))
            atual_num = int(m.group(1))
            atual_linhas = []
        elif atual_num is not None:
            if not _e_lixo(linha):
                atual_linhas.append(linha)

    if atual_num is not None:
        resultado.append((atual_num, atual_linhas))

    return resultado


# ── Parsing de alternativas / enunciado ──────────────────────────────────────

def _e_conteudo(linha: str) -> bool:
    s = linha.strip()
    if len(s) < 8:
        return False
    # Linhas sem espaço são barcodes/símbolos (ex.: CoOÇGoOS, LC1ºdia)
    if " " not in s:
        return False
    alpha = sum(1 for c in s if c.isalnum() or c.isspace())
    return alpha / len(s) >= 0.5


def _limpar_alt(texto: str) -> str:
    """
    Remove prefixo de bolinha OCR mal lida (ex.: 'O texto...' → 'texto...')
    apenas quando o caractere antes do espaço não forma frase gramatical.
    Só strip se: linha começa com 'O ' + minúscula (artigo errado/bolinha OCR).
    """
    m = re.match(r"^O\s+([a-z])", texto)
    if m:
        return texto[texto.index(" ") + 1:]
    return texto


def extrair_alternativas(linhas: list[str]) -> tuple[list[str], dict]:
    """
    Coleta as últimas 5 linhas de conteúdo como alternativas A-E.
    Retorna (linhas_restantes, {A:..., B:..., C:..., D:..., E:...}).
    """
    letras = list("ABCDE")
    conteudo = [ln for ln in linhas if _e_conteudo(ln)]

    if len(conteudo) < 5:
        return linhas, {}

    candidatas = conteudo[-5:]
    alts = {letras[i]: _limpar_alt(candidatas[i].strip()) for i in range(5)}

    # Encontrar índice da primeira alternativa nas linhas originais
    n_encontradas = 0
    corte = -1
    for i in range(len(linhas) - 1, -1, -1):
        if _e_conteudo(linhas[i]):
            n_encontradas += 1
            if n_encontradas == 5:
                corte = i
                break

    restantes = linhas[:corte] if corte >= 0 else linhas
    return restantes, alts


def agrupar_paragrafos(linhas: list[str]) -> list[str]:
    pars: list[str] = []
    atual: list[str] = []
    for ln in linhas:
        if ln.strip():
            atual.append(ln.strip())
        else:
            if atual:
                pars.append(" ".join(atual))
                atual = []
    if atual:
        pars.append(" ".join(atual))
    return [p for p in pars if len(p.strip()) >= 3]


def parsear_questao(num: int, linhas: list[str]) -> dict:
    restantes, alts = extrair_alternativas(linhas)
    pars = agrupar_paragrafos(restantes)

    if not pars:
        return {"enunciado": [], "comando": "", "alternativas": alts}

    return {
        "enunciado":    pars[:-1],
        "comando":      pars[-1],
        "alternativas": alts,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  RE-EXTRAÇÃO 2021 — OCR via Tesseract/Portuguese")
    print("=" * 68)

    v1_path = PASTA_JSON_V1 / "enem_2021.json"
    with open(v1_path, encoding="utf-8") as f:
        v1 = json.load(f)
    print(f"  v1 carregado: {len(v1)} questões")

    questoes_out: list[dict] = []

    for dia in ["dia1", "dia2"]:
        pdf_path = PASTA_PROVAS / "2021" / f"{dia}.pdf"
        if not pdf_path.exists():
            print(f"  [AVISO] PDF não encontrado: {pdf_path}")
            continue

        print(f"\n  ── {dia} ──")
        print("  OCR em andamento...")
        texto_ocr = ocr_pdf(pdf_path)

        blocos_ocr = dividir_questoes(texto_ocr)  # lista ordenada (num, linhas)
        print(f"  OCR detectou {len(blocos_ocr)} blocos de questão")

        # Índice de busca: num → lista de índices em blocos_ocr
        ocr_index: dict[int, list[int]] = {}
        for idx, (num, _) in enumerate(blocos_ocr):
            ocr_index.setdefault(num, []).append(idx)

        # Processar questões do v1 em ordem
        v1_dia = [q for q in v1 if q.get("dia") == dia]
        num_counter: dict[int, int] = {}

        for v1q in v1_dia:
            num = v1q["numero"]
            occ = num_counter.get(num, 0)
            num_counter[num] = occ + 1

            # Buscar o bloco OCR correspondente (pela ocorrência)
            ocr_idxs = ocr_index.get(num, [])
            if occ < len(ocr_idxs):
                _, ocr_linhas = blocos_ocr[ocr_idxs[occ]]
                parsed = parsear_questao(num, ocr_linhas)
            else:
                parsed = {"enunciado": [], "comando": "", "alternativas": {}}
                print(f"    Q{num:03d} (ocorrência {occ+1}): não encontrado no OCR")

            q = {
                "numero":       num,
                "ano":          2021,
                "dia":          dia,
                "area":         v1q.get("area", ""),
                "enunciado":    parsed["enunciado"],
                "comando":      parsed["comando"],
                "alternativas": parsed["alternativas"],
                "gabarito":     v1q.get("gabarito"),
                "confianca":    v1q.get("confianca", 0.9),
                "revisado":     v1q.get("revisado", False),
                "imagens":      v1q.get("imagens") or [],
                "tem_imagem":   v1q.get("tem_imagem", False),
            }
            questoes_out.append(q)

        # Resumo do dia
        n_cmd  = sum(1 for q in questoes_out if q["dia"] == dia and q.get("comando","").strip())
        n_alts = sum(1 for q in questoes_out if q["dia"] == dia and q.get("alternativas"))
        print(f"  {dia}: {len(v1_dia)} questões  com_cmd={n_cmd}  com_alts={n_alts}")

    out_path = PASTA_JSON / "enem_2021.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(questoes_out, f, ensure_ascii=False, indent=2)

    n_cmd  = sum(1 for q in questoes_out if q.get("comando","").strip())
    n_alts = sum(1 for q in questoes_out if q.get("alternativas"))
    n_gab  = sum(1 for q in questoes_out if q.get("gabarito"))
    print(f"\n  Salvo: {out_path}")
    print(f"  Total: {len(questoes_out)}  cmd={n_cmd}  alts={n_alts}  gab={n_gab}")
    print("=" * 68)


if __name__ == "__main__":
    main()
