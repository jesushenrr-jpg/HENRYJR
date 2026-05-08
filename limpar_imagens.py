"""
Limpeza e correção do banco de imagens ENEM (2009–2024).

Problemas tratados:
  A. Barras de código (62×2244px) — artefato de extração 2024/2019
  B. Elementos decorativos do PDF (bullets, separadores) — <100px menor dimensão
  C. Linhas separadoras finas — min_dim ≤ 55px, max_dim ≥ 200px, < 5KB
  D. Logos/cabeçalhos de página em fundo escuro — identificados manualmente
  E. Conversão .jpx → .jpg (2009 / 2024) — incompatibilidade com browsers

Ação padrão: remove do JSON; converte .jpx in-place.
Os arquivos originais NÃO são deletados (ficam no disco como backup).
"""

import json, shutil, sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA_JSON = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")
PASTA_IMG  = Path(r"C:\PROJETOS\HENRYJR\dados\imagens")

# ─────────────────────────────────────────────────────────────────────────────
# Listas de imagens identificadas manualmente como artefatos/lixo de PDF
# (além das regras automáticas abaixo)
# ─────────────────────────────────────────────────────────────────────────────
ARTEFATOS_MANUAIS = {
    # ── Logos / cabeçalhos de página em fundo escuro ──────────────────────
    # 2022/Q004 dia1: logo INALI + símbolo em fundo preto (476×92)
    "2022/dia1/q004_2.jpeg",
    "2022/dia1/q005_2.jpeg",   # mesma fonte — confirmar logo INALI
    # ── 2009: arquivos JPX extremamente pequenos = fundo preto / falhos ───
    # Todos os .jpx com < 5 KB E dimensão mínima < 200px são convertidos
    # (regra automática D cobre isso)
}


def dimensoes(rel_path: str):
    """Retorna (w, h) do arquivo de imagem, ou (0, 0) se erro."""
    fp = PASTA_IMG / rel_path
    if not fp.exists():
        return (0, 0)
    try:
        img = Image.open(fp)
        return img.size
    except Exception:
        return (0, 0)


def eh_artefato(rel_path: str, w: int, h: int, kb: float) -> str | None:
    """
    Retorna descrição do artefato se o arquivo deve ser removido do JSON,
    ou None se deve ser mantido.
    """
    if rel_path in ARTEFATOS_MANUAIS:
        return "artefato manual (logo/cabeçalho)"

    # A. Barra de código de barras: largura ≤ 65px e altura ≥ 2000px
    if w <= 65 and h >= 2000:
        return f"barra de código ({w}×{h})"

    # B. Elemento decorativo minúsculo: menor dimensão ≤ 75px, KB < 5
    min_d = min(w, h)
    if min_d > 0 and min_d <= 75 and kb < 5:
        return f"elemento decorativo ({w}×{h}, {kb:.1f}KB)"

    # C. Separador/linha fina: min_dim ≤ 55px, max_dim ≥ 200px, KB < 5
    max_d = max(w, h)
    if min_d > 0 and min_d <= 55 and max_d >= 200 and kb < 5:
        return f"separador fino ({w}×{h}, {kb:.1f}KB)"

    return None


def converter_jpx(rel_path: str) -> str | None:
    """
    Converte .jpx → .jpg usando Pillow. Retorna novo caminho relativo
    ou None se erro.
    """
    src = PASTA_IMG / rel_path
    if not src.exists():
        return None
    try:
        img = Image.open(src)
        # Converter para RGB se necessário (palette ou L)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        dst_rel = rel_path.replace(".jpx", ".jpg")
        dst = PASTA_IMG / dst_rel
        img.save(str(dst), "JPEG", quality=92)
        return dst_rel
    except Exception as e:
        print(f"    ERRO ao converter {rel_path}: {e}")
        return None


def processar_json(ano: int) -> dict:
    """
    Aplica limpeza ao JSON do ano. Retorna estatísticas.
    """
    json_path = PASTA_JSON / f"enem_{ano}.json"
    with open(json_path, encoding="utf-8") as f:
        questoes = json.load(f)

    stats = {
        "artefatos_removidos": 0,
        "jpx_convertidos": 0,
        "questoes_afetadas": 0,
        "tem_imagem_corrigido": 0,
    }
    log = []

    for q in questoes:
        imgs_originais = list(q.get("imagens") or [])
        imgs_novas = []
        modificou = False

        for rel in imgs_originais:
            fp = PASTA_IMG / rel
            kb = fp.stat().st_size / 1024 if fp.exists() else 0
            w, h = dimensoes(rel)

            # ── Conversão .jpx → .jpg ─────────────────────────────────────
            if rel.lower().endswith(".jpx"):
                novo_rel = converter_jpx(rel)
                if novo_rel:
                    rel = novo_rel
                    stats["jpx_convertidos"] += 1
                    modificou = True
                    log.append(f"  {ano} Q{q['numero']:03d}: .jpx→.jpg  {novo_rel}")

            # Re-calcular dimensões após conversão (extensão pode ter mudado)
            w2, h2 = dimensoes(rel)
            kb2 = (PASTA_IMG / rel).stat().st_size / 1024 if (PASTA_IMG / rel).exists() else kb

            # ── Verificar se é artefato ───────────────────────────────────
            motivo = eh_artefato(rel, w2 or w, h2 or h, kb2 or kb)
            if motivo:
                stats["artefatos_removidos"] += 1
                modificou = True
                log.append(f"  {ano} Q{q['numero']:03d}: REMOVE '{rel}' [{motivo}]")
            else:
                imgs_novas.append(rel)

        if modificou:
            q["imagens"] = imgs_novas
            stats["questoes_afetadas"] += 1

            # Corrigir tem_imagem se a lista ficou vazia
            if not imgs_novas and not q.get("imagens_alternativas"):
                if q.get("tem_imagem"):
                    q["tem_imagem"] = False
                    stats["tem_imagem_corrigido"] += 1
                    log.append(f"  {ano} Q{q['numero']:03d}: tem_imagem → False (lista vazia)")

    # Salvar JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    for linha in log:
        print(linha)

    return stats


def main():
    print("=" * 72)
    print("  LIMPEZA DE IMAGENS — ENEM 2009–2024")
    print("=" * 72)

    total_stats = {
        "artefatos_removidos": 0,
        "jpx_convertidos": 0,
        "questoes_afetadas": 0,
        "tem_imagem_corrigido": 0,
    }

    for json_path in sorted(PASTA_JSON.glob("enem_*.json")):
        ano = int(json_path.stem.split("_")[1])
        print(f"\n{'─'*72}")
        print(f"  Ano {ano}")
        print(f"{'─'*72}")
        stats = processar_json(ano)
        for k, v in stats.items():
            total_stats[k] += v
        print(f"  → artefatos={stats['artefatos_removidos']}  "
              f"jpx={stats['jpx_convertidos']}  "
              f"questoes={stats['questoes_afetadas']}  "
              f"tem_img_fix={stats['tem_imagem_corrigido']}")

    print(f"\n{'='*72}")
    print(f"  TOTAL: artefatos={total_stats['artefatos_removidos']}  "
          f"jpx={total_stats['jpx_convertidos']}  "
          f"questoes={total_stats['questoes_afetadas']}  "
          f"tem_img_fix={total_stats['tem_imagem_corrigido']}")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
