"""
Auditoria completa de imagens do banco de questões ENEM (2009–2024).

Verifica para cada questão:
1. Consistência entre tem_imagem e lista imagens
2. Existência dos arquivos no disco
3. Padrões suspeitos (arquivos _3.png = render completo, etc.)
4. Questões com imagens_alternativas
5. Resumo por ano e global

Saída: relatório em texto + salva JSON com todos os problemas
"""

import json, sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA_JSON = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_IMG  = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")

# Sufixos suspeitos: render de página inteira, não imagem específica da questão
# O padrão _3.png / _4.png aparece quando o extrator salva renders de página inteira
PAT_RENDER_PAGINA = {"_3.png", "_4.png", "_5.png"}

def checar_arquivo(rel_path: str) -> bool:
    """Retorna True se o arquivo existe no disco."""
    return (PASTA_IMG / rel_path).exists()


def dimensoes(rel_path: str):
    """Retorna (w, h) do arquivo de imagem, ou (0, 0) se erro."""
    fp = PASTA_IMG / rel_path
    if not fp.exists():
        return (0, 0)
    try:
        from PIL import Image as PILImage
        img = PILImage.open(fp)
        return img.size
    except Exception:
        return (0, 0)


def eh_barcode(w: int, h: int) -> bool:
    """Barra de código: largura ≤ 65px e altura ≥ 2000px."""
    return w <= 65 and h >= 2000


def media_brilho_arquivo(rel_path: str) -> float:
    """Brilho médio [0-255] da imagem. Retorna 255 se erro."""
    import numpy as np
    fp = PASTA_IMG / rel_path
    if not fp.exists():
        return 255.0
    try:
        from PIL import Image as PILImage
        img = PILImage.open(fp).convert("L")
        return float(np.array(img).mean())
    except Exception:
        return 255.0


def tamanho_arquivo_kb(rel_path: str) -> float:
    """Tamanho do arquivo em KB, ou -1 se não existe."""
    fp = PASTA_IMG / rel_path
    if fp.exists():
        return fp.stat().st_size / 1024
    return -1


def auditar_ano(ano: int, questoes: list) -> dict:
    """
    Audita todas as questões de um ano. Retorna dict com listas de problemas.
    """
    problemas = defaultdict(list)

    for q in questoes:
        num  = q["numero"]
        dia  = q.get("dia", "?")
        tem  = q.get("tem_imagem", False)
        imgs = q.get("imagens") or []
        alts = q.get("imagens_alternativas") or {}

        # ── Consistência tem_imagem ↔ imagens ──────────────────────────────
        if tem and not imgs:
            problemas["tem_imagem_sem_lista"].append(
                f"{ano} Q{num:03d} ({dia}): tem_imagem=True mas imagens=[]"
            )
        if not tem and imgs:
            problemas["lista_sem_tem_imagem"].append(
                f"{ano} Q{num:03d} ({dia}): imagens={imgs} mas tem_imagem=False/None"
            )

        # ── Verificar existência de cada arquivo de imagem ─────────────────
        for rel in imgs:
            if not checar_arquivo(rel):
                problemas["arquivo_faltando"].append(
                    f"{ano} Q{num:03d}: FALTA {rel}"
                )

        # ── Barra de código (barcode strip) restante ──────────────────────
        for rel in imgs:
            w, h = dimensoes(rel)
            if eh_barcode(w, h):
                problemas["barcode_residual"].append(
                    f"{ano} Q{num:03d}: barcode residual {rel} ({w}×{h})"
                )

        # ── Imagens quase pretas (brilho médio < 10) ───────────────────────
        for rel in imgs:
            brilho = media_brilho_arquivo(rel)
            if brilho < 10:
                problemas["imagem_preta"].append(
                    f"{ano} Q{num:03d}: {rel} (brilho={brilho:.1f})"
                )

        # ── Arquivos muito pequenos (< 1.5 KB) — quase certamente vazio ───
        for rel in imgs:
            kb = tamanho_arquivo_kb(rel)
            if 0 < kb < 1.5:
                problemas["arquivo_minusculo"].append(
                    f"{ano} Q{num:03d}: {rel} apenas {kb:.1f} KB"
                )

        # ── imagens_alternativas: verificar existência ─────────────────────
        for letra, rel in alts.items():
            if not checar_arquivo(rel):
                problemas["alt_img_faltando"].append(
                    f"{ano} Q{num:03d}: FALTA alt_{letra} → {rel}"
                )

    return dict(problemas)


def main():
    todos_problemas = {}
    estatisticas = []

    for json_path in sorted(PASTA_JSON.glob("enem_*.json")):
        ano = int(json_path.stem.split("_")[1])
        with open(json_path, encoding="utf-8") as f:
            questoes = json.load(f)

        probs = auditar_ano(ano, questoes)
        todos_problemas[ano] = probs

        n_tem   = sum(1 for q in questoes if q.get("tem_imagem"))
        n_imgs  = sum(1 for q in questoes if q.get("imagens"))
        n_alts  = sum(1 for q in questoes if q.get("imagens_alternativas"))
        n_arqs  = sum(len(q.get("imagens") or []) for q in questoes)
        n_prob  = sum(len(v) for v in probs.values())

        estatisticas.append({
            "ano": ano, "total": len(questoes),
            "tem_imagem": n_tem, "com_lista_imgs": n_imgs,
            "total_arquivos": n_arqs, "com_img_alts": n_alts,
            "problemas": n_prob,
        })

    # ── Relatório no terminal ──────────────────────────────────────────────
    print("=" * 72)
    print("  AUDITORIA DE IMAGENS — ENEM 2009–2024")
    print("=" * 72)

    print(f"\n{'Ano':>5} {'Questões':>9} {'tem_img':>8} {'arqs':>6} {'img_alts':>9} {'problemas':>10}")
    print("-" * 55)
    total_probs = 0
    for e in estatisticas:
        print(f"{e['ano']:>5} {e['total']:>9} {e['tem_imagem']:>8} "
              f"{e['total_arquivos']:>6} {e['com_img_alts']:>9} {e['problemas']:>10}")
        total_probs += e["problemas"]
    print("-" * 55)
    print(f"{'TOTAL':>5} {sum(e['total'] for e in estatisticas):>9} "
          f"{sum(e['tem_imagem'] for e in estatisticas):>8} "
          f"{sum(e['total_arquivos'] for e in estatisticas):>6} "
          f"{sum(e['com_img_alts'] for e in estatisticas):>9} "
          f"{total_probs:>10}")

    # ── Detalhe por categoria de problema ─────────────────────────────────
    cats = [
        "arquivo_faltando",
        "alt_img_faltando",
        "tem_imagem_sem_lista",
        "lista_sem_tem_imagem",
        "barcode_residual",
        "imagem_preta",
        "arquivo_minusculo",
    ]
    LABELS = {
        "arquivo_faltando":     "Arquivo inexistente (enunciado)",
        "alt_img_faltando":     "Arquivo inexistente (alternativas)",
        "tem_imagem_sem_lista": "tem_imagem=True mas lista vazia",
        "lista_sem_tem_imagem": "Lista preenchida mas tem_imagem=False",
        "barcode_residual":     "Barra de código residual (62×2244)",
        "imagem_preta":         "Imagem quase preta (brilho < 10)",
        "arquivo_minusculo":    "Arquivo < 1.5 KB (provavelmente vazio)",
    }

    for cat in cats:
        itens = []
        for ano, probs in todos_problemas.items():
            itens.extend(probs.get(cat, []))
        if not itens:
            continue
        print(f"\n{'─'*72}")
        print(f"  [{len(itens)}] {LABELS[cat]}")
        print(f"{'─'*72}")
        for it in itens:
            print(f"  {it}")

    # ── Salvar JSON com todos os problemas ────────────────────────────────
    out_path = PASTA_JSON / "auditoria_imagens.json"
    saida = {
        "estatisticas": estatisticas,
        "problemas": {str(k): v for k, v in todos_problemas.items()},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"\n  Relatório salvo: {out_path}")
    print(f"\n{'='*72}\n  CONCLUÍDO — {total_probs} problema(s) encontrado(s)\n{'='*72}")


if __name__ == "__main__":
    main()
