import fitz  # PyMuPDF
import json
import os
import re
import shutil
from tqdm import tqdm
from pathlib import Path

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
PASTA_PROVAS   = r"C:\Projetos\henryjr\dados\provas"
PASTA_SAIDA    = r"C:\Projetos\henryjr\dados\json"
PASTA_IMAGENS  = r"C:\Projetos\henryjr\dados\imagens"

AREAS = {
    "dia1": [
        "Linguagens, Codigos e suas Tecnologias",
        "Ciencias Humanas e suas Tecnologias"
    ],
    "dia2": [
        "Ciencias da Natureza e suas Tecnologias",
        "Matematica e suas Tecnologias"
    ]
}

# Questões por caderno (padrão ENEM moderno 2009+)
QUESTOES_DIA1 = list(range(1,  91))   # Q01–Q90
QUESTOES_DIA2 = list(range(91, 181))  # Q91–Q180

# ─── UTILITÁRIOS ──────────────────────────────────────────────────────────────
def limpar_texto(texto):
    """Remove espaços extras e caracteres indesejados."""
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.strip()
    return texto

def criar_pastas():
    """Cria as pastas de saída se não existirem."""
    Path(PASTA_SAIDA).mkdir(parents=True, exist_ok=True)
    Path(PASTA_IMAGENS).mkdir(parents=True, exist_ok=True)

# ─── EXTRAÇÃO DE GABARITO ─────────────────────────────────────────────────────
def extrair_gabarito(caminho_pdf, ano, dia):
    """
    Lê o PDF de gabarito e retorna um dicionário:
    { numero_questao (int): letra_correta (str) }
    """
    gabarito = {}

    if not os.path.exists(caminho_pdf):
        print(f"   ⚠️  Gabarito não encontrado: {caminho_pdf}")
        return gabarito

    try:
        doc = fitz.open(caminho_pdf)
        texto_completo = ""
        for pagina in doc:
            texto_completo += pagina.get_text()
        doc.close()

        # Padrão: número seguido de letra (ex: "1 A", "01 B", "1A", "01B")
        # Aceita variações comuns nos gabaritos do INEP
        padroes = [
            r'(\d{1,3})\s*[–\-:]?\s*([A-Ea-e])\b',
            r'QUESTAO\s*(\d{1,3})\s*([A-Ea-e])\b',
        ]

        for padrao in padroes:
            matches = re.findall(padrao, texto_completo, re.IGNORECASE)
            if matches:
                for num, letra in matches:
                    numero = int(num)
                    # Filtra apenas questões do intervalo do dia
                    if dia == "dia1" and 1 <= numero <= 90:
                        gabarito[numero] = letra.upper()
                    elif dia == "dia2" and 91 <= numero <= 180:
                        gabarito[numero] = letra.upper()
                break

        if gabarito:
            print(f"   ✅ Gabarito {dia}: {len(gabarito)} questões lidas")
        else:
            print(f"   ⚠️  Gabarito {dia}: nenhuma questão identificada no PDF")

    except Exception as e:
        print(f"   ❌ Erro ao ler gabarito {dia}: {e}")

    return gabarito

# ─── EXTRAÇÃO DE IMAGENS ──────────────────────────────────────────────────────
def extrair_imagens_pagina(pagina, ano, dia, num_questao, pasta_imagens):
    """
    Extrai imagens de uma página e salva em disco.
    Retorna lista de caminhos relativos das imagens salvas.
    """
    caminhos = []
    pasta_ano = os.path.join(pasta_imagens, str(ano), dia)
    Path(pasta_ano).mkdir(parents=True, exist_ok=True)

    lista_imagens = pagina.get_images(full=True)

    for idx, img in enumerate(lista_imagens):
        try:
            xref = img[0]
            doc = pagina.parent
            base_img = doc.extract_image(xref)
            dados = base_img["image"]
            extensao = base_img["ext"]

            # Ignora imagens muito pequenas (ícones, decorações)
            if len(dados) < 2000:
                continue

            nome_arquivo = f"q{num_questao:03d}_{idx+1}.{extensao}"
            caminho_completo = os.path.join(pasta_ano, nome_arquivo)
            caminho_relativo = f"{ano}/{dia}/{nome_arquivo}"

            with open(caminho_completo, "wb") as f:
                f.write(dados)

            caminhos.append(caminho_relativo)

        except Exception:
            continue

    return caminhos

# ─── EXTRAÇÃO DE QUESTÕES ─────────────────────────────────────────────────────
def extrair_questoes_pdf(caminho_pdf, ano, dia, gabarito, pasta_imagens):
    """
    Extrai todas as questões de um PDF de prova.
    Retorna lista de dicionários com os dados de cada questão.
    """
    questoes = []

    if not os.path.exists(caminho_pdf):
        print(f"   ⚠️  Prova não encontrada: {caminho_pdf}")
        return questoes

    try:
        doc = fitz.open(caminho_pdf)
        texto_completo = ""
        mapa_paginas = {}  # numero_questao -> numero_pagina

        # Primeira passagem: mapeia em qual página cada questão começa
        for num_pag, pagina in enumerate(doc):
            texto = pagina.get_text()
            matches = re.finditer(r'QUEST[AÃ]O\s+(\d{1,3})', texto, re.IGNORECASE)
            for match in matches:
                num_q = int(match.group(1))
                if num_q not in mapa_paginas:
                    mapa_paginas[num_q] = num_pag

        # Segunda passagem: extrai texto completo
        paginas_texto = []
        for pagina in doc:
            paginas_texto.append(pagina.get_text())
        texto_completo = "\n".join(paginas_texto)

        # Divide o texto em blocos por questão
        # Padrão: "QUESTÃO XX" ou "QUESTAO XX"
        separador = r'(QUEST[AÃ]O\s+\d{1,3})'
        blocos = re.split(separador, texto_completo, flags=re.IGNORECASE)

        questao_atual = None
        for i, bloco in enumerate(blocos):
            # Verifica se é um marcador de questão
            match_num = re.match(r'QUEST[AÃ]O\s+(\d{1,3})', bloco, re.IGNORECASE)
            if match_num:
                questao_atual = int(match_num.group(1))
                continue

            if questao_atual is None:
                continue

            # Filtra questões fora do intervalo do dia
            if dia == "dia1" and not (1 <= questao_atual <= 90):
                continue
            if dia == "dia2" and not (91 <= questao_atual <= 180):
                continue

            # Extrai as alternativas (A, B, C, D, E)
            alternativas = {}
            padrao_alt = r'\b([A-E])\s+((?:(?![A-E]\s).)+)'
            matches_alt = re.findall(padrao_alt, bloco, re.DOTALL)

            texto_enunciado = bloco
            if matches_alt:
                # Remove o bloco de alternativas do enunciado
                pos_primeira_alt = bloco.find(matches_alt[0][0])
                if pos_primeira_alt > 0:
                    texto_enunciado = bloco[:pos_primeira_alt]

                for letra, texto_alt in matches_alt:
                    alternativas[letra] = limpar_texto(texto_alt)

            enunciado = limpar_texto(texto_enunciado)

            # Extrai imagens da página onde a questão está
            imagens = []
            if questao_atual in mapa_paginas:
                num_pag = mapa_paginas[questao_atual]
                pagina = doc[num_pag]
                imagens = extrair_imagens_pagina(
                    pagina, ano, dia, questao_atual, pasta_imagens
                )

            # Determina a área de conhecimento
            if dia == "dia1":
                area = AREAS["dia1"][0] if questao_atual <= 45 else AREAS["dia1"][1]
            else:
                area = AREAS["dia2"][0] if questao_atual <= 135 else AREAS["dia2"][1]

            questao = {
                "numero":       questao_atual,
                "ano":          ano,
                "dia":          dia,
                "area":         area,
                "enunciado":    enunciado,
                "alternativas": alternativas,
                "gabarito":     gabarito.get(questao_atual, None),
                "imagens":      imagens,
                "tem_imagem":   len(imagens) > 0
            }

            questoes.append(questao)

        doc.close()

    except Exception as e:
        print(f"   ❌ Erro ao processar {caminho_pdf}: {e}")

    return questoes

# ─── PROCESSAMENTO PRINCIPAL ──────────────────────────────────────────────────
def processar_todos_os_anos():
    criar_pastas()

    print("\n" + "="*60)
    print("  EXTRAÇÃO DE QUESTÕES — BANCO DE QUESTÕES ENEM")
    print("="*60)

    if not os.path.exists(PASTA_PROVAS):
        print(f"\n❌ Pasta de provas não encontrada: {PASTA_PROVAS}")
        return

    anos = sorted([
        d for d in os.listdir(PASTA_PROVAS)
        if os.path.isdir(os.path.join(PASTA_PROVAS, d)) and d.isdigit()
    ])

    if not anos:
        print("\n❌ Nenhuma pasta de ano encontrada em:", PASTA_PROVAS)
        return

    print(f"\n📚 Anos encontrados: {', '.join(anos)}")
    print(f"📁 JSONs serão salvos em: {PASTA_SAIDA}")
    print(f"🖼️  Imagens serão salvas em: {PASTA_IMAGENS}\n")

    total_questoes = 0
    resumo = []

    for ano in tqdm(anos, desc="Processando anos", unit="ano"):
        pasta_ano = os.path.join(PASTA_PROVAS, ano)
        questoes_ano = []

        print(f"\n{'─'*50}")
        print(f"📅 ANO: {ano}")

        for dia in ["dia1", "dia2"]:
            caminho_prova    = os.path.join(pasta_ano, f"{dia}.pdf")
            caminho_gabarito = os.path.join(pasta_ano, f"gabarito_{dia}.pdf")

            print(f"\n  📖 Processando {dia}...")

            # Extrai gabarito
            gabarito = extrair_gabarito(caminho_gabarito, ano, dia)

            # Extrai questões
            questoes = extrair_questoes_pdf(
                caminho_prova, int(ano), dia, gabarito, PASTA_IMAGENS
            )

            print(f"   📝 Questões extraídas: {len(questoes)}")
            questoes_ano.extend(questoes)

        # Salva JSON do ano
        if questoes_ano:
            caminho_json = os.path.join(PASTA_SAIDA, f"enem_{ano}.json")
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(questoes_ano, f, ensure_ascii=False, indent=2)

            total_questoes += len(questoes_ano)
            resumo.append({
                "ano": ano,
                "total": len(questoes_ano),
                "com_gabarito": sum(1 for q in questoes_ano if q["gabarito"]),
                "com_imagem":   sum(1 for q in questoes_ano if q["tem_imagem"])
            })
            print(f"\n  💾 Salvo: enem_{ano}.json ({len(questoes_ano)} questões)")

    # Salva resumo geral
    caminho_resumo = os.path.join(PASTA_SAIDA, "resumo_extracao.json")
    with open(caminho_resumo, "w", encoding="utf-8") as f:
        json.dump({
            "total_geral": total_questoes,
            "por_ano": resumo
        }, f, ensure_ascii=False, indent=2)

    # Relatório final
    print("\n\n" + "="*60)
    print("  RELATÓRIO FINAL DA EXTRAÇÃO")
    print("="*60)
    print(f"\n{'ANO':<8} {'QUESTÕES':<12} {'COM GABARITO':<16} {'COM IMAGEM'}")
    print("─" * 50)
    for item in resumo:
        print(f"{item['ano']:<8} {item['total']:<12} {item['com_gabarito']:<16} {item['com_imagem']}")
    print("─" * 50)
    print(f"{'TOTAL':<8} {total_questoes}")
    print(f"\n✅ Extração concluída! JSONs salvos em: {PASTA_SAIDA}")
    print(f"📄 Resumo salvo em: resumo_extracao.json\n")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    processar_todos_os_anos()