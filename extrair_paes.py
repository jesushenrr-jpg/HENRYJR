"""
extrair_paes.py — Extrai questões do vestibular PAES (UEMA) 2019–2025.
PDFs são digitais — parsing de texto, zero Vision/API.
Saída: DADOS/json_paes/paes_{ano}_{dia}.json

Estrutura PAES:
  - Q01–Q15: Linguagens, Códigos e suas Tecnologias (comum)
  - Q16–Q20: Língua Inglesa (1ª variante) ou Língua Espanhola (2ª variante)
  - Q21–Q40: Ciências Humanas e suas Tecnologias
  - Q41–Q60: Matemática, Ciências da Natureza e suas Tecnologias
  - 2021 teve DIA 1 + DIA 2 separados (44 questões por dia, numeração reinicia)
  - Outros anos: dia único com 60 questões

Gabaritos:
  - Formato: "01\nD\n02\nB\n..." — número e letra em linhas alternadas
  - Q16-Q20 aparecem duas vezes: 1ª = Língua Inglesa (canônica), 2ª = Língua Espanhola
  - 2024: gabarito preliminar só cobre Q01–Q38 (limitação conhecida)

Uso:
    python extrair_paes.py
    python extrair_paes.py --ano 2023   # só este ano
"""
import argparse
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE       = Path(r"C:\PROJETOS\HENRYJR")
INPUT_DIR  = BASE / "DADOS" / "PAES_PROVAS"
OUTPUT_DIR = BASE / "DADOS" / "json_paes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Cabeçalhos de área → área canônica (normalizada sem acentos para compatibilidade)
AREA_HEADERS = {
    "LINGUAGENS":       "Linguagens, Codigos e suas Tecnologias",
    "LINGUA INGLESA":   "Linguagens, Codigos e suas Tecnologias",
    "LÍNGUA INGLESA":   "Linguagens, Codigos e suas Tecnologias",
    "LINGUA ESPANHOLA": "Linguagens, Codigos e suas Tecnologias",
    "LÍNGUA ESPANHOLA": "Linguagens, Codigos e suas Tecnologias",
    "CIENCIAS HUMANAS": "Ciencias Humanas e suas Tecnologias",
    "CIÊNCIAS HUMANAS": "Ciencias Humanas e suas Tecnologias",
    "MATEMATICA":       "Ciencias da Natureza e suas Tecnologias",
    "MATEMÁTICA":       "Ciencias da Natureza e suas Tecnologias",
}

# Faixas de questão por área (padrão para anos de 60 questões)
FAIXA_AREA_60 = {
    range(1, 21):  "Linguagens, Codigos e suas Tecnologias",
    range(21, 41): "Ciencias Humanas e suas Tecnologias",
    range(41, 61): "Ciencias da Natureza e suas Tecnologias",
}

# Para 2021 (44 questões por dia)
FAIXA_AREA_44 = {
    range(1, 16):  "Linguagens, Codigos e suas Tecnologias",
    range(16, 21): "Linguagens, Codigos e suas Tecnologias",
    range(21, 35): "Ciencias Humanas e suas Tecnologias",
    range(35, 45): "Ciencias da Natureza e suas Tecnologias",
}


def area_por_numero(num: int, total_qs: int) -> str:
    """Retorna área com base no número da questão e total de questões da prova."""
    faixas = FAIXA_AREA_44 if total_qs <= 44 else FAIXA_AREA_60
    for faixa, area in faixas.items():
        if num in faixa:
            return area
    return "Linguagens, Codigos e suas Tecnologias"


# ── Gabarito ─────────────────────────────────────────────────────────────────

def parse_gabarito_paes(pdf_path: Path) -> tuple[dict, dict]:
    """
    Extrai gabarito do PDF PAES.
    Retorna (gab_ingles, gab_espanhol).
    - gab_ingles: {numero(int): letra(str|None)}  — Língua Inglesa para Q16-Q20
    - gab_espanhol: {16:..., 17:..., 18:..., 19:..., 20:...}
    """
    doc = fitz.open(str(pdf_path))
    texto = ""
    for i in range(len(doc)):
        texto += doc[i].get_text() + "\n"
    doc.close()

    # Dividir em linhas limpas
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]

    gab_ingles: dict = {}
    gab_espanhol: dict = {}
    seen_16_20: dict = {}   # {num: count_of_occurrences}

    i = 0
    while i < len(linhas):
        m = re.match(r"^(\d{1,2})$", linhas[i])
        if m:
            num = int(m.group(1))
            if 1 <= num <= 60 and i + 1 < len(linhas):
                resp_raw = linhas[i + 1].strip()
                if re.match(r"^[A-Ea-e]$", resp_raw) or resp_raw.lower() == "nula":
                    resposta = None if resp_raw.lower() == "nula" else resp_raw.upper()

                    if 16 <= num <= 20:
                        cnt = seen_16_20.get(num, 0)
                        if cnt == 0:
                            gab_ingles[num] = resposta   # 1ª ocorrência = Inglesa
                        elif cnt == 1:
                            gab_espanhol[num] = resposta  # 2ª ocorrência = Espanhola
                        seen_16_20[num] = cnt + 1
                    else:
                        if num not in gab_ingles:
                            gab_ingles[num] = resposta
                    i += 2
                    continue
        i += 1

    return gab_ingles, gab_espanhol


# ── Parser de questões ────────────────────────────────────────────────────────

# Linhas a ignorar no enunciado (cabeçalhos, rodapés do PAES)
_IGNORAR = re.compile(
    r"^(?:\d{4}$"                          # só o ano (ex: 2024)
    r"|Processo Seletivo"
    r"|Acesso .? Educa"
    r"|UNIVERSIDADE ESTADUAL"
    r"|UEMA"
    r"|PAES \d{4}"
    r"|GABARITO"
    r"|São Luís"
    r"|Superintend"
    r"|Assessoria"
    r"|Divis"
    r"|SUCONS"
    r"|ASCONS"
    r"|DOCV"
    r"|DPSV"
    r")",
    re.IGNORECASE,
)


def _extrair_alternativas(bloco: str) -> dict[str, str]:
    """
    Extrai alternativas a-e do bloco da questão linha a linha.
    Robusto contra blocos sem lookahead — acumula linhas de continuação.
    """
    alternativas: dict[str, str] = {}
    letra_atual: str | None = None
    linhas_atual: list[str] = []

    for linha in bloco.split("\n"):
        m = re.match(r'^\s*([a-e])\)\s*(.*)', linha, re.IGNORECASE)
        if m:
            # Salva alternativa anterior antes de começar a nova
            if letra_atual is not None:
                texto = " ".join(linhas_atual).strip()
                if texto:
                    alternativas[letra_atual] = texto
            letra_atual = m.group(1).upper()
            inicio = m.group(2).strip()
            linhas_atual = [inicio] if inicio else []
        elif letra_atual is not None:
            # Linha de continuação da alternativa atual
            l = linha.strip()
            if l and not _IGNORAR.match(l):
                linhas_atual.append(l)

    # Salva última alternativa
    if letra_atual is not None:
        texto = " ".join(linhas_atual).strip()
        if texto:
            alternativas[letra_atual] = texto

    return alternativas


def parse_questoes_paes(pdf_path: Path) -> list[dict]:
    """
    Extrai questões do PDF da prova PAES (digital, texto).
    Retorna lista de dicts: {numero, area_raw, enunciado, alternativas, pagina_pdf}
    """
    doc = fitz.open(str(pdf_path))

    # Acumular texto com marcadores de página.
    # sort=True faz PyMuPDF ordenar blocos por posição Y antes de concatenar,
    # corrigindo PDFs com layout 2 colunas onde o marcador de questão fica
    # numa coluna lateral e o conteúdo na coluna principal.
    blocos: list[tuple[int, str]] = []   # (pagina, texto_pag)
    for i in range(len(doc)):
        blocos.append((i, doc[i].get_text(sort=True)))
    doc.close()

    texto_total = ""
    pag_offsets: list[tuple[int, int]] = []   # (offset_inicio, pagina)
    for pag, texto in blocos:
        pag_offsets.append((len(texto_total), pag))
        texto_total += texto

    def pagina_de_offset(off: int) -> int:
        pag = 0
        for o, p in pag_offsets:
            if o <= off:
                pag = p
        return pag

    # Encontrar marcadores de questão: "Questão NN" ou "Questão\nNN"
    quest_re = re.compile(r"Quest[aã]o\s+(\d{1,2})\b", re.IGNORECASE)
    matches = list(quest_re.finditer(texto_total))

    questoes_raw: list[dict] = []
    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num < 1 or num > 60:
            continue

        # Bloco da questão vai até o início da próxima (ou fim)
        inicio = m.start()
        fim = matches[idx + 1].start() if idx + 1 < len(matches) else len(texto_total)
        bloco = texto_total[inicio:fim]

        # Extrair alternativas  a) / b) / c) / d) / e)
        alternativas = _extrair_alternativas(bloco)

        if not alternativas:
            continue   # Sem alternativas = não é questão objetiva

        # Enunciado = tudo antes da 1ª alternativa
        primeiro_alt = re.search(r"^[a-e]\)", bloco, re.MULTILINE)
        enunciado_raw = bloco[len(m.group()):primeiro_alt.start()] if primeiro_alt else ""

        # Limpar enunciado
        paragrafos = []
        for linha in enunciado_raw.split("\n"):
            l = linha.strip()
            if l and not _IGNORAR.match(l):
                paragrafos.append(l)

        questoes_raw.append({
            "numero":    num,
            "enunciado": paragrafos,
            "alternativas": alternativas,
            "pagina_pdf": pagina_de_offset(inicio),
        })

    # Desduplicar:
    # - Q16-Q20 aparecem 2 vezes (Língua Inglesa + Espanhola); mantemos a 1ª (Inglesa).
    # - Algumas questões têm um bloco de "referência" (questão NN.) seguido do bloco
    #   real com alternativas; a referência é descartada acima (sem alternativas), mas
    #   por segurança preferimos sempre o bloco COM 5 alternativas completas.
    vistos: dict[int, dict] = {}
    for q in questoes_raw:
        num = q["numero"]
        if num not in vistos:
            vistos[num] = q
        elif num not in range(16, 21):
            # Para Q fora de 16-20: trocar se a versão atual tiver mais alternativas
            if len(q["alternativas"]) > len(vistos[num]["alternativas"]):
                vistos[num] = q

    return sorted(vistos.values(), key=lambda q: q["numero"])


# ── Montagem do banco ─────────────────────────────────────────────────────────

def montar_banco(q: dict, fonte: str, tipo: str, ano: int, dia: str,
                 gabarito_map: dict) -> dict:
    """Monta dict com todos os campos da tabela questoes."""
    num = q["numero"]
    gabarito = gabarito_map.get(num)  # None = sem gabarito ou anulada
    anulada = (gabarito is None and num in gabarito_map)

    return {
        "fonte":        fonte,
        "tipo":         tipo,
        "ano":          ano,
        "dia":          dia,
        "numero":       num,
        "area":         area_por_numero(num, max(gabarito_map.keys(), default=60)),
        "evento":       None,
        "turno":        None,
        "provedor":     None,
        "enunciado":    q["enunciado"],
        "alternativas": q["alternativas"],
        "gabarito":     gabarito,
        "confianca":    1.0,   # parser de texto = confiança máxima
        "revisado":     False,
        "anulada":      anulada,
        "tem_imagem":   False,
        "pagina_pdf":   q["pagina_pdf"],
    }


# ── Detecção de arquivos por ano ──────────────────────────────────────────────

def descobrir_arquivos(input_dir: Path) -> dict:
    """
    Retorna dict: {ano: {dia: (prova_path, gab_path)}}
    Exemplos de chave dia: 'dia1', 'dia2'
    """
    resultado: dict = {}

    for f in sorted(input_dir.glob("*.pdf")):
        nome = f.name

        # Detectar ANO
        m_ano = re.search(r"\b(20\d{2})\b", nome)
        if not m_ano:
            continue
        ano = int(m_ano.group(1))

        # Detectar DIA
        m_dia = re.search(r"DIA\s*(\d)", nome, re.IGNORECASE)
        dia = f"dia{m_dia.group(1)}" if m_dia else "dia1"

        # Tipo: prova ou gabarito
        is_gab = nome.upper().startswith("GABARITO") or "GAB" in nome.upper()

        if ano not in resultado:
            resultado[ano] = {}
        if dia not in resultado[ano]:
            resultado[ano][dia] = [None, None]   # [prova, gab]

        if is_gab:
            resultado[ano][dia][1] = f
        else:
            resultado[ano][dia][0] = f

    # Converter listas para tuples
    return {
        ano: {dia: tuple(pair) for dia, pair in dias.items()}
        for ano, dias in resultado.items()
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extrai questões PAES (UEMA)")
    parser.add_argument("--ano", type=int, help="Processar só este ano")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        print(f"✗ Pasta não encontrada: {INPUT_DIR}")
        sys.exit(1)

    arquivos = descobrir_arquivos(INPUT_DIR)
    if args.ano:
        arquivos = {args.ano: arquivos[args.ano]} if args.ano in arquivos else {}

    if not arquivos:
        print("Nenhum arquivo encontrado.")
        sys.exit(1)

    print(f"PAES_PROVAS — {len(arquivos)} anos | {sum(len(d) for d in arquivos.values())} aplicações")
    total_geral = 0

    for ano in sorted(arquivos):
        for dia, (prova_path, gab_path) in sorted(arquivos[ano].items()):
            if prova_path is None:
                print(f"\n  [{ano}] {dia.upper()} — prova não encontrada, pulando")
                continue

            print(f"\n  [{ano}] {dia.upper()}")
            print(f"  Extraindo {prova_path.name} ...")

            questoes = parse_questoes_paes(prova_path)
            print(f"    {len(questoes)} questões extraídas")

            gab_ingles: dict = {}
            if gab_path and gab_path.exists():
                gab_ingles, gab_esp = parse_gabarito_paes(gab_path)
                n_gab = len(gab_ingles)
                n_nulas = sum(1 for v in gab_ingles.values() if v is None)
                print(f"    {n_gab} gabaritos ({n_nulas} nulas) | Espanhola: {len(gab_esp)} entradas")
            else:
                print(f"    ⚠ Gabarito não encontrado")

            # Montar dicts de banco
            registros = [
                montar_banco(q, "PAES", "PROVA", ano, dia, gab_ingles)
                for q in questoes
            ]

            # Salvar JSON
            nome_json = f"paes_{ano}_{dia}.json"
            saida = OUTPUT_DIR / nome_json
            saida.write_text(
                json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            n = len(registros)
            total_geral += n
            n_com_gab = sum(1 for r in registros if r["gabarito"] is not None)
            print(f"    → {n} questões | {n_com_gab} com gabarito")
            print(f"    → Salvo: {saida.name}")

    print(f"\n✓ Total: {total_geral} questões PAES → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
