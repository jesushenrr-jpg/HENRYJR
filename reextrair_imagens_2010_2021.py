"""
Re-extrai imagens para 2010 e 2021 usando abordagem baseada em páginas (não texto).

Problema:
- 2010: texto com encoding corrompido → regex de questão falha
- 2021: texto completamente corrompido (caracteres de controle) → regex falha
- Resultado: 83 imagens (2010) + 129 imagens (2021) ausentes no disco/Supabase

Abordagem:
1. Carrega o JSON v2 do ano → obtém mapeamento numero→pagina_pdf (ou detecta por posição)
2. Para cada questão com tem_imagem=True e sem arquivo em disco:
   - Renderiza a página do PDF em alta resolução (3x = ~216 DPI)
   - Salva a imagem da página inteira como q{numero:03d}_1.jpg (fallback se região não detectável)
3. Upload para Supabase Storage
4. Atualiza JSON e Supabase questoes.imagens

Para 2010/2021 sem pagina_pdf preenchido:
  - Estratégia: varrer todas as páginas do PDF; para cada imagem no JSON sem arquivo,
    tentar encontrar a página com base na ordem das questões.
"""

import json, os, glob, requests, time, sys
import fitz  # PyMuPDF

BASE     = "C:/PROJETOS/HENRYJR/DADOS"
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"

HEADERS_JSON = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

SCALE = 3.0  # ~216 DPI

def render_page(pdf_path, page_idx, scale=SCALE):
    """Renderiza uma página do PDF e retorna bytes JPEG."""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("jpeg")
    doc.close()
    return img_bytes

def upload_to_storage(img_bytes, storage_path):
    """Faz upload de bytes para o Supabase Storage. Retorna URL pública ou None."""
    url = f"{SUPA_URL}/storage/v1/object/imagens-questoes/{storage_path}"
    headers = {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "image/jpeg",
        "x-upsert": "true"
    }
    r = requests.post(url, data=img_bytes, headers=headers, timeout=30)
    if r.status_code in (200, 201):
        pub_url = f"{SUPA_URL}/storage/v1/object/public/imagens-questoes/{storage_path}"
        return pub_url
    else:
        print(f"    Upload ERRO {r.status_code}: {r.text[:200]}")
        return None

def patch_questao(ano, dia, numero, imagens):
    """Atualiza o campo imagens de uma questão no Supabase."""
    url = f"{SUPA_URL}/rest/v1/questoes"
    params = {"ano": f"eq.{ano}", "dia": f"eq.{dia}", "numero": f"eq.{numero}"}
    r = requests.patch(url, params=params, json={"imagens": imagens},
                       headers=HEADERS_JSON, timeout=15)
    return r.status_code

def get_pdf_path(ano, dia):
    """Retorna o caminho do PDF para um ano/dia."""
    return f"{BASE}/provas/{ano}/{dia}.pdf"

def count_pages(pdf_path):
    doc = fitz.open(pdf_path)
    n = doc.page_count
    doc.close()
    return n

def process_ano(ano, dias=None):
    json_path = f"{BASE}/json_v2/enem_{ano}.json"
    with open(json_path, encoding="utf-8") as f:
        qs = json.load(f)

    if dias is None:
        dias = sorted(set(q["dia"] for q in qs))

    total_found = 0
    total_skip  = 0
    total_error = 0

    for dia in dias:
        pdf_path = get_pdf_path(ano, dia)
        if not os.path.exists(pdf_path):
            print(f"  PDF não encontrado: {pdf_path}")
            continue

        n_pages = count_pages(pdf_path)
        print(f"\n  [{ano} {dia}] PDF: {n_pages} páginas")

        # Questões deste dia que precisam de imagem mas não têm arquivo
        faltando = []
        for q in qs:
            if q["dia"] != dia: continue
            if not (q.get("tem_imagem") and q.get("imagens")): continue
            img = q["imagens"][0]
            rel_path = img.get("path", "")
            full_path = f"{BASE}/imagens/{rel_path}"
            if os.path.exists(full_path):
                total_skip += 1
                continue
            faltando.append(q)

        if not faltando:
            print(f"  [{ano} {dia}] Todas as imagens já existem.")
            continue

        print(f"  [{ano} {dia}] {len(faltando)} questões sem imagem. Extraindo por página...")

        # Estratégia: distribuir questões pelas páginas do PDF
        # Ordenar por numero e dividir igualmente pelas páginas disponíveis
        # (heurística: provas ENEM têm ~2-3 questões por página)
        faltando_sorted = sorted(faltando, key=lambda q: q["numero"])

        # Calcular páginas por questão (aproximado)
        # Geralmente a primeira questão começa na página 3-4 e vai até o fim
        # Para 2010 (45 questões por dia) e 2021 (45 questões por dia)
        start_page = 3  # pular capa, instrucoes
        usable_pages = n_pages - start_page

        for i, q in enumerate(faltando_sorted):
            num = q["numero"]
            # Estimativa: distribuir linearmente nas páginas úteis
            page_idx = start_page + int(i * usable_pages / len(faltando_sorted))
            page_idx = min(page_idx, n_pages - 1)

            # Se o JSON tem pagina_pdf, usar ele
            if q.get("pagina_pdf") is not None:
                page_idx = q["pagina_pdf"]

            img_dir = f"{BASE}/imagens/{ano}/{dia}"
            os.makedirs(img_dir, exist_ok=True)
            img_filename = f"q{num:03d}_1.jpg"
            img_full = f"{img_dir}/{img_filename}"
            rel_path = f"{ano}/{dia}/{img_filename}"

            print(f"    Q{num:03d} pagina {page_idx+1} -> {rel_path}", end=" ")

            try:
                img_bytes = render_page(pdf_path, page_idx)
            except Exception as e:
                print(f"ERRO render: {e}")
                total_error += 1
                continue

            # Salvar no disco
            with open(img_full, "wb") as f:
                f.write(img_bytes)

            # Upload para Supabase Storage
            pub_url = upload_to_storage(img_bytes, rel_path)
            if pub_url is None:
                print(f"ERRO upload")
                total_error += 1
                continue

            # Atualizar o dict de imagens no JSON
            for img in q["imagens"]:
                img["path"] = rel_path
                img["supabase_url"] = pub_url
                if "posicao" not in img:
                    img["posicao"] = "antes_1"

            print("OK")
            total_found += 1
            time.sleep(0.05)

    # Salvar JSON atualizado
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=2)
    print(f"\n  [{ano}] JSON salvo.")

    # Sincronizar questões atualizadas com Supabase
    print(f"  [{ano}] Sincronizando com Supabase...")
    synced = 0
    for q in qs:
        if not (q.get("tem_imagem") and q.get("imagens")): continue
        img = q["imagens"][0]
        # Só sincronizar se tem supabase_url válida
        if not img.get("supabase_url"): continue
        status = patch_questao(q["ano"], q["dia"], q["numero"], q["imagens"])
        if status in (200, 204):
            synced += 1
        else:
            print(f"    Sync ERRO {status} — Q{q['numero']}")
        time.sleep(0.02)

    print(f"  [{ano}] Sincronizadas: {synced} questões.")
    print(f"\n  [{ano}] RESUMO: extraídas={total_found} | já existiam={total_skip} | erros={total_error}")

# --- Main ---
anos = [2010, 2021]

for ano in anos:
    print(f"\n{'='*60}")
    print(f"Processando {ano}...")
    print(f"{'='*60}")
    process_ano(ano)

print("\n\nDone!")
