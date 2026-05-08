import fitz
import os

# Aponta para o gabarito_dia1 de 2010 — ajuste se necessário
CAMINHO_GAB = r"C:\Projetos\henryjr\dados\provas\2010\gabarito_dia1.pdf"

def investigar():
    print("\n" + "="*60)
    print("  INVESTIGAÇÃO — GABARITO 2010")
    print("="*60)

    doc = fitz.open(CAMINHO_GAB)
    print(f"\n📄 Total de páginas: {len(doc)}")

    # ── TESTE B: Verifica anotações embutidas ─────────────────────────
    print("\n🔍 TESTE 1 — Anotações embutidas no PDF:")
    total_anotacoes = 0
    for num_pag, pagina in enumerate(doc):
        anotacoes = pagina.annots()
        lista = list(anotacoes) if anotacoes else []
        if lista:
            total_anotacoes += len(lista)
            print(f"   Página {num_pag+1}: {len(lista)} anotação(ões)")
            for anot in lista[:3]:  # Mostra as 3 primeiras
                print(f"     - Tipo: {anot.type} | Cor: {anot.colors} | Rect: {anot.rect}")

    if total_anotacoes == 0:
        print("   ❌ Nenhuma anotação encontrada — Opção B não funciona")
    else:
        print(f"\n   ✅ {total_anotacoes} anotações encontradas — Opção B pode funcionar!")

    # ── TESTE A: Analisa cores dominantes por página ───────────────────
    print("\n🎨 TESTE 2 — Análise de cores (busca por verde/círculo):")
    pagina_teste = doc[7]  # Página 8 (onde estão as questões 103-105 da imagem)
    
    # Renderiza a página em alta resolução
    mat = fitz.Matrix(2, 2)
    pix = pagina_teste.get_pixmap(matrix=mat)
    
    # Conta pixels verdes (R < 150, G > 150, B < 150)
    pixels_verdes = 0
    pixels_verdes_claros = 0
    total_pixels = pix.width * pix.height
    
    for y in range(0, pix.height, 3):  # Amostragem a cada 3 pixels
        for x in range(0, pix.width, 3):
            pixel = pix.pixel(x, y)
            r, g, b = pixel[0], pixel[1], pixel[2]
            # Verde escuro/médio (típico de marcações)
            if g > 120 and r < 100 and b < 100:
                pixels_verdes += 1
            # Verde claro (pode ser highlight)
            if g > 150 and r < 180 and b < 180 and g > r and g > b:
                pixels_verdes_claros += 1
    
    print(f"   Página 8 — pixels verdes escuros: {pixels_verdes}")
    print(f"   Página 8 — pixels verdes claros:  {pixels_verdes_claros}")
    
    if pixels_verdes > 50 or pixels_verdes_claros > 200:
        print("   ✅ Verde detectado — Opção A deve funcionar!")
    else:
        print("   ⚠️  Poucos pixels verdes — pode ser outra cor de marcação")

    # ── Verifica o tom exato da cor de marcação ────────────────────────
    print("\n🖌️  TESTE 3 — Amostragem de cores na região das alternativas:")
    print("   (Procurando pixels que fogem do preto/branco)")
    
    cores_encontradas = {}
    for y in range(0, pix.height, 5):
        for x in range(0, pix.width, 5):
            pixel = pix.pixel(x, y)
            r, g, b = pixel[0], pixel[1], pixel[2]
            # Ignora preto, branco e cinza
            if r > 200 and g > 200 and b > 200:
                continue
            if r < 30 and g < 30 and b < 30:
                continue
            if abs(r-g) < 20 and abs(g-b) < 20:
                continue
            # Agrupa por tom dominante
            if r > g and r > b:
                tom = "VERMELHO"
            elif g > r and g > b:
                tom = "VERDE"
            elif b > r and b > g:
                tom = "AZUL"
            else:
                tom = "OUTRO"
            cores_encontradas[tom] = cores_encontradas.get(tom, 0) + 1
    
    if cores_encontradas:
        print("   Cores coloridas detectadas na página:")
        for cor, qtd in sorted(cores_encontradas.items(), key=lambda x: -x[1]):
            print(f"     {cor}: {qtd} pixels amostrados")
    else:
        print("   ⚠️  Apenas preto e branco detectados nesta página")

    doc.close()
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    investigar()