import fitz
import os
import json
import shutil

PASTA_PROVAS  = r"C:\Projetos\henryjr\dados\provas\2009"
PASTA_IMAGENS = r"C:\Projetos\henryjr\dados\imagens\2009"
CAMINHO_JSON  = r"C:\Projetos\henryjr\dados\json\enem_2009.json"

def renderizar_paginas_2009():
    print("\n" + "="*60)
    print("  CORRIGINDO IMAGENS 2009 — RENDERIZAÇÃO DIRETA")
    print("="*60)

    # ── Limpa imagens pretas antigas ──────────────────────────────────
    print("\n🗑️  Removendo imagens pretas antigas...")
    removidas = 0
    for root, dirs, files in os.walk(PASTA_IMAGENS):
        for f in files:
            caminho = os.path.join(root, f)
            os.remove(caminho)
            removidas += 1
    print(f"   {removidas} arquivos removidos")

    # ── Renderiza páginas de cada dia ─────────────────────────────────
    mapa_paginas = {}  # numero_questao -> (dia, num_pagina)

    for dia in ["dia1", "dia2"]:
        caminho_pdf = os.path.join(PASTA_PROVAS, f"{dia}.pdf")
        if not os.path.exists(caminho_pdf):
            print(f"\n⚠️  {dia}.pdf não encontrado, pulando...")
            continue

        pasta_dia = os.path.join(PASTA_IMAGENS, dia)
        os.makedirs(pasta_dia, exist_ok=True)

        doc = fitz.open(caminho_pdf)
        total_pags = len(doc)
        print(f"\n📖 {dia}.pdf — {total_pags} páginas")

        paginas_com_questao = {}  # num_pagina -> [numeros de questão]

        # Primeira passagem: mapeia questões por página
        for num_pag in range(total_pags):
            pagina = doc[num_pag]
            texto = pagina.get_text()
            import re
            questoes_na_pag = re.findall(r'[Qq]uest[ãa]o\s+(\d+)', texto)
            if questoes_na_pag:
                paginas_com_questao[num_pag] = [int(q) for q in questoes_na_pag]
                for num_q in questoes_na_pag:
                    mapa_paginas[int(num_q)] = (dia, num_pag)

        # Segunda passagem: renderiza apenas páginas com questões
        renderizadas = 0
        for num_pag, questoes in paginas_com_questao.items():
            pagina = doc[num_pag]

            # Renderiza em alta resolução (3x = ~216 DPI)
            mat = fitz.Matrix(3, 3)
            pix = pagina.get_pixmap(matrix=mat, alpha=False)

            # Nome do arquivo inclui as questões da página
            qs = "_".join(str(q) for q in sorted(questoes)[:3])
            nome = f"pag{num_pag+1:03d}_q{qs}.jpg"
            caminho_saida = os.path.join(pasta_dia, nome)
            pix.save(caminho_saida)
            renderizadas += 1

        doc.close()
        print(f"   ✅ {renderizadas} páginas com questões renderizadas")

    # ── Atualiza JSON do 2009 ─────────────────────────────────────────
    print(f"\n📄 Atualizando JSON do 2009...")

    if not os.path.exists(CAMINHO_JSON):
        print(f"   ❌ JSON não encontrado: {CAMINHO_JSON}")
        return

    with open(CAMINHO_JSON, encoding="utf-8") as f:
        questoes = json.load(f)

    atualizadas = 0
    sem_pagina  = []

    for q in questoes:
        num = q["numero"]
        if num in mapa_paginas:
            dia, num_pag = mapa_paginas[num]
            # Busca o arquivo de página correspondente
            pasta_dia = os.path.join(PASTA_IMAGENS, dia)
            arquivos = [f for f in os.listdir(pasta_dia)
                        if f.startswith(f"pag{num_pag+1:03d}_")]
            if arquivos:
                caminho_relativo = f"2009/{dia}/{arquivos[0]}"
                q["imagens"]    = [caminho_relativo]
                q["tem_imagem"] = True
                atualizadas += 1
            else:
                q["imagens"]    = []
                q["tem_imagem"] = False
        else:
            q["imagens"]    = []
            q["tem_imagem"] = False
            sem_pagina.append(num)

    with open(CAMINHO_JSON, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    # ── Relatório ─────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"  Questões com página mapeada:  {atualizadas}")
    print(f"  Questões sem página:          {len(sem_pagina)}")
    if sem_pagina:
        print(f"  Números sem página: {sem_pagina[:20]}")
    print(f"\n  ⚠️  ATENÇÃO: As imagens agora são páginas completas.")
    print(f"  Na Correção 2 vamos recortar apenas a região de cada questão.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    renderizar_paginas_2009()