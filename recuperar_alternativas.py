"""
Recupera alternativas faltantes para questões específicas.
Usa o mesmo algoritmo do extrair_v2.py mas só para questões afetadas.

Questões alvo (22 no total):
  2009: Q21, Q36, Q85 (dia1), Q93, Q138, Q149 (dia2) — sem alternativas
  2010: Q108 (dia2) — sem alternativas
  2016: Q49, Q85 (dia1) — alternativas incompletas
  2020: Q106 (dia2) — alternativas incompletas; Q137 — sem alternativas
  2021: Q2, Q11, Q16, Q43, Q54, Q69 (dia1), Q107, Q127, Q151, Q169, Q170 (dia2) — OCR
"""

import json, os, re, io, requests, time
import fitz
from PIL import Image
import pytesseract

BASE     = "C:/PROJETOS/HENRYJR/DADOS"
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Users\FACIMP\tessdata'

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def is_bold(flags):
    return bool(flags & 16) or bool(flags & 4)

def limpar(t):
    return re.sub(r'\s+', ' ', t).strip()

def get_pdf_linhas(pdf_path):
    """Coleta todas as linhas de texto do PDF em ordem de leitura (col esq → dir)."""
    doc = fitz.open(pdf_path)
    linhas = []
    for page_num, page in enumerate(doc):
        mid_x  = page.rect.width / 2
        blocos = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        col_esq, col_dir = [], []
        for bloco in blocos:
            if bloco["type"] != 0: continue
            centro_x = (bloco["bbox"][0] + bloco["bbox"][2]) / 2
            if centro_x < mid_x:
                col_esq.append(bloco)
            else:
                col_dir.append(bloco)
        col_esq.sort(key=lambda b: b["bbox"][1])
        col_dir.sort(key=lambda b: b["bbox"][1])
        for bloco in col_esq + col_dir:
            for raw_linha in bloco["lines"]:
                spans = [s for s in raw_linha["spans"] if s["text"].strip()]
                if not spans: continue
                linhas.append({
                    "page": page_num,
                    "y": raw_linha["bbox"][1],
                    "spans": spans
                })
    doc.close()
    return linhas

def detectar_questao_linha(linha, ano):
    for span in linha["spans"]:
        t = span["text"].strip()
        m = re.match(r'^(QUEST[AÃ]O|Quest[aã]o)\s+(\d{1,3})$', t)
        if m:
            return int(m.group(2))
    if ano == 2009 and len(linha["spans"]) >= 2:
        t0 = linha["spans"][0]["text"].strip()
        t1 = linha["spans"][1]["text"].strip()
        if t0 in ('Questão', 'Questao') and re.match(r'^\d{1,3}$', t1):
            return int(t1)
    return None

def detectar_alt_linha(linha):
    if not linha["spans"]: return None
    primeiro = linha["spans"][0]
    t = primeiro["text"].rstrip('\t').strip()
    if re.match(r'^[A-E]$', t) and is_bold(primeiro["flags"]):
        return t
    return None

def extrair_alternativas_pdf(pdf_path, numero_alvo, ano):
    """
    Extrai alternativas de uma questão específica do PDF.
    Retorna dict {A:..., B:..., C:..., D:..., E:...} ou {} se falhar.
    """
    linhas = get_pdf_linhas(pdf_path)

    # Encontrar o bloco da questão alvo
    idx_inicio = None
    idx_fim = None

    for i, l in enumerate(linhas):
        n = detectar_questao_linha(l, ano)
        if n == numero_alvo:
            idx_inicio = i
        elif n is not None and idx_inicio is not None:
            idx_fim = i
            break

    if idx_inicio is None:
        return {}
    if idx_fim is None:
        idx_fim = len(linhas)

    # Extrair alternativas do bloco
    alts = {}
    alt_atual = None
    alt_partes = []

    for i in range(idx_inicio, idx_fim):
        l = linhas[i]
        letra = detectar_alt_linha(l)
        if letra:
            if alt_atual:
                alts[alt_atual] = limpar(' '.join(alt_partes))
            alt_atual = letra
            # Texto da alternativa: spans após o primeiro
            resto = ' '.join(s["text"] for s in l["spans"][1:])
            alt_partes = [limpar(resto)] if limpar(resto) else []
        elif alt_atual:
            texto_linha = limpar(' '.join(s["text"] for s in l["spans"]))
            if texto_linha:
                alt_partes.append(texto_linha)

    if alt_atual:
        alts[alt_atual] = limpar(' '.join(alt_partes))

    return alts

def extrair_alt_ocr(pdf_path, numero_alvo, ano):
    """
    Para PDFs com texto corrompido (2021): usa OCR para extrair alternativas.
    Procura nas páginas onde está a questão.
    """
    linhas_pdf = get_pdf_linhas(pdf_path)
    doc = fitz.open(pdf_path)

    # Encontrar página da questão via OCR em todas as páginas
    paginas_candidatas = []
    for page_num in range(2, doc.page_count):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
        texto_ocr = pytesseract.image_to_string(img, lang='por',
                                                 config='--oem 3 --psm 1')
        pat = re.compile(r'Quest[aã]o\s+0*' + str(numero_alvo) + r'\b', re.IGNORECASE)
        if pat.search(texto_ocr):
            paginas_candidatas.append((page_num, texto_ocr))

    doc.close()

    if not paginas_candidatas:
        return {}

    # Para cada página candidata, tentar extrair alternativas
    for page_num, texto_ocr in paginas_candidatas:
        # Dividir o texto na parte após "Questão X"
        pat = re.compile(r'Quest[aã]o\s+0*' + str(numero_alvo) + r'\b', re.IGNORECASE)
        m = pat.search(texto_ocr)
        if not m: continue

        bloco = texto_ocr[m.end():]

        # Próxima questão delimita o fim
        next_q = re.search(r'Quest[aã]o\s+\d+\b', bloco, re.IGNORECASE)
        if next_q:
            bloco = bloco[:next_q.start()]

        alts = {}
        alt_atual = None
        alt_partes = []

        for linha in bloco.splitlines():
            m_alt = re.match(r'^([ABCDE])[\s\)\.\-]\s*(.*)$', linha.strip())
            if m_alt:
                if alt_atual:
                    alts[alt_atual] = ' '.join(alt_partes).strip()
                alt_atual = m_alt.group(1)
                alt_partes = [m_alt.group(2).strip()] if m_alt.group(2).strip() else []
            elif alt_atual and linha.strip():
                alt_partes.append(linha.strip())

        if alt_atual:
            alts[alt_atual] = ' '.join(alt_partes).strip()

        if len(alts) >= 3:
            return alts

    return {}

def patch_questao(ano, dia, numero, updates):
    url = f"{SUPA_URL}/rest/v1/questoes"
    params = {"ano": f"eq.{ano}", "dia": f"eq.{dia}", "numero": f"eq.{numero}"}
    r = requests.patch(url, params=params, json=updates, headers=HEADERS, timeout=15)
    return r.status_code

# ─── Main ───────────────────────────────────────────────────────────────────

# Casos a corrigir: (ano, dia, numero, usar_ocr)
CASOS = [
    # 2009 — sem alternativas
    (2009, 'dia1', 21, False),
    (2009, 'dia1', 36, False),
    (2009, 'dia1', 85, False),
    (2009, 'dia2', 93, False),
    (2009, 'dia2', 138, False),
    (2009, 'dia2', 149, False),
    # 2010 — sem alternativas
    (2010, 'dia2', 108, False),
    # 2016 — alternativas incompletas
    (2016, 'dia1', 49, False),
    (2016, 'dia1', 85, False),
    # 2020 — alternativas incompletas / sem alternativas
    (2020, 'dia2', 106, False),
    (2020, 'dia2', 137, False),
    # 2021 — OCR
    (2021, 'dia1', 2, True),
    (2021, 'dia1', 11, True),
    (2021, 'dia1', 16, True),
    (2021, 'dia1', 43, True),
    (2021, 'dia1', 54, True),
    (2021, 'dia1', 69, True),
    (2021, 'dia2', 107, True),
    (2021, 'dia2', 127, True),
    (2021, 'dia2', 151, True),
    (2021, 'dia2', 169, True),
    (2021, 'dia2', 170, True),
]

# Carregar todos os JSONs
jsons = {}
for ano in set(c[0] for c in CASOS):
    with open(f"{BASE}/json_v2/enem_{ano}.json", encoding='utf-8') as f:
        jsons[ano] = json.load(f)

corrigidas = 0
falhas = 0

for (ano, dia, num, usar_ocr) in CASOS:
    pdf_path = f"{BASE}/provas/{ano}/{dia}.pdf"
    print(f"\n[{ano} {dia} Q{num:03d}] {'(OCR)' if usar_ocr else '(PDF)'}...", end=' ')

    if not os.path.exists(pdf_path):
        print(f"PDF nao encontrado")
        falhas += 1
        continue

    if usar_ocr:
        alts = extrair_alt_ocr(pdf_path, num, ano)
    else:
        alts = extrair_alternativas_pdf(pdf_path, num, ano)

    print(f"alts encontradas: {list(alts.keys())}", end=' ')

    if len(alts) < 3:
        print("INSUFICIENTE")
        falhas += 1
        continue

    # Atualizar JSON
    for q in jsons[ano]:
        if q['numero'] == num and q['dia'] == dia:
            q['alternativas'] = alts
            break

    # Sincronizar Supabase
    status = patch_questao(ano, dia, num, {'alternativas': alts})
    if status in (200, 204):
        corrigidas += 1
        print("OK")
    else:
        print(f"SYNC ERRO {status}")
        falhas += 1
    time.sleep(0.05)

# Salvar JSONs atualizados
anos_modificados = set(c[0] for c in CASOS)
for ano in anos_modificados:
    with open(f"{BASE}/json_v2/enem_{ano}.json", 'w', encoding='utf-8') as f:
        json.dump(jsons[ano], f, ensure_ascii=False, indent=2)
    print(f"[{ano}] JSON salvo.")

print(f"\nRESUMO: corrigidas={corrigidas} | falhas={falhas}")
