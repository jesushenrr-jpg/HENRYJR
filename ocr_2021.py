"""
OCR das questões de 2021 com encoding corrompido.

O PDF 2021 usa fonte customizada que resulta em texto ilegível na extração.
Este script:
  1. Renderiza cada página do PDF em alta resolução
  2. Executa OCR com Tesseract (PT) — PSM 1 (Auto) para lidar com layout 2 colunas
  3. Concatena todo o texto e particiona por questão (regex "Questão NN")
  4. Extrai enunciado + alternativas de cada bloco
  5. Substitui o placeholder ⚠ no JSON v2 pelo texto real
  6. Salva o JSON e sincroniza com Supabase

Limitação: OCR não é perfeito. Questões com muitas imagens ou fórmulas
podem ficar incompletas. Melhor que o placeholder, mas revisão manual é ideal.
"""

import json, os, re, io, sys, time, requests
import fitz
from PIL import Image, ImageFilter
import pytesseract

# Configurações
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

PLACEHOLDER = "Enunciado não disponível por limitação técnica"

# Regex para detectar inicio de questão: "Questão 03" ou "QUESTÃO 03"
PAT_Q = re.compile(r'Quest[aã]o\s+0*(\d{1,3})\b', re.IGNORECASE)
# Regex para alternativas: linha iniciando com A, B, C, D ou E seguido de espaço ou )
PAT_ALT = re.compile(r'^([ABCDE])\s+(.+)$', re.MULTILINE)
PAT_ALT2 = re.compile(r'^([ABCDE])\)\s*(.+)$', re.MULTILINE)

def ocr_page(pdf_path, page_idx, scale=3.0):
    """Renderiza uma página e retorna o texto OCR."""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    doc.close()

    img = Image.open(io.BytesIO(pix.tobytes('png')))
    # Aumentar contraste para melhorar OCR
    img = img.convert('L')  # Grayscale

    # PSM 1 = Auto, detecta colunas. PSM 6 = bloco uniforme.
    config = r'--oem 3 --psm 1'
    texto = pytesseract.image_to_string(img, lang='por', config=config)
    return texto

def ocr_pdf(pdf_path, start_page=0):
    """Faz OCR em todas as páginas do PDF e retorna texto concatenado."""
    doc = fitz.open(pdf_path)
    n = doc.page_count
    doc.close()
    partes = []
    for i in range(start_page, n):
        t = ocr_page(pdf_path, i)
        partes.append(f"\n\n--- PAGINA {i+1} ---\n\n{t}")
        print(f"  Página {i+1}/{n} OCR done", end='\r')
    print()
    return "\n".join(partes)

def particionar_por_questao(texto):
    """
    Divide o texto OCR em blocos por questão.
    Retorna dict: {numero: texto_bloco}
    """
    partes = PAT_Q.split(texto)
    # partes = [antes_da_Q1, num1, bloco1, num2, bloco2, ...]
    blocos = {}
    i = 1
    while i < len(partes) - 1:
        num_str = partes[i].strip()
        bloco = partes[i + 1] if i + 1 < len(partes) else ""
        try:
            num = int(num_str)
            blocos[num] = bloco
        except ValueError:
            pass
        i += 2
    return blocos

def extrair_alternativas(bloco):
    """
    Tenta extrair alternativas A-E do bloco de texto.
    Retorna dict {A:..., B:..., C:..., D:..., E:...} e texto do enunciado.
    """
    alts = {}
    enunciado_linhas = []
    alt_atual = None
    alt_texto = []

    for linha in bloco.splitlines():
        linha = linha.rstrip()
        # Detectar início de alternativa
        m = re.match(r'^([ABCDE])[\s\)\.\-]\s*(.*)$', linha)
        if m and m.group(1) in 'ABCDE':
            # Salvar alternativa anterior
            if alt_atual:
                alts[alt_atual] = ' '.join(alt_texto).strip()
            alt_atual = m.group(1)
            alt_texto = [m.group(2).strip()]
        elif alt_atual:
            # Continuação da alternativa
            if linha.strip():
                alt_texto.append(linha.strip())
        else:
            if linha.strip():
                enunciado_linhas.append(linha.strip())

    # Última alternativa
    if alt_atual:
        alts[alt_atual] = ' '.join(alt_texto).strip()

    enunciado = ' '.join(enunciado_linhas).strip()
    return enunciado, alts

def patch_questao(ano, dia, numero, updates):
    """Atualiza campos de uma questão no Supabase."""
    url = f"{SUPA_URL}/rest/v1/questoes"
    params = {"ano": f"eq.{ano}", "dia": f"eq.{dia}", "numero": f"eq.{numero}"}
    r = requests.patch(url, params=params, json=updates, headers=HEADERS, timeout=15)
    return r.status_code

# ─── Main ───────────────────────────────────────────────────────────────────

JSON_PATH = f"{BASE}/json_v2/enem_2021.json"
with open(JSON_PATH, encoding='utf-8') as f:
    qs = json.load(f)

# Identificar questões com placeholder (precisam de OCR)
com_placeholder = {q['numero']: q for q in qs if
    q.get('enunciado') and any(PLACEHOLDER in p for p in q['enunciado'])}
print(f"Questoes com placeholder: {len(com_placeholder)}")

# Processar dia1 e dia2
total_corrigidas = 0
total_erros = 0

for dia in ['dia1', 'dia2']:
    pdf_path = f"{BASE}/provas/2021/{dia}.pdf"
    if not os.path.exists(pdf_path):
        print(f"PDF nao encontrado: {pdf_path}")
        continue

    # Filtrar questões deste dia com placeholder
    qs_dia = {num: q for num, q in com_placeholder.items() if q['dia'] == dia}
    if not qs_dia:
        print(f"[2021 {dia}] Nenhuma questao com placeholder.")
        continue

    print(f"\n[2021 {dia}] Fazendo OCR de {pdf_path}...")
    texto_completo = ocr_pdf(pdf_path, start_page=2)  # pular capa e instrucoes

    print(f"[2021 {dia}] Particionando por questao...")
    blocos = particionar_por_questao(texto_completo)
    print(f"[2021 {dia}] Encontradas {len(blocos)} questoes no OCR: {sorted(blocos.keys())[:10]}...")

    for num, q in sorted(qs_dia.items()):
        if num not in blocos:
            print(f"  Q{num:03d} NAO encontrada no OCR")
            total_erros += 1
            continue

        bloco = blocos[num]
        enunciado_ocr, alts_ocr = extrair_alternativas(bloco)

        # Atualizar JSON
        if enunciado_ocr:
            q['enunciado'] = [p.strip() for p in enunciado_ocr.split('  ') if p.strip()]
            if not q['enunciado']:
                q['enunciado'] = [enunciado_ocr]

        if alts_ocr and len(alts_ocr) >= 3:  # so atualizar se extraiu pelo menos 3 alts
            q['alternativas'] = alts_ocr

        q['ocr'] = True  # marcar como extraido por OCR para revisao posterior
        total_corrigidas += 1
        print(f"  Q{num:03d} OK | enunciado={len(enunciado_ocr)}ch | alts={list(alts_ocr.keys())}")

# Salvar JSON
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(qs, f, ensure_ascii=False, indent=2)
print(f"\nJSON salvo.")

# Sincronizar com Supabase
print("Sincronizando com Supabase...")
synced = 0
for q in qs:
    if not q.get('ocr'):
        continue
    updates = {
        'enunciado': q['enunciado'],
        'alternativas': q.get('alternativas', {}),
        'ocr': True
    }
    status = patch_questao(2021, q['dia'], q['numero'], updates)
    if status in (200, 204):
        synced += 1
    else:
        print(f"  Sync ERRO {status} Q{q['numero']}")
    time.sleep(0.02)

print(f"\nSincronizadas: {synced} questoes")
print(f"\nRESUMO: corrigidas={total_corrigidas} | erros={total_erros}")
print("\nDone!")
