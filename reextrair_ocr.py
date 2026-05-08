"""
Re-extracao de qualquer ano ENEM via OCR (PyMuPDF + Tesseract).

Usado para anos cujo PDF tem fonte customizada que impede extracao de texto
normal (confirmados: 2010, 2021). Ver diagnostico_2010.md para detalhes.

Uso:
    python reextrair_ocr.py 2010
    python reextrair_ocr.py 2021

Preserva do JSON v1: gabarito, area, dia, imagens/tem_imagem.

Estrutura especial do 2021 (dia1):
    - Q001-Q005 versao ingles + Q001-Q005 versao espanhol (95 entradas no v1)
    - Tratado via contagem de ocorrencias para mapear OCR -> v1.

Pos-processamento aplicado automaticamente:
    - Regra do penultimo ponto (corrigir_enunciados.py) para questoes onde
      enunciado ficou vazio mas o comando tem multiplas frases.
"""

import json, os, re, sys
from pathlib import Path
from collections import defaultdict

import fitz
import pytesseract
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Configuracao -------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\PROJETOS\HENRYJR\tessdata"

PASTA_PROVAS  = Path(r"C:\PROJETOS\HENRYJR\dados\PROVAS")
PASTA_JSON_V2 = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_JSON_V1 = Path(r"C:\PROJETOS\HENRYJR\dados\json")

ZOOM     = 300 / 72
TESS_CFG = "--psm 1 --oem 1"

PAT_Q    = re.compile(r"Quest.o\s+0*(\d{1,3})\b", re.IGNORECASE)
PAT_FIM  = re.compile(r"[.!?](?=\s+[A-Z\xc0-\xff]|\s*$)")
PAT_ABRV = re.compile(
    r"\b(Art|Fig|Pag|pag|vol|Vol|op|cit|Dr|Dra|Sr|Sra|Prof|Profa|"
    r"ed|Ed|cap|Cap|sec|Sec|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.",
    re.IGNORECASE,
)

# Padroes de linhas que sao cabecalhos/rodapes/barcodes -- filtrados
LIXO_PATS = [
    re.compile(r"enem.*?20\d{2}", re.IGNORECASE),
    re.compile(r"Exame Nacional do Ensino M"),
    re.compile(r"Quest[oo]es de \d+ a \d+"),
    re.compile(r"\b(LC|CN|CH|MT)\b.*\bdia\b", re.IGNORECASE),
    re.compile(r"caderno\s+\d+\s*[-]", re.IGNORECASE),
    re.compile(r"LINGUAGENS,?\s+C[OO]DIGOS", re.IGNORECASE),
    re.compile(r"CI[EE]NCIAS\s+(DA\s+NATUREZA|HUMANAS)", re.IGNORECASE),
    re.compile(r"MATEM[AA]TICA\s+E\s+SUAS", re.IGNORECASE),
    re.compile(r"^\s*[\*\|\(\)]{2,}"),
    re.compile(r"^\s*[\dO\s]{6,}\s*$"),
]


# -- OCR ----------------------------------------------------------------------

def ocr_pdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    n = len(doc)
    partes = []
    for i, pag in enumerate(doc):
        mat = fitz.Matrix(ZOOM, ZOOM)
        pix = pag.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        partes.append(pytesseract.image_to_string(img, lang="por", config=TESS_CFG))
        print(f"    OCR pagina {i+1}/{n}...", end="\r")
    doc.close()
    print()
    return "\n".join(partes)


# -- Filtragem de linhas ------------------------------------------------------

def _e_lixo(linha: str) -> bool:
    s = linha.strip()
    if not s:
        return False   # linhas em branco sao separadores de paragrafo
    if len(s) < 3:
        return True
    for pat in LIXO_PATS:
        if pat.search(s):
            return True
    alpha = sum(1 for c in s if c.isalnum() or c.isspace())
    return alpha / len(s) < 0.4


# -- Divisao por questao ------------------------------------------------------

def dividir_questoes(texto: str) -> list[tuple[int, list[str]]]:
    """Lista ordenada de (num_questao, linhas), preservando duplicatas."""
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
            s = linha.strip()
            if not s:
                atual_linhas.append("")          # preserva separador de paragrafo
            elif not _e_lixo(linha):
                atual_linhas.append(linha)

    if atual_num is not None:
        resultado.append((atual_num, atual_linhas))

    return resultado


# -- Parsing de alternativas --------------------------------------------------

# Bolinha OCR: circulo (bolinha) lido como O ou OQ, seguido de letra
_BOLINHA = re.compile(r"^O[Q]?\s+[A-Za-z]")


def _e_conteudo(linha: str) -> bool:
    s = linha.strip()
    if len(s) < 8:
        return False
    if " " not in s:
        return False
    alpha = sum(1 for c in s if c.isalnum() or c.isspace())
    return alpha / len(s) >= 0.5


def _limpar_alt(texto: str) -> str:
    """Remove prefixo de bolinha OCR ('O ' ou 'OQ ') — circulo mal lido pelo Tesseract."""
    m = re.match(r"^O[Q]?\s+", texto)
    if m:
        return texto[m.end():]
    return texto


def _encontrar_inicio_alts(pars: list[str]) -> int:
    """
    Busca o ultimo grupo de 5 paragrafos consecutivos iniciando com padrao de bolinha.
    Retorna o indice do primeiro paragrafo das alternativas, ou -1 se nao encontrado.
    """
    n = len(pars)
    for i in range(n - 5, -1, -1):
        if all(_BOLINHA.match(pars[i + j]) for j in range(5)):
            return i
    return -1


def extrair_alternativas(linhas: list[str]) -> tuple[list[str], dict]:
    """Fallback: ultimas 5 linhas de conteudo (alternativas de 1 linha sem bolinha)."""
    letras = list("ABCDE")
    conteudo = [ln for ln in linhas if _e_conteudo(ln)]
    if len(conteudo) < 5:
        return linhas, {}

    candidatas = conteudo[-5:]
    alts = {letras[i]: _limpar_alt(candidatas[i].strip()) for i in range(5)}

    n_enc, corte = 0, -1
    for i in range(len(linhas) - 1, -1, -1):
        if _e_conteudo(linhas[i]):
            n_enc += 1
            if n_enc == 5:
                corte = i
                break

    return linhas[:corte] if corte >= 0 else linhas, alts


# -- Agrupamento em paragrafos ------------------------------------------------

def agrupar_paragrafos(linhas: list[str]) -> list[str]:
    pars, atual = [], []
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


# -- Regra do penultimo ponto (fallback) -------------------------------------

def _fins_de_frase(texto: str) -> list[int]:
    pos = []
    for m in PAT_FIM.finditer(texto):
        trecho = texto[max(0, m.start() - 10): m.start()]
        if PAT_ABRV.search(trecho):
            continue
        pos.append(m.end())
    return pos


def separar_pelo_penultimo_ponto(texto: str) -> tuple[list[str], str]:
    fins = _fins_de_frase(texto)
    if len(fins) < 2:
        return [], texto.strip()
    split_pos = fins[-2]
    enun = texto[:split_pos].strip()
    cmd  = texto[split_pos:].strip()
    return ([enun] if enun else []), cmd


# -- Parsing completo de uma questao -----------------------------------------

def parsear_questao(linhas: list[str]) -> dict:
    pars = agrupar_paragrafos(linhas)

    if not pars:
        return {"enunciado": [], "comando": "", "alternativas": {}}

    # Estrategia 1: bolinhas em paragrafos (alternativas multi-linha separadas por blancos)
    corte = _encontrar_inicio_alts(pars)
    if corte >= 0:
        alts_pars = pars[corte:corte + 5]
        resto = pars[:corte]
        alts = {l: _limpar_alt(alts_pars[i]) for i, l in enumerate("ABCDE")}
    else:
        # Estrategia 2: ultimas 5 linhas de conteudo (alternativas 1-linha sem bolinha)
        resto_linhas, alts = extrair_alternativas(linhas)
        resto = agrupar_paragrafos(resto_linhas)

    if not resto:
        return {"enunciado": [], "comando": "", "alternativas": alts}

    if len(resto) == 1:
        enun_pars, cmd = separar_pelo_penultimo_ponto(resto[0])
    else:
        enun_pars = resto[:-1]
        cmd       = resto[-1]

    return {"enunciado": enun_pars, "comando": cmd, "alternativas": alts}


# -- Processamento por ano/dia ------------------------------------------------

def processar_ano(ano: int) -> None:
    v1_path = PASTA_JSON_V1 / f"enem_{ano}.json"
    if not v1_path.exists():
        print(f"  [ERRO] JSON v1 nao encontrado: {v1_path}")
        return

    with open(v1_path, encoding="utf-8") as f:
        v1 = json.load(f)

    questoes_out: list[dict] = []

    for dia in ["dia1", "dia2"]:
        pdf_path = PASTA_PROVAS / str(ano) / f"{dia}.pdf"
        if not pdf_path.exists():
            print(f"  [AVISO] PDF nao encontrado: {pdf_path}")
            for v1q in v1:
                if v1q.get("dia") == dia:
                    questoes_out.append(_q_vazia(v1q, ano, dia))
            continue

        print(f"\n  -- {ano}/{dia} ({pdf_path.name}) --")
        print("  OCR em andamento...")
        texto_ocr = ocr_pdf(pdf_path)

        blocos = dividir_questoes(texto_ocr)
        print(f"  OCR detectou {len(blocos)} blocos de questao")

        # Indice: num -> lista de posicoes em blocos (para duplicatas do 2021)
        idx_map: dict[int, list[int]] = {}
        for i, (num, _) in enumerate(blocos):
            idx_map.setdefault(num, []).append(i)

        v1_dia   = [q for q in v1 if q.get("dia") == dia]
        contador: dict[int, int] = {}

        for v1q in v1_dia:
            num = v1q["numero"]
            occ = contador.get(num, 0)
            contador[num] = occ + 1

            idxs = idx_map.get(num, [])
            if occ < len(idxs):
                _, linhas = blocos[idxs[occ]]
                parsed = parsear_questao(linhas)
            else:
                parsed = {"enunciado": [], "comando": "", "alternativas": {}}
                print(f"    Q{num:03d} (ocorrencia {occ+1}): nao encontrado no OCR")

            questoes_out.append({
                "numero":       num,
                "ano":          ano,
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
            })

        n_cmd  = sum(1 for q in questoes_out if q["dia"] == dia and q.get("comando","").strip())
        n_alts = sum(1 for q in questoes_out if q["dia"] == dia and q.get("alternativas"))
        print(f"  {dia}: {len(v1_dia)} questoes  cmd={n_cmd}  alts={n_alts}")

    out_path = PASTA_JSON_V2 / f"enem_{ano}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(questoes_out, f, ensure_ascii=False, indent=2)

    n_cmd  = sum(1 for q in questoes_out if q.get("comando","").strip())
    n_alts = sum(1 for q in questoes_out if q.get("alternativas"))
    n_gab  = sum(1 for q in questoes_out if q.get("gabarito"))
    print(f"\n  Salvo: {out_path.name}")
    print(f"  Total={len(questoes_out)}  cmd={n_cmd}  alts={n_alts}  gab={n_gab}")


def _q_vazia(v1q: dict, ano: int, dia: str) -> dict:
    return {
        "numero": v1q["numero"], "ano": ano, "dia": dia,
        "area": v1q.get("area",""), "enunciado": [], "comando": "",
        "alternativas": {}, "gabarito": v1q.get("gabarito"),
        "confianca": 0.0, "revisado": False,
        "imagens": v1q.get("imagens") or [],
        "tem_imagem": v1q.get("tem_imagem", False),
    }


# -- Main ---------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python reextrair_ocr.py <ano>")
        print("Exemplo: python reextrair_ocr.py 2010")
        sys.exit(1)

    try:
        ano = int(sys.argv[1])
    except ValueError:
        print(f"Ano invalido: {sys.argv[1]}")
        sys.exit(1)

    print("=" * 68)
    print(f"  RE-EXTRACAO OCR -- ENEM {ano}")
    print("=" * 68)

    processar_ano(ano)

    print("=" * 68)


if __name__ == "__main__":
    main()
