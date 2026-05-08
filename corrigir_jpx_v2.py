import os
import json
import numpy as np

# Tenta diferentes bibliotecas para abrir JPX
def abrir_jpx(caminho):
    # Tentativa 1: imagecodecs (melhor suporte a JPEG 2000)
    try:
        import imagecodecs
        with open(caminho, "rb") as f:
            dados = f.read()
        img_array = imagecodecs.jpeg2k_decode(dados)
        return img_array, "imagecodecs"
    except Exception as e1:
        pass

    # Tentativa 2: OpenCV
    try:
        import cv2
        img = cv2.imread(caminho, cv2.IMREAD_UNCHANGED)
        if img is not None and img.sum() > 0:
            return img, "opencv"
    except Exception as e2:
        pass

    # Tentativa 3: PyMuPDF renderizando direto do PDF
    return None, "falhou"

def converter_jpx_v2():
    PASTA_IMAGENS = r"C:\Projetos\henryjr\dados\imagens\2009"
    PASTA_PROVAS  = r"C:\Projetos\henryjr\dados\provas\2009"
    CAMINHO_JSON  = r"C:\Projetos\henryjr\dados\json\enem_2009.json"

    print("\n" + "="*60)
    print("  CONVERSÃO .JPX → .JPG v2 — 2009")
    print("="*60)

    # Coleta todos os jpx restantes e os jpg pretos gerados antes
    arquivos = []
    for root, dirs, files in os.walk(PASTA_IMAGENS):
        for f in files:
            if f.lower().endswith((".jpx", ".jpg")):
                arquivos.append(os.path.join(root, f))

    print(f"\n🔍 Arquivos encontrados: {len(arquivos)}")

    # Verifica quais jpg estão pretos (soma de pixels muito baixa)
    try:
        import cv2
        pretos = []
        for caminho in arquivos:
            if caminho.endswith(".jpg"):
                img = cv2.imread(caminho)
                if img is None or img.sum() < 1000:
                    pretos.append(caminho)
                    print(f"  ⬛ {os.path.basename(caminho)} — imagem preta detectada")
        print(f"\n  Total de imagens pretas: {len(pretos)}")
    except:
        print("  ⚠️  OpenCV não disponível para detectar imagens pretas")

    # A melhor solução para 2009: renderizar as páginas direto do PDF
    print("\n🔄 Estratégia alternativa: renderizar direto dos PDFs do 2009...")
    print("   (Ignora os objetos de imagem corrompidos e renderiza a página inteira)")

    try:
        import fitz

        for dia in ["dia1", "dia2"]:
            caminho_pdf = os.path.join(PASTA_PROVAS, f"{dia}.pdf")
            if not os.path.exists(caminho_pdf):
                print(f"  ⚠️  {dia}.pdf não encontrado")
                continue

            pasta_dia = os.path.join(PASTA_IMAGENS, dia)
            os.makedirs(pasta_dia, exist_ok=True)

            doc = fitz.open(caminho_pdf)
            print(f"\n  📖 {dia}.pdf — {len(doc)} páginas")

            for num_pag, pagina in enumerate(doc):
                # Renderiza a página inteira em alta resolução
                mat = fitz.Matrix(3, 3)  # 3x = ~216 DPI
                pix = pagina.get_pixmap(matrix=mat)

                nome_pag = f"pagina_{num_pag+1:03d}.jpg"
                caminho_saida = os.path.join(pasta_dia, nome_pag)
                pix.save(caminho_saida)

            doc.close()
            print(f"  ✅ {len(doc)} páginas renderizadas em {pasta_dia}")

        print("\n" + "="*60)
        print("  ATENÇÃO: Estratégia mudada para renderização de páginas")
        print("  As imagens agora são páginas completas em alta resolução.")
        print("  O próximo script (Correção 2) vai recortar as regiões")
        print("  corretas de cada questão a partir dessas páginas.")
        print("="*60 + "\n")

    except ImportError:
        print("  ❌ PyMuPDF não encontrado. Rode: pip install pymupdf")

if __name__ == "__main__":
    converter_jpx_v2()