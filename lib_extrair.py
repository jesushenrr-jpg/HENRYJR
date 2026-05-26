"""
lib_extrair.py — Funções compartilhadas para extração de questões.
Usada por extrair_uft.py, extrair_exato_provas.py, extrair_enem_simulados.py.
"""
import base64
import json
import os
import re
import time
from pathlib import Path

import fitz  # PyMuPDF: pip install pymupdf

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

AREA_ALIASES: dict[str, str] = {
    "linguagens": "Linguagens, Codigos e suas Tecnologias",
    "linguagens, códigos e suas tecnologias": "Linguagens, Codigos e suas Tecnologias",
    "linguagens, codigos e suas tecnologias": "Linguagens, Codigos e suas Tecnologias",
    "ciências humanas e suas tecnologias": "Ciencias Humanas e suas Tecnologias",
    "ciencias humanas e suas tecnologias": "Ciencias Humanas e suas Tecnologias",
    "humanas": "Ciencias Humanas e suas Tecnologias",
    "ciências da natureza e suas tecnologias": "Ciencias da Natureza e suas Tecnologias",
    "ciencias da natureza e suas tecnologias": "Ciencias da Natureza e suas Tecnologias",
    "natureza": "Ciencias da Natureza e suas Tecnologias",
    "matemática e suas tecnologias": "Matematica e suas Tecnologias",
    "matematica e suas tecnologias": "Matematica e suas Tecnologias",
    "matemática": "Matematica e suas Tecnologias",
    "matematica": "Matematica e suas Tecnologias",
}

AREAS_VALIDAS = {
    "Linguagens, Codigos e suas Tecnologias",
    "Ciencias Humanas e suas Tecnologias",
    "Ciencias da Natureza e suas Tecnologias",
    "Matematica e suas Tecnologias",
}


def normalizar_area(texto: str) -> str | None:
    """Normaliza nome de área para o padrão do banco. Retorna None se não reconhecida."""
    key = texto.strip().lower()
    for alias, canonical in AREA_ALIASES.items():
        if alias in key:
            return canonical
    for area in AREAS_VALIDAS:
        if area.lower() in key:
            return area
    return None


def pagina_tem_texto(texto: str, min_chars: int = 150) -> bool:
    """True se o texto extraído tem conteúdo suficiente (dispensa Vision)."""
    return len(texto.strip()) >= min_chars


def extrair_texto_pagina(doc: fitz.Document, page_num: int) -> str:
    """Extrai texto de uma página específica."""
    return doc[page_num].get_text()


def renderizar_pagina_base64(doc: fitz.Document, page_num: int, dpi: int = 72) -> str:
    """Renderiza uma página como PNG e retorna base64."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = doc[page_num].get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    return base64.b64encode(png_bytes).decode()


def _chamar_groq_json(messages: list, max_tokens: int = 4096, tentativas: int = 3) -> str | None:
    """Chama a API Groq e retorna o texto da resposta.
    Usa requests (não urllib) para enviar User-Agent correto e evitar bloqueio Cloudflare.
    """
    import requests as _req
    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    for t in range(tentativas):
        try:
            r = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            elif r.status_code == 429:
                espera = 65 if t == 0 else 120
                print(f"    ↩ Rate limit 429 — aguardando {espera}s...")
                time.sleep(espera)
            elif t < tentativas - 1:
                time.sleep(10 * (t + 1))
            else:
                print(f"    ✗ Groq falhou após {tentativas} tentativas: HTTP {r.status_code}")
                return None
        except Exception as e:
            if t < tentativas - 1:
                time.sleep(10 * (t + 1))
            else:
                print(f"    ✗ Groq falhou: {e}")
                return None
    return None


PROMPT_EXTRAIR_QUESTOES = """Analise esta página de prova e extraia TODAS as questões visíveis.
Para cada questão retorne um objeto JSON com:
- numero (int): número da questão
- area (str): área — exatamente uma de: "Linguagens, Codigos e suas Tecnologias", "Ciencias Humanas e suas Tecnologias", "Ciencias da Natureza e suas Tecnologias", "Matematica e suas Tecnologias"
- enunciado (list[str]): parágrafos do enunciado (sem o comando)
- comando (str): frase final antes das alternativas (começa com verbo)
- alternativas (dict): {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}

Retorne JSON válido no formato:
{"questoes": [...]}

Se não houver questões na página, retorne {"questoes": []}.
Nunca inclua o número da questão nos campos de texto."""


def extrair_questoes_pagina_vision(doc: fitz.Document, page_num: int) -> list[dict]:
    """Usa Groq Vision para extrair questões de uma página como imagem."""
    img_b64 = renderizar_pagina_base64(doc, page_num)
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": PROMPT_EXTRAIR_QUESTOES},
        ],
    }]
    resposta = _chamar_groq_json(messages)
    if not resposta:
        return []
    match = re.search(r'\{.*\}', resposta, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        questoes = data.get("questoes", [])
        for q in questoes:
            if q.get("area"):
                q["area"] = normalizar_area(q["area"]) or q["area"]
        return questoes
    except json.JSONDecodeError:
        print(f"    ⚠ JSON inválido na página {page_num}")
        return []


def extrair_questoes_pdf(pdf_path: Path) -> list[dict]:
    """
    Extrai questões de um PDF usando PyMuPDF + Groq Vision fallback.
    Retorna lista de questões brutas (sem gabarito).
    """
    if not pdf_path.exists():
        print(f"  ✗ PDF não encontrado: {pdf_path}")
        return []

    doc = fitz.open(str(pdf_path))
    todas: list[dict] = []
    print(f"  Extraindo {pdf_path.name} ({len(doc)} páginas)...")

    for page_num in range(len(doc)):
        texto = extrair_texto_pagina(doc, page_num)
        if pagina_tem_texto(texto):
            questoes_pagina = _parse_questoes_texto(texto)
            if questoes_pagina:
                todas.extend(questoes_pagina)
                print(f"    Página {page_num+1}: {len(questoes_pagina)} questões (texto)")
                continue

        # Fallback: Groq Vision
        print(f"    Página {page_num+1}: usando Vision...")
        questoes_pagina = extrair_questoes_pagina_vision(doc, page_num)
        if questoes_pagina:
            todas.extend(questoes_pagina)
            print(f"    Página {page_num+1}: {len(questoes_pagina)} questões (Vision)")
        time.sleep(1)  # Evita rate limit

    doc.close()
    return todas


def _parse_questoes_texto(texto: str) -> list[dict]:
    """
    Tenta extrair questões de texto PyMuPDF usando padrão ENEM.
    Retorna [] se não conseguir detectar estrutura clara.
    """
    if not re.search(r'\b(?:QUESTÃO|Questão|QUEST[AÃ]O)\s+\d+', texto):
        return []
    # Estrutura detectada mas parsing completo deixamos para Vision
    # para garantir qualidade — retorna [] para acionar fallback Vision
    return []


# ---------------------------------------------------------------------------
# Parse de gabaritos
# ---------------------------------------------------------------------------

def parse_gabarito(pdf_path: Path) -> dict[int, str | None]:
    """
    Extrai gabarito de um PDF. Tenta múltiplos padrões em sequência.
    Retorna dict {numero: letra} onde letra pode ser None (anulada).
    """
    if not pdf_path.exists():
        print(f"  ⚠ Gabarito não encontrado: {pdf_path}")
        return {}

    doc = fitz.open(str(pdf_path))
    texto = "\n".join(doc[i].get_text() for i in range(len(doc)))
    doc.close()

    resultado = _gabarito_tabela(texto)
    if resultado:
        return resultado

    resultado = _gabarito_numero_letra(texto)
    if resultado:
        return resultado

    resultado = _gabarito_brackets(texto)
    if resultado:
        return resultado

    print(f"  ⚠ Gabarito texto falhou para {pdf_path.name}, tentando Vision...")
    return _gabarito_vision(pdf_path)


def _gabarito_tabela(texto: str) -> dict[int, str | None]:
    """Formato: tabela com número e letra, ex: '01 A  02 B  03 C'"""
    pattern = re.compile(r'(\d{1,2})\s+([A-E])\b')
    resultado = {}
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= 180:
            resultado[num] = m.group(2).upper()
    return resultado if len(resultado) >= 5 else {}


def _gabarito_numero_letra(texto: str) -> dict[int, str | None]:
    """Formato: '1. A', '1- A', '01. A'"""
    resultado = {}
    pattern = re.compile(
        r'^(\d{1,3})[.\-]\s*([A-E]|ANULADA)(?:\s|$)',
        re.MULTILINE | re.IGNORECASE,
    )
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        val = m.group(2).upper()
        if 1 <= num <= 180:
            resultado[num] = None if val == "ANULADA" else val
    return resultado if len(resultado) >= 5 else {}


def _gabarito_brackets(texto: str) -> dict[int, str | None]:
    """Formato: '1. [A]', '01. [B]'"""
    resultado = {}
    pattern = re.compile(
        r'(\d{1,3})[.\-]\s*\[([A-E])\](?:\s*[-–]\s*(ANULADA))?',
        re.IGNORECASE,
    )
    for m in pattern.finditer(texto):
        num = int(m.group(1))
        letra = m.group(2).upper()
        anulada = bool(m.group(3))
        if 1 <= num <= 180:
            resultado[num] = None if anulada else letra
    return resultado if len(resultado) >= 5 else {}


def _gabarito_vision(pdf_path: Path) -> dict[int, str | None]:
    """Extrai gabarito via Groq Vision quando texto falha."""
    doc = fitz.open(str(pdf_path))
    img_b64 = renderizar_pagina_base64(doc, 0)
    doc.close()

    prompt = """Esta é a página de gabarito de uma prova. Extraia todos os pares (número, resposta).
Retorne JSON: {"gabarito": {"1": "A", "2": "B", ...}}
Para questões anuladas use null. Somente números e letras A-E."""

    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": prompt},
        ],
    }]
    resposta = _chamar_groq_json(messages, max_tokens=1024)
    if not resposta:
        return {}
    match = re.search(r'\{.*\}', resposta, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group())
        gab = data.get("gabarito", {})
        return {int(k): (v.upper() if v else None) for k, v in gab.items()
                if str(k).isdigit() and (v is None or v.upper() in "ABCDE")}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Normalização de questão para o esquema do banco
# ---------------------------------------------------------------------------

def normalizar_questao_banco(
    q: dict,
    fonte: str,
    tipo: str,
    ano: int | None,
    turno: str | None,
    evento: str | None,
    provedor: str | None,
    dia: str,
    gabarito_map: dict[int, str | None],
    numero_global: int,
) -> dict:
    """
    Converte uma questão bruta para o formato do banco de dados.
    numero_global: número único para esta questão nesta fonte/prova.
    """
    num_local = q.get("numero", numero_global)
    gabarito = gabarito_map.get(num_local)
    anulada = gabarito is None and num_local in gabarito_map

    alternativas = q.get("alternativas", {})
    if isinstance(alternativas, list):
        alternativas = {chr(65 + i): v for i, v in enumerate(alternativas)}

    enunciado = q.get("enunciado", [])
    if isinstance(enunciado, str):
        enunciado = [enunciado]

    row: dict = {
        "numero":       numero_global,
        "ano":          ano,
        "dia":          dia,
        "area":         q.get("area") or "Linguagens, Codigos e suas Tecnologias",
        "competencia":  None,
        "enunciado":    enunciado,
        "comando":      q.get("comando", ""),
        "alternativas": alternativas,
        "gabarito":     gabarito,
        "confianca":    0.80,
        "revisado":     False,
        "anulada":      anulada,
        "tem_imagem":   False,
        "pagina_pdf":   None,
        "imagens":      [],
        "fonte":        fonte,
        "tipo":         tipo,
        "evento":       evento,
        "turno":        turno,
        "provedor":     provedor,
    }
    # Remove None apenas para campos opcionais — mantém campos que podem ser NULL no DB
    campos_nullable = {"ano", "competencia", "pagina_pdf", "evento", "turno", "provedor", "gabarito"}
    return {k: v for k, v in row.items() if v is not None or k in campos_nullable}
