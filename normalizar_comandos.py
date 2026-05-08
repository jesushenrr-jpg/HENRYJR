"""
Normaliza o campo `comando` em todos os JSONs v2 (2010–2024).

Regra: o `comando` é SEMPRE o último parágrafo do `enunciado`.

Operações:
  1. 2010 — mescla linhas quebradas em parágrafos antes de mover o comando
  2. 2011–2024 — move diretamente o último item de `enunciado` para `comando`

Apenas atualiza questões onde `comando` está vazio.
Não toca no 2009 (já correto) nem no JSON v1 do 2010 (gabaritos manuais).
"""

import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")


# ── Mesclagem de linhas (necessário só para 2010) ──────────────────────────────

def _fim_sentenca(linha: str) -> bool:
    """True se a linha termina uma sentença (ponto, ! ou ?)."""
    s = linha.rstrip()
    if not s:
        return False
    ult = s[-1]
    if ult in ".!?":
        return True
    # fecha aspas/parêntese após ponto terminal
    if ult in ')"' and len(s) > 1 and s[-2] in ".!?":
        return True
    return False


def mesclar_linhas(pars: list[str]) -> list[str]:
    """
    Mescla uma lista de linhas (como o 2010 quebrado) em parágrafos reais.
    - Linhas sem pontuação terminal são unidas à linha seguinte com espaço.
    - Hifenização ao final (word wrap) é re-emendada sem espaço.
    """
    resultado: list[str] = []
    atual = ""

    for linha in pars:
        stripped = linha.strip()
        if not stripped:
            if atual.strip():
                resultado.append(atual.strip())
                atual = ""
            continue

        if not atual:
            atual = stripped
        elif _fim_sentenca(atual):
            resultado.append(atual.strip())
            atual = stripped
        elif atual.rstrip().endswith("-"):
            # hifenização de palavra — emenda sem espaço
            atual = atual.rstrip()[:-1] + stripped
        else:
            atual = atual.rstrip() + " " + stripped

    if atual.strip():
        resultado.append(atual.strip())

    return resultado


# ── Processamento por ano ──────────────────────────────────────────────────────

def processar_ano(ano: int) -> dict:
    jp = PASTA / f"enem_{ano}.json"
    if not jp.exists():
        return {"ignorado": 1}

    with open(jp, encoding="utf-8") as f:
        questoes = json.load(f)

    stats = {"atualizados": 0, "sem_enun": 0, "ja_ok": 0}

    for q in questoes:
        # Não sobrescreve comando já preenchido
        if (q.get("comando") or "").strip():
            stats["ja_ok"] += 1
            continue

        enun = q.get("enunciado") or []

        if ano == 2010:
            enun = mesclar_linhas(enun)

        if not enun:
            stats["sem_enun"] += 1
            continue

        # O último parágrafo do enunciado é o comando
        q["comando"] = enun[-1]
        q["enunciado"] = enun[:-1]
        stats["atualizados"] += 1

    with open(jp, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 68)
    print("  NORMALIZAÇÃO DE COMANDOS — ENEM 2010–2024")
    print("=" * 68)

    total_upd = 0
    for ano in range(2010, 2025):
        if ano == 2021:
            print(f"\n  {ano} — IGNORADO (será re-extraído via OCR)")
            continue

        stats = processar_ano(ano)
        upd = stats.get("atualizados", 0)
        total_upd += upd
        print(f"  {ano}: atualizados={upd}  sem_enun={stats.get('sem_enun',0)}"
              f"  ja_ok={stats.get('ja_ok',0)}")

    print(f"\n  Total atualizado: {total_upd} questões")
    print("=" * 68)


if __name__ == "__main__":
    main()
