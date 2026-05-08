from PIL import Image
import os
from pathlib import Path

PASTA_IMAGENS = r"C:\Projetos\henryjr\dados\imagens\2009"

def converter_jpx():
    print("\n" + "="*60)
    print("  CONVERSÃO .JPX → .JPG — 2009")
    print("="*60)

    if not os.path.exists(PASTA_IMAGENS):
        print(f"\n❌ Pasta não encontrada: {PASTA_IMAGENS}")
        return

    arquivos_jpx = []
    for root, dirs, files in os.walk(PASTA_IMAGENS):
        for f in files:
            if f.lower().endswith(".jpx"):
                arquivos_jpx.append(os.path.join(root, f))

    if not arquivos_jpx:
        print("\n⚠️  Nenhum arquivo .jpx encontrado.")
        return

    print(f"\n🔍 Encontrados: {len(arquivos_jpx)} arquivos .jpx")
    convertidos = 0
    erros = []

    for caminho_jpx in arquivos_jpx:
        caminho_jpg = caminho_jpx.rsplit(".", 1)[0] + ".jpg"
        try:
            img = Image.open(caminho_jpx).convert("RGB")
            img.save(caminho_jpg, "JPEG", quality=95)
            os.remove(caminho_jpx)
            print(f"  ✅ {os.path.basename(caminho_jpx)} → {os.path.basename(caminho_jpg)}")
            convertidos += 1
        except Exception as e:
            erros.append(f"{os.path.basename(caminho_jpx)}: {e}")
            print(f"  ❌ {os.path.basename(caminho_jpx)}: {e}")

    print(f"\n{'='*60}")
    print(f"  Convertidos: {convertidos}")
    print(f"  Erros:       {len(erros)}")

    if not erros:
        print("  🎉 Todos os .jpx convertidos com sucesso!")
    print(f"{'='*60}\n")

    # Atualiza referências no JSON do 2009
    import json
    caminho_json = r"C:\Projetos\henryjr\dados\json\enem_2009.json"
    if os.path.exists(caminho_json):
        with open(caminho_json, encoding="utf-8") as f:
            questoes = json.load(f)

        atualizadas = 0
        for q in questoes:
            novas_imagens = []
            for img in q.get("imagens", []):
                if img.endswith(".jpx"):
                    novas_imagens.append(img.rsplit(".", 1)[0] + ".jpg")
                    atualizadas += 1
                else:
                    novas_imagens.append(img)
            q["imagens"] = novas_imagens

        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(questoes, f, ensure_ascii=False, indent=2)

        print(f"  📄 JSON do 2009 atualizado: {atualizadas} referências corrigidas\n")

if __name__ == "__main__":
    converter_jpx()