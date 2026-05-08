import fitz  # PyMuPDF
import json
import os
import re
import sys
import traceback
from pathlib import Path
from tqdm import tqdm

# Força UTF-8 no stdout para evitar erros de encoding no Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
PASTA_PROVAS  = r"C:\Projetos\henryjr\dados\provas"
PASTA_SAIDA   = r"C:\Projetos\henryjr\dados\json_v2"
PASTA_IMAGENS = r"C:\Projetos\henryjr\dados\imagens"

AREAS = {
    "dia1": [
        "Linguagens, Codigos e suas Tecnologias",   # Q01–Q45
        "Ciencias Humanas e suas Tecnologias",      # Q46–Q90
    ],
    "dia2": [
        "Ciencias da Natureza e suas Tecnologias",  # Q91–Q135
        "Matematica e suas Tecnologias",             # Q136–Q180
    ],
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def is_bold(flags):
    # PyMuPDF: bit 4 (16) = bold. Alguns PDFs usam bit 2 (4) para negrito.
    return bool(flags & 16) or bool(flags & 4)

def get_area(numero, dia):
    if dia == "dia1":
        return AREAS["dia1"][0] if numero <= 45 else AREAS["dia1"][1]
    else:
        return AREAS["dia2"][0] if numero <= 135 else AREAS["dia2"][1]

def limpar(t):
    return re.sub(r'\s+', ' ', t).strip()

# Padrões de "lixo" que aparecem nos PDFs entre questões (rodapés, códigos).
# A substituição é feita por espaço (não por vazio) para não colar palavras
# que estavam nas bordas da string suja.
_LIXO = re.compile(
    # ── "– AZUL – PÁGINA X ENEM 2009" / "- AMARELO - Página X" / "- AZUL - 1ª Aplicação"
    # Rodapé de página: cor do caderno + número de página ou edição ───────────
    r'[-–]\s*(?:AZUL|AMARELO|VERDE|ROSA|CINZA|BRANCO|LARANJA)\s*[-–]\s*'
    r'(?:P[AÁ]GIN[AÀ]\s*\d+|\d+[ªa°]\s*\w+)'
    r'(?:\s+(?:ENEM\s*)?20\d{2})?'
    r'|'

    # ── Títulos de área do ENEM (separam seções dentro do caderno) ───────────
    # Cobre variações com/sem acento e sufixos extras do 2024
    r'(?:'
    r'LINGUAGENS?\s*,?\s*C[OÓ]DIGOS?\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|CIENCIAS?\s+HUMANAS?\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|CIENCIAS?\s+DA\s+NATUREZA\s+E\s+SUAS\s+TECNOLOGIAS?'
    r'|MATEM[AÁ]TICA\s+E\s+SUAS\s+TECNOLOGIAS?'
    r')'
    r'(?:\s*E\s+REDA[CÇ][AÃ]O)?'           # "E REDAÇÃO" (2024)
    r'(?:\s*[•·]\s*\d+[°º]\s*DIA\s*[•·])?' # "• 2º DIA •" (2024)
    r'|'

    # ── Cabeçalho de área+dia (todas as variantes encontradas) ──────────────
    # "CH - 1º dia | CadernoPágina 3"
    # "CN – 1º dia CADERNOPÁGINA 4 ENEM 2009"
    # "6 LC - 1° dia | Caderno1ª Aplicação"
    # "LC - 1° dia | Caderno1ª Aplicação"
    r'(?:\d+\s*)?(?:CH|LC|CN|MT)\s*[-–]\s*\d+[°º]\w*\s+[Dd][Ii][Aa]\b'
    r'(?:\s*[|]?\s*Caderno\w*(?:\s+\d+[ªa]?\s*\w*|\s*\d*[ªa]?\s*\w*))?'
    r'(?:\s+ENEM\s*20\d{2})?'

    # ── Marca d'água ENEM repetida ──────────────────────────────────────────
    # "ENEM2024ENEM2024ENEM2024..." ou "ENEM 2022 ENEM 2022 ENEM 2022..."
    r'|(?:ENEM\s*20\d{2}){2,}'

    # ── Cabeçalho com bullet: "2 CN • 2º DIA • CADERNO 5 • AMARELO" ────────
    r'|\d+\s+[A-Z]{2,}\s*•[^•\n]+•[^\n]+'

    # ── Rodapé com traço: "2 –LC • 1º DIA…–" ────────────────────────────────
    r'|\d+\s*[–\-]\s*[A-Z]{2,}[\s\S]*?[–\-]'

    # ── Código de prova: "*010175AZ3*" ───────────────────────────────────────
    r'|\*[A-Z0-9]{6,}\*'

    # ── "QUESTÃO XX" no final do campo ──────────────────────────────────────
    r'|QUEST[AÃ]O\s+\d+\s*$'

    # ── "Qu..." truncado no final ────────────────────────────────────────────
    r'|[Qq]u\w{0,4}\.?\s*$'

    # ── Cabeçalho de seção: "Questões de 01 a 05 (opção espanhol)" ──────────
    r'|Quest[õo]es de \d+.*$'

    # ── "REDAÇÃO • 1º DIA • CADERNO X • COR" (2024) ─────────────────────────
    r'|REDA[CÇ][AÃ]O\s*[•\-–][^\n]+'

    # ── "RASCUNHO DA REDAÇÃO - COR - Página XX" (2012-2019) ──────────────────
    r'|RASCUNHO\s+DA\s+REDA[CÇ][AÃ]O[^\n]*'

    # ── "Caderno Página X" ou "Caderno 1ª Aplicação" sem prefixo de área ────
    r'|Caderno\s+(?:P[aá]gina\s*\d*|\d+[ªa]?\s*\w*)[^\n]{0,20}'

    # ── Watermark 2024 com encoding corrompido: "ENEM20E4ENEM20E4..." ────────
    r'|(?:ENEM20[A-Z0-9]{2}){2,}'

    # ── Sequências de números de página soltos: "28 29 30 31 32" ────────────
    r'|(?:\b\d{1,2}\s+){3,}\d{1,2}\b',

    re.IGNORECASE,
)

def limpar_lixo(t):
    # Substitui por espaço (não vazio) para preservar separação entre palavras
    return limpar(_LIXO.sub(' ', t))

# ─── EXTRAÇÃO DE GABARITO ─────────────────────────────────────────────────────
def extrair_gabarito(caminho_pdf, dia):
    """Lê PDF de gabarito e retorna {numero: letra}."""
    gabarito = {}
    if not os.path.exists(caminho_pdf):
        print(f"   ⚠️  Gabarito não encontrado: {caminho_pdf}")
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
        print(f"   🗝  Gabarito: {len(gabarito)} questões lidas")
    except Exception as e:
        print(f"   ⚠️  Erro no gabarito: {e}")
    return gabarito

# ─── COLETA DE LINHAS (spans) ─────────────────────────────────────────────────
class Linha:
    """Uma linha de texto com todos os seus spans e metadados de posição."""
    __slots__ = ("page_num", "y", "spans")

    def __init__(self, page_num, y, spans):
        self.page_num = page_num
        self.y        = y
        self.spans    = spans  # list[dict] — dicts do PyMuPDF

    def texto(self):
        return "".join(s["text"] for s in self.spans)


def coletar_linhas(doc):
    """
    Retorna lista de Linha respeitando a ordem de leitura de duas colunas:
    coluna esquerda da página inteira primeiro, depois coluna direita.
    Usa o centro horizontal do bloco para decidir a qual coluna pertence.
    """
    linhas = []
    for page_num, page in enumerate(doc):
        mid_x  = page.rect.width / 2
        blocos = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        col_esq, col_dir = [], []
        for bloco in blocos:
            if bloco["type"] != 0:
                continue
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
                if not spans:
                    continue
                y = raw_linha["bbox"][1]
                linhas.append(Linha(page_num, y, spans))
    return linhas

# ─── DETECÇÃO DE MARCADORES ───────────────────────────────────────────────────
def detectar_questao(linha, ano):
    """
    Retorna (numero, questao_x) se a linha for um marcador de questão,
    ou (None, None) caso contrário.
    questao_x é o x do span marcador — usado depois para detectar alternativas
    na mesma coluna.

    Padrões por ano:
      2011-2024 (geral): span negrito 'QUESTÃO 01'
      2019-2021:         span negrito 'Questão 01' tamanho ≈11
      2009:              span 'Questão' + número no span seguinte (mesma linha)
                         OU span isolado 'Questão' (número vem na próxima linha)
    """
    # Padrão moderno: 'QUESTÃO 01' ou 'Questão 01' num único span negrito
    for span in linha.spans:
        t = span["text"].strip()
        m = re.match(r'^(QUEST[AÃ]O|Quest[aã]o)\s+(\d{1,3})$', t)
        if m:
            return int(m.group(2)), span["origin"][0]

    # 2009: dois spans na mesma linha — 'Questão' e número separados
    if ano == 2009 and len(linha.spans) >= 2:
        t0 = linha.spans[0]["text"].strip()
        t1 = linha.spans[1]["text"].strip()
        if t0 in ('Questão', 'Questao') and re.match(r'^\d{1,3}$', t1):
            return int(t1), linha.spans[0]["origin"][0]

    # 2009 fallback: 'Questão' isolado (número vem na próxima linha)
    if ano == 2009:
        for span in linha.spans:
            if span["text"].strip() in ('Questão', 'Questao'):
                return -1, span["origin"][0]  # sentinela

    return None, None


def detectar_alt(linha, questao_x=0):
    """
    Retorna a letra da alternativa (A-E) se a linha começar com um marcador
    de alternativa, ou None.

    Padrão confirmado: primeiro span é a letra sozinha ('A', 'B'… ou 'A\t'),
    negrito. Questões podem cruzar colunas (enunciado à esquerda, alternativas
    à direita), por isso não filtramos pelo x absoluto.
    """
    if not linha.spans:
        return None
    primeiro = linha.spans[0]
    t = primeiro["text"].rstrip('\t').strip()
    if re.match(r'^[A-E]$', t) and is_bold(primeiro["flags"]):
        return t
    return None

# ─── CONSTRUÇÃO DE PARÁGRAFOS ─────────────────────────────────────────────────
def linhas_para_paragrafos(linhas):
    """
    Converte lista de Linha em lista de strings (parágrafos do enunciado).
    Novo parágrafo quando há gap vertical > 1,5× a altura da linha,
    ou quando a linha está vazia.
    """
    if not linhas:
        return []

    paragrafos = []
    bloco_atual = []
    y_anterior  = None
    altura_ref  = None

    for ln in linhas:
        texto = limpar(ln.texto())
        if not texto:
            if bloco_atual:
                paragrafos.append(" ".join(bloco_atual))
                bloco_atual = []
            y_anterior = None
            continue

        if y_anterior is not None and altura_ref:
            gap = ln.y - y_anterior
            if gap > altura_ref * 1.6:
                if bloco_atual:
                    paragrafos.append(" ".join(bloco_atual))
                    bloco_atual = []

        # Estima altura pela fonte do primeiro span
        if ln.spans:
            altura_ref = ln.spans[0].get("size", 10.0)

        bloco_atual.append(texto)
        y_anterior = ln.y

    if bloco_atual:
        paragrafos.append(" ".join(bloco_atual))

    return [p for p in paragrafos if p]

# ─── IMAGENS ──────────────────────────────────────────────────────────────────
def salvar_imagens(doc, page_num, ano, dia, num_questao):
    """Extrai e salva imagens da página; retorna lista de caminhos relativos."""
    caminhos = []
    pasta = Path(PASTA_IMAGENS) / str(ano) / dia
    pasta.mkdir(parents=True, exist_ok=True)

    pagina = doc[page_num]
    for idx, img_info in enumerate(pagina.get_images(full=True)):
        try:
            xref = img_info[0]
            base = doc.extract_image(xref)
            if len(base["image"]) < 2000:   # ignora ícones/decorações
                continue
            nome    = f"q{num_questao:03d}_{idx+1}.{base['ext']}"
            destino = pasta / nome
            destino.write_bytes(base["image"])
            caminhos.append(f"{ano}/{dia}/{nome}")
        except Exception:
            continue
    return caminhos

# ─── EXTRAÇÃO PRINCIPAL ───────────────────────────────────────────────────────
def processar_pdf(caminho_pdf, ano, dia, gabarito):
    """
    Extrai todas as questões de um PDF usando análise span-a-span.
    Retorna lista de dicts no formato v2.
    """
    if not os.path.exists(caminho_pdf):
        print(f"   ⚠️  PDF não encontrado: {caminho_pdf}")
        return []

    questoes  = []
    mapa_pags = {}  # numero_questao → page_num

    # Estado mutável encapsulado num dict para acesso em funções aninhadas
    st = {
        "num":            None,   # número da questão atual
        "questao_x":      0,      # x do marcador da questão (referência de coluna)
        "enunciado_lns":  [],     # linhas do enunciado
        "alternativas":   {},     # {letra: texto}
        "alt_atual":      None,   # letra em construção
        "alt_lns":        [],     # linhas da alternativa atual
        "aguarda_num_09": False,  # 2009: aguarda número na próxima linha
        "aguarda_x_09":   0,      # x do sentinela 2009
    }

    def fechar_alt():
        if st["alt_atual"] is not None:
            parags = linhas_para_paragrafos(st["alt_lns"])
            novo = limpar_lixo(" ".join(parags)) if parags else ""
            alt  = st["alt_atual"]
            # Salva se: tem conteúdo novo  OU  a letra ainda não foi registrada.
            # Não sobrescreve conteúdo existente com texto vazio (double-detection).
            if novo or alt not in st["alternativas"]:
                st["alternativas"][alt] = novo
        st["alt_atual"] = None
        st["alt_lns"]   = []

    def fechar_questao():
        fechar_alt()
        num = st["num"]
        if num is None:
            return

        valida_dia1 = (dia == "dia1" and 1 <= num <= 90)
        valida_dia2 = (dia == "dia2" and 91 <= num <= 180)
        if not (valida_dia1 or valida_dia2):
            _reset()
            return

        imagens = salvar_imagens(doc, mapa_pags.get(num, 0), ano, dia, num) \
                  if num in mapa_pags else []

        paragrafos = [limpar_lixo(p) for p in linhas_para_paragrafos(st["enunciado_lns"])
                      if limpar_lixo(p)]

        alts = st["alternativas"]
        questoes.append({
            "numero":       num,
            "ano":          ano,
            "dia":          dia,
            "area":         get_area(num, dia),
            "enunciado":    paragrafos,
            "comando":      "",       # separação automática do comando é fase futura
            "alternativas": alts,
            "gabarito":     gabarito.get(num),
            "confianca":    1.0 if len(alts) == 5 else 0.5,
            "revisado":     False,
            "imagens":      imagens,
            "tem_imagem":   len(imagens) > 0,
        })
        _reset()

    def _reset():
        st["num"]           = None
        st["questao_x"]     = 0
        st["enunciado_lns"] = []
        st["alternativas"]  = {}
        st["alt_atual"]     = None
        st["alt_lns"]       = []

    try:
        doc    = fitz.open(caminho_pdf)
        linhas = coletar_linhas(doc)

        for ln in linhas:

            # ── 2009: aguardando número após sentinela ──────────────────────
            if st["aguarda_num_09"]:
                t = ln.texto().strip()
                if re.match(r'^\d{1,3}$', t):
                    fechar_questao()
                    st["num"]       = int(t)
                    st["questao_x"] = st["aguarda_x_09"]
                    mapa_pags[st["num"]] = ln.page_num
                    st["aguarda_num_09"] = False
                    continue
                else:
                    st["aguarda_num_09"] = False  # não encontrou, desiste

            # ── Marcador de questão ─────────────────────────────────────────
            resultado, qx = detectar_questao(ln, ano)
            if resultado is not None:
                if resultado == -1:                 # 2009 sentinela
                    st["aguarda_num_09"] = True
                    st["aguarda_x_09"]   = qx
                    continue
                fechar_questao()
                st["num"]       = resultado
                st["questao_x"] = qx
                mapa_pags[resultado] = ln.page_num
                continue

            if st["num"] is None:
                continue   # ainda não chegou na primeira questão

            # ── Marcador de alternativa ─────────────────────────────────────
            letra = detectar_alt(ln, st["questao_x"])
            if letra:
                fechar_alt()
                st["alt_atual"] = letra
                # Conteúdo da mesma linha (spans após a letra)
                spans_conteudo = ln.spans[1:]
                if spans_conteudo:
                    st["alt_lns"].append(Linha(ln.page_num, ln.y, spans_conteudo))
                continue

            # ── Conteúdo ────────────────────────────────────────────────────
            if st["alt_atual"] is not None:
                st["alt_lns"].append(ln)
            else:
                st["enunciado_lns"].append(ln)

        fechar_questao()   # fecha a última questão do arquivo
        doc.close()

    except Exception as e:
        print(f"   ❌ Erro em {caminho_pdf}: {e}")
        traceback.print_exc()

    # Deduplicação: PDFs podem ter índices/capas com os primeiros números
    # repetidos. Mantém a versão com mais alternativas para cada número.
    vistas: dict = {}
    for q in questoes:
        n = q["numero"]
        if n not in vistas or len(q["alternativas"]) > len(vistas[n]["alternativas"]):
            vistas[n] = q
    questoes = sorted(vistas.values(), key=lambda q: q["numero"])

    return questoes

# ─── ORQUESTRADOR ─────────────────────────────────────────────────────────────
def processar_todos_os_anos(anos_alvo=None):
    Path(PASTA_SAIDA).mkdir(parents=True, exist_ok=True)
    Path(PASTA_IMAGENS).mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("  EXTRAÇÃO v2 — BANCO DE QUESTÕES ENEM")
    print("="*60)

    todos_anos = sorted([
        d for d in os.listdir(PASTA_PROVAS)
        if os.path.isdir(os.path.join(PASTA_PROVAS, d)) and d.isdigit()
    ])
    anos = [str(a) for a in anos_alvo] if anos_alvo else todos_anos
    print(f"\n📚 Processando: {', '.join(anos)}")

    total  = 0
    resumo = []

    for ano_str in tqdm(anos, desc="Anos", unit="ano"):
        ano_int = int(ano_str)

        # Proteção: JSON do 2010 foi preenchido manualmente
        if ano_int == 2010:
            print(f"\n⚠️  2010 ignorado — gabarito manual preservado em json/")
            continue

        pasta_ano   = os.path.join(PASTA_PROVAS, ano_str)
        questoes_ano = []

        print(f"\n{'─'*50}")
        print(f"📅 ANO: {ano_str}")

        for dia in ["dia1", "dia2"]:
            caminho_prova    = os.path.join(pasta_ano, f"{dia}.pdf")
            caminho_gabarito = os.path.join(pasta_ano, f"gabarito_{dia}.pdf")

            print(f"\n  📖 {dia}...")
            gabarito = extrair_gabarito(caminho_gabarito, dia)
            questoes = processar_pdf(caminho_prova, ano_int, dia, gabarito)

            completas = sum(1 for q in questoes if len(q["alternativas"]) == 5)
            print(f"   📝 {len(questoes)} questões | {completas} completas (5 alt.)")
            questoes_ano.extend(questoes)

        questoes_ano.sort(key=lambda q: q["numero"])

        if questoes_ano:
            caminho_json = os.path.join(PASTA_SAIDA, f"enem_{ano_str}.json")
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(questoes_ano, f, ensure_ascii=False, indent=2)

            total += len(questoes_ano)
            resumo.append({
                "ano":          ano_str,
                "total":        len(questoes_ano),
                "completas":    sum(1 for q in questoes_ano if len(q["alternativas"]) == 5),
                "com_gabarito": sum(1 for q in questoes_ano if q["gabarito"]),
                "com_imagem":   sum(1 for q in questoes_ano if q["tem_imagem"]),
            })
            print(f"\n  💾 enem_{ano_str}.json salvo ({len(questoes_ano)} questões)")

    # Salva resumo
    caminho_resumo = os.path.join(PASTA_SAIDA, "resumo_extracao_v2.json")
    with open(caminho_resumo, "w", encoding="utf-8") as f:
        json.dump({"total_geral": total, "por_ano": resumo}, f,
                  ensure_ascii=False, indent=2)

    print("\n\n" + "="*60)
    print("  RELATÓRIO FINAL")
    print("="*60)
    print(f"\n{'ANO':<8} {'TOTAL':<8} {'COMPLET':<10} {'C/GABAR':<10} {'C/IMG'}")
    print("─" * 50)
    for r in resumo:
        print(f"{r['ano']:<8} {r['total']:<8} {r['completas']:<10} "
              f"{r['com_gabarito']:<10} {r['com_imagem']}")
    print("─" * 50)
    print(f"{'TOTAL':<8} {total}")
    print(f"\n✅ Concluído! JSONs em: {PASTA_SAIDA}\n")

# ─── MODO TESTE ───────────────────────────────────────────────────────────────
def testar_ano(ano, dia="dia1", n=5):
    """
    Extrai e exibe as primeiras N questões de um ano/dia para inspeção rápida.
    Uso: python extrair_v2.py teste 2023 dia1 5
    """
    pasta_ano = os.path.join(PASTA_PROVAS, str(ano))
    caminho_prova    = os.path.join(pasta_ano, f"{dia}.pdf")
    caminho_gabarito = os.path.join(pasta_ano, f"gabarito_{dia}.pdf")

    print(f"\n{'='*60}")
    print(f"  TESTE — {ano} {dia.upper()}")
    print(f"{'='*60}")

    gabarito = extrair_gabarito(caminho_gabarito, dia)
    questoes = processar_pdf(caminho_prova, int(ano), dia, gabarito)

    completas = sum(1 for q in questoes if len(q["alternativas"]) == 5)
    print(f"\n✅ {len(questoes)} questões extraídas | {completas} completas")
    print(f"🗝  Com gabarito: {sum(1 for q in questoes if q['gabarito'])}")

    print(f"\n{'─'*50}")
    print(f"PRIMEIRAS {n} QUESTÕES:")
    print(f"{'─'*50}")

    for q in questoes[:n]:
        print(f"\n[Q{q['numero']:03d}] {q['area']}")
        print(f"  Gabarito: {q['gabarito']}  |  Confiança: {q['confianca']}"
              f"  |  Imagens: {len(q['imagens'])}")
        print(f"  Enunciado ({len(q['enunciado'])} parágrafo(s)):")
        for i, p in enumerate(q["enunciado"][:3]):
            print(f"    [{i+1}] {p[:110]}{'…' if len(p) > 110 else ''}")
        if len(q["enunciado"]) > 3:
            print(f"    … +{len(q['enunciado'])-3} parágrafos")
        print(f"  Alternativas ({len(q['alternativas'])}):")
        for letra, texto in q["alternativas"].items():
            print(f"    {letra}) {texto[:85]}{'…' if len(texto) > 85 else ''}")

    print(f"\n{'='*60}\n")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if not args:
        # Padrão: teste rápido no 2023 dia1
        testar_ano(2023, "dia1", 5)

    elif args[0] == "todos":
        processar_todos_os_anos()

    elif args[0] == "teste":
        ano = int(args[1]) if len(args) > 1 else 2023
        dia = args[2]      if len(args) > 2 else "dia1"
        n   = int(args[3]) if len(args) > 3 else 5
        testar_ano(ano, dia, n)

    else:
        # Lista de anos separados por vírgula: python extrair_v2.py 2022,2023
        anos = [a.strip() for a in args[0].split(",")]
        processar_todos_os_anos(anos_alvo=anos)
