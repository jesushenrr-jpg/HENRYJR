"""
OCR para o ENEM 2010.

O PDF de 2010 usa uma fonte customizada que corrompeu o texto extraído.
Este script renderiza cada página como imagem (300 DPI) e usa o Tesseract
com português para reextrair o texto com acentuação correta.

Estratégia de layout: cada página é dividida em coluna esquerda e coluna
direita antes do OCR, respeitando a ordem de leitura do caderno.

Saída: dados/json_v2/enem_2010.json (sobrescreve o atual)
       Os gabaritos são preservados do JSON existente ou do gabarito_dia*.pdf.
"""

import fitz
import json
import os
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# tessdata em pasta do projeto (não requer admin)
os.environ.setdefault("TESSDATA_PREFIX", r"C:\PROJETOS\HENRYJR\tessdata")

PASTA_PROVAS  = r"C:\PROJETOS\HENRYJR\dados\PROVAS"
PASTA_SAIDA   = r"C:\PROJETOS\HENRYJR\dados\json_v2"
PASTA_IMAGENS = r"C:\PROJETOS\HENRYJR\dados\imagens"
JSON_V1       = r"C:\PROJETOS\HENRYJR\dados\json\enem_2010.json"

ZOOM   = 300 / 72   # resolução ~300 DPI — boa para OCR
LANG   = "por"      # idioma Tesseract (português)
ANO    = 2010

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AREAS = {
    "dia1": [
        "Linguagens, Codigos e suas Tecnologias",
        "Ciencias Humanas e suas Tecnologias",
    ],
    "dia2": [
        "Ciencias da Natureza e suas Tecnologias",
        "Matematica e suas Tecnologias",
    ],
}

# ─── LIMPEZA ──────────────────────────────────────────────────────────────────
_LIXO = re.compile(
    r'[-–]\s*(?:AZUL|AMARELO|VERDE|ROSA|CINZA|BRANCO|LARANJA)\s*[-–]\s*'
    r'(?:P[AÁ]GIN[AÀ]\s*\d+|\d+[ªa°]\s*\w+)(?:\s+(?:ENEM\s*)?20\d{2})?'
    r'|(?:LINGUAGENS?\s*,?\s*C[OÓ]DIGOS?\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|CIENCIAS?\s+HUMANAS?\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|CIENCIAS?\s+DA\s+NATUREZA\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|MATEM[AÁ]TICA\s+E\s+SUAS\s+TECNOLOGIAS?)(?:\s*E\s+REDA[CÇ][AÃ]O)?'
    r'|(?:\d+\s*)?(?:CH|LC|CN|MT)\s*[-–]\s*\d+[°º]\w*\s+[Dd][Ii][Aa]\b[^\n]*'
    r'|(?:ENEM\s*20\d{2}){2,}'
    r'|\*[A-Z0-9]{6,}\*'
    r'|QUEST[AÃ]O\s+\d+\s*$'
    r'|RASCUNHO\s+DA\s+REDA[CÇ][AÃ]O[^\n]*'
    r'|(?:\b\d{1,2}\s+){3,}\d{1,2}\b',
    re.IGNORECASE,
)

def limpar(t):
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def limpar_lixo(t):
    return limpar(_LIXO.sub(' ', t))

def get_area(numero, dia):
    if dia == "dia1":
        return AREAS["dia1"][0] if numero <= 45 else AREAS["dia1"][1]
    return AREAS["dia2"][0] if numero <= 135 else AREAS["dia2"][1]

# ─── GABARITOS ────────────────────────────────────────────────────────────────
def carregar_gabaritos_v1():
    """Carrega gabaritos do JSON v1 que foram inseridos manualmente."""
    if not os.path.exists(JSON_V1):
        return {}
    with open(JSON_V1, encoding="utf-8") as f:
        questoes = json.load(f)
    return {q["numero"]: q["gabarito"] for q in questoes if q.get("gabarito")}


def extrair_gabarito_pdf(caminho_pdf, dia):
    """Fallback: tenta extrair gabarito do PDF (funciona para anos com gabarito textual)."""
    gabarito = {}
    if not os.path.exists(caminho_pdf):
        return gabarito
    try:
        doc = fitz.open(caminho_pdf)
        texto = "\n".join(p.get_text() for p in doc)
        doc.close()
        for padrao in [
            r'(\d{1,3})\s*[–\-:]?\s*([A-Ea-e])\b',
            r'QUESTAO\s*(\d{1,3})\s*([A-Ea-e])\b',
        ]:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            if matches:
                for num, letra in matches:
                    n = int(num)
                    if (dia == "dia1" and 1 <= n <= 90) or \
                       (dia == "dia2" and 91 <= n <= 180):
                        gabarito[n] = letra.upper()
                break
    except Exception:
        pass
    return gabarito

# ─── RENDERIZAÇÃO E OCR ───────────────────────────────────────────────────────
def pagina_para_imagem_pil(pagina):
    """Renderiza uma página do PDF como imagem PIL em ~300 DPI."""
    mat  = fitz.Matrix(ZOOM, ZOOM)
    pix  = pagina.get_pixmap(matrix=mat, alpha=False)
    modo = "RGB"
    return Image.frombytes(modo, [pix.width, pix.height], pix.samples)


def ocr_imagem(img: Image.Image) -> str:
    """Roda Tesseract na imagem e retorna texto limpo."""
    # psm 4: coluna única de texto — melhor separação de linhas que psm 6
    config = "--oem 1 --psm 6"
    texto = pytesseract.image_to_string(img, lang=LANG, config=config)
    return texto


def ocr_pagina(pagina) -> str:
    """
    Divide a página em coluna esquerda e direita, faz OCR em cada metade
    separadamente e concatena na ordem de leitura correta.
    """
    img = pagina_para_imagem_pil(pagina)
    largura, altura = img.size
    meio = largura // 2

    # Margem pequena para não cortar palavras na divisão
    margem = int(largura * 0.01)

    col_esq = img.crop((0,             0, meio + margem, altura))
    col_dir = img.crop((meio - margem, 0, largura,       altura))

    texto_esq = ocr_imagem(col_esq)
    texto_dir = ocr_imagem(col_dir)

    # Separador de coluna (linha em branco) para preservar estrutura
    return texto_esq + "\n\n" + texto_dir


# ─── PARSE DO TEXTO OCR ───────────────────────────────────────────────────────
_RE_QUESTAO = re.compile(r'^\s*QUEST[AÃ]O\s+(\d{1,3})\s*$', re.IGNORECASE)

# Marcadores de círculo do 2010: OCR lê os círculos de alternativa como estes
# artefatos. Q e OQ/O& são raros em texto normal → mais seguros.
# 'e', 'é', 'O', 'o', 'oe' são adicionados com guarda de total_linhas >= MIN_LINHAS_ENUNC.
_RE_CIRC_2010 = re.compile(r'^(OQ?&?|[EG]Q?|Q|&&?|&|[eéêèEG]|O[^u]?|oe?|oO|eo|EO)\s+(.+)$')

# Marcador 'o' minúsculo isolado: regex para uso quando já estamos em modo alt
# Aceita 'o texto' (com espaço) ou 'o.' / 'o,' (marcador imediatamente seguido de pontuação)
_RE_O_LOWER = re.compile(r'^o(?:\s+(.+)|[.,;!?])$')

# Marcadores "seguros": raramente ocorrem em texto normal
# 'oO'/'eo'/'EO' adicionados — combos impossíveis em português normal
_RE_CIRC_SEGURO = re.compile(r'^(OQ?&?|Q|&&?|&|oO|eo|EO)\s+(.+)$')

# Inline: marcador E absorvido após pontuação final de uma alternativa
# Captura: (texto_antes_ponto, marcador_E, texto_da_E)
_RE_E_INLINE = re.compile(
    r'^(.*?[.!?])\s+([EeéêèGOQ]Q?&?)\s+([A-ZÁÉÍÓÚa-záéíóúãõâêôüà].+)$',
    re.DOTALL,
)

MIN_LINHAS_ENUNC = 5   # linhas mínimas antes de ativar detecção de alternativas


def pre_processar_ocr(texto: str) -> str:
    """
    Insere quebra de linha antes de marcadores de círculo que o OCR coloca
    na mesma linha do texto anterior.
    Passo 1: após pontuação final + marcador + palavra/dígito.
    Passo 2: 'oO', 'oe', 'eo' inline entre não-espaços (combos inexistentes em português).
    NÃO inclui 'Q' sozinho: evita quebrar 'Questão' em duas linhas.
    """
    # Passo 1: após [.!?] + marcador + início de palavra ou dígito
    t = re.sub(
        r'([.!?])\s+(OQ?&?|[EeéêèEG]|oe?|eo)\s+([A-ZÁÉÍÓÚa-záéíóúãõ0-9R\$])',
        r'\1\n\2 \3',
        texto,
    )
    # Passo 2: marcadores inline dentro de uma linha (não cruza newlines)
    # oO/oe/eo/EO são combos inexistentes em português normal
    t = re.sub(
        r'(\S) +(oO|oe|eo|EO) +(\S)',
        lambda m: f'{m.group(1)}\n{m.group(2)} {m.group(3)}',
        t,
    )
    return t


def recuperar_E_inline(alts: dict) -> dict:
    """
    Para questões com exatamente 4 alternativas (A-D), tenta recuperar E
    a partir de texto absorvido inline na última alternativa detectada.
    Padrão: 'texto. [marcador] mais_texto' → split em D e E.
    """
    if len(alts) >= 5:
        return alts

    for letra in ['D', 'C', 'B']:
        texto = alts.get(letra, '')
        m = _RE_E_INLINE.match(texto)
        if m:
            alts[letra] = m.group(1).strip()
            alts['E']   = m.group(3).strip()
            return alts
    return alts


def parse_questoes(texto_completo: str, dia: str, gabarito: dict) -> list:
    """
    Analisa o texto OCR linha-a-linha para o ENEM 2010.

    Os círculos de alternativa são lidos pelo Tesseract como: Q, OQ, O, &, e.
    O parser detecta esses padrões em ordem de aparição e atribui A-E.

    Proteção contra falso-positivo:
    - Usa total_linhas (conta todas as linhas não-em-branco desde QUESTÃO)
      independente de estarmos em modo enunciado ou alternativa.
    - Marcadores "seguros" (Q, OQ, &) são aceitos a partir de 1 linha.
    - Marcadores ambíguos (O, e) só são aceitos após MIN_LINHAS_ENUNC linhas.
    """
    questoes: dict = {}

    num_atual    = None
    enunciado    = []
    alts         = {}
    alt_atual    = None
    alt_linhas   = []
    alt_counter  = 0        # próxima letra: 0=A … 4=E
    total_linhas = 0        # contador geral (enunciado + alt_linhas)
    LETRAS       = "ABCDE"

    def fechar_alt():
        nonlocal alt_atual, alt_linhas
        if alt_atual is not None:
            texto = limpar_lixo(" ".join(alt_linhas))
            if texto or alt_atual not in alts:
                alts[alt_atual] = texto
        alt_atual  = None
        alt_linhas = []

    def fechar_questao():
        nonlocal num_atual, enunciado, alts, alt_atual, alt_linhas
        nonlocal alt_counter, total_linhas
        fechar_alt()
        n = num_atual
        if n is None:
            return
        valida = (dia == "dia1" and 1 <= n <= 90) or \
                 (dia == "dia2" and 91 <= n <= 180)
        if not valida:
            num_atual = None; enunciado = []; alts = {}
            alt_counter = 0; total_linhas = 0
            return

        paragrafos = [limpar_lixo(p) for p in enunciado if limpar_lixo(p)]
        alts = recuperar_E_inline(alts)
        q = {
            "numero":       n,
            "ano":          ANO,
            "dia":          dia,
            "area":         get_area(n, dia),
            "enunciado":    paragrafos,
            "comando":      "",
            "alternativas": dict(alts),
            "gabarito":     gabarito.get(n),
            "confianca":    1.0 if len(alts) == 5 else 0.5,
            "revisado":     False,
            "imagens":      [],
            "tem_imagem":   False,
        }
        if n not in questoes or len(alts) > len(questoes[n]["alternativas"]):
            questoes[n] = q

        num_atual    = None; enunciado  = []; alts = {}
        alt_atual    = None; alt_linhas = []
        alt_counter  = 0;    total_linhas = 0

    def iniciar_alt(letra: str, resto: str):
        nonlocal alt_atual, alt_linhas
        fechar_alt()
        alt_atual  = letra
        alt_linhas = [resto] if resto else []

    for linha in texto_completo.splitlines():
        # ── Marcador de questão ──────────────────────────────────────────────
        m = _RE_QUESTAO.match(linha)
        if m:
            fechar_questao()
            num_atual = int(m.group(1))
            continue

        if num_atual is None:
            continue

        linha_limpa = limpar(linha)
        if not linha_limpa:
            continue

        total_linhas += 1   # conta todas as linhas não-em-branco da questão

        if alt_counter < 5:
            # Marcador seguro: aceito a partir de 1 linha de contexto
            m_seg = _RE_CIRC_SEGURO.match(linha)
            if m_seg and total_linhas >= 1:
                iniciar_alt(LETRAS[alt_counter], m_seg.group(2).strip())
                alt_counter += 1
                continue

            # Marcador ambíguo (O, e, o, oe): só após MIN_LINHAS_ENUNC linhas
            m_amb = _RE_CIRC_2010.match(linha)
            if m_amb and total_linhas >= MIN_LINHAS_ENUNC:
                texto_amb = m_amb.group(2) or ''
                iniciar_alt(LETRAS[alt_counter], texto_amb.strip())
                alt_counter += 1
                continue

            # 'o' + pontuação imediata (ex: 'o.' — alt com texto OCR ilegível)
            # Específico o suficiente para não ter falsos positivos
            if re.match(r'^o[.,;!?]$', linha) and total_linhas >= MIN_LINHAS_ENUNC:
                iniciar_alt(LETRAS[alt_counter], '')
                alt_counter += 1
                continue

            # 'o' minúsculo: muito ambíguo, aceito apenas quando já estamos
            # em modo alternativa (alt_counter >= 1) — seguro neste contexto
            if alt_counter >= 1:
                m_o = _RE_O_LOWER.match(linha)
                if m_o:
                    texto_o = m_o.group(1) or ''
                    iniciar_alt(LETRAS[alt_counter], texto_o.strip())
                    alt_counter += 1
                    continue

        # ── Continuação de alternativa ou enunciado ──────────────────────────
        if alt_atual is not None:
            alt_linhas.append(linha_limpa)
        else:
            enunciado.append(linha_limpa)

    fechar_questao()

    return sorted(questoes.values(), key=lambda q: q["numero"])


# ─── IMAGENS (mantém as já extraídas pelo extrair_v2.py) ─────────────────────
def reaproveicar_imagens(questoes: list):
    """
    Verifica se já existem imagens extraídas para cada questão
    e preenche os campos imagens/tem_imagem.
    """
    for q in questoes:
        n   = q["numero"]
        dia = q["dia"]
        pasta = Path(PASTA_IMAGENS) / str(ANO) / dia
        if not pasta.exists():
            continue
        imgs = sorted(pasta.glob(f"q{n:03d}_*.jpg")) + \
               sorted(pasta.glob(f"q{n:03d}_*.png")) + \
               sorted(pasta.glob(f"q{n:03d}_*.jpeg"))
        if imgs:
            q["imagens"]    = [f"{ANO}/{dia}/{p.name}" for p in imgs]
            q["tem_imagem"] = True


# ─── PROCESSAMENTO PRINCIPAL ─────────────────────────────────────────────────
def processar_dia(dia: str, gabarito: dict) -> list:
    caminho = os.path.join(PASTA_PROVAS, str(ANO), f"{dia}.pdf")
    if not os.path.exists(caminho):
        print(f"  ⚠️  PDF não encontrado: {caminho}")
        return []

    print(f"  📄 Abrindo {dia}.pdf...")
    doc = fitz.open(caminho)
    n_pags = len(doc)
    print(f"     {n_pags} páginas — iniciando OCR (pode demorar ~1-2 min)...")

    texto_total = []
    for i, pagina in enumerate(doc):
        print(f"     OCR página {i+1}/{n_pags}...", end="\r")
        texto_total.append(ocr_pagina(pagina))

    doc.close()
    print(f"\n     OCR concluído.")

    texto_completo = pre_processar_ocr("\n\n".join(texto_total))
    questoes = parse_questoes(texto_completo, dia, gabarito)

    reaproveicar_imagens(questoes)

    com_5  = sum(1 for q in questoes if len(q["alternativas"]) == 5)
    sem    = sum(1 for q in questoes if len(q["alternativas"]) == 0)
    print(f"  ✅ {len(questoes)} questões | {com_5} com 5 alternativas | {sem} sem alternativas")
    return questoes


def main():
    print("\n" + "="*60)
    print("  OCR ENEM 2010 — Reextração via Tesseract")
    print("="*60)

    # Gabaritos: prioridade para o JSON v1 (inserção manual)
    gabarito = carregar_gabaritos_v1()
    print(f"\n  🗝  Gabaritos carregados do v1: {len(gabarito)} questões")

    # Fallback: gabarito PDF (provavelmente não vai extrair nada para 2010)
    if len(gabarito) < 180:
        for dia in ["dia1", "dia2"]:
            gab_pdf = os.path.join(PASTA_PROVAS, str(ANO), f"gabarito_{dia}.pdf")
            gab_extra = extrair_gabarito_pdf(gab_pdf, dia)
            for k, v in gab_extra.items():
                if k not in gabarito:
                    gabarito[k] = v
        print(f"  🗝  Gabaritos após fallback PDF: {len(gabarito)} questões")

    todas_questoes = []
    for dia in ["dia1", "dia2"]:
        print(f"\n{'─'*50}")
        print(f"  📅 Processando {dia}...")
        questoes = processar_dia(dia, gabarito)
        todas_questoes.extend(questoes)

    # Salva JSON
    Path(PASTA_SAIDA).mkdir(parents=True, exist_ok=True)
    destino = os.path.join(PASTA_SAIDA, "enem_2010.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(todas_questoes, f, ensure_ascii=False, indent=2)

    # Relatório
    com_gab  = sum(1 for q in todas_questoes if q["gabarito"])
    com_5alt = sum(1 for q in todas_questoes if len(q["alternativas"]) == 5)
    com_img  = sum(1 for q in todas_questoes if q["tem_imagem"])

    print(f"\n{'='*60}")
    print(f"  RESULTADO FINAL — ENEM 2010")
    print(f"{'─'*60}")
    print(f"  Total de questões:       {len(todas_questoes)}")
    print(f"  Com gabarito:            {com_gab}")
    print(f"  Com 5 alternativas:      {com_5alt}")
    print(f"  Com imagem:              {com_img}")
    print(f"  Salvo em: {destino}")
    print(f"{'='*60}\n")

    # Mostra Q007 como amostra
    q7 = next((q for q in todas_questoes if q["numero"] == 7), None)
    if q7:
        print("  AMOSTRA — Q007:")
        for p in q7["enunciado"][:4]:
            print(f"    {p[:110]}")
        print(f"  Alternativas: {list(q7['alternativas'].keys())}")
        print(f"  Gabarito: {q7['gabarito']}\n")


if __name__ == "__main__":
    main()
