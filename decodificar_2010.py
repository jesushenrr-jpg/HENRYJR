"""
Decodifica o texto corrompido dos JSONs do ENEM 2010.

A prova de 2010 usou uma fonte customizada que mapeia cada caractere
subtraindo 29 do código ASCII original. Para recuperar o texto original,
somamos 29 a cada caractere codificado.

Regra de decodificação:
  - Caracteres no intervalo 3–93 (exceto espaço=32): decoded = chr(ord(c) + 29)
  - Demais caracteres: mantidos como estão
    (inclui espaços normais, chars acentuados corrompidos >93, etc.)

Só aplica a decodificação em strings que contenham caracteres de controle
(ord 1–31), que sinalizam que o texto está no formato codificado.
"""

import json
import os
import re
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAMINHO_V1  = r"C:\Projetos\henryjr\dados\json\enem_2010.json"
CAMINHO_V2  = r"C:\Projetos\henryjr\dados\json_v2\enem_2010.json"


# ─── DECODER ──────────────────────────────────────────────────────────────────

def decode_text_2010(text: str) -> str:
    """Decodifica uma string da fonte customizada do 2010."""
    if not text:
        return text

    # Só decodifica se houver caracteres de controle (sinal de texto codificado)
    if not any(1 <= ord(c) <= 31 for c in text):
        return text

    result = []
    for c in text:
        code = ord(c)
        # Intervalo codificado: 3–93, excluindo espaço normal (32)
        if 3 <= code <= 93 and code != 32:
            result.append(chr(code + 29))
        else:
            result.append(c)

    decoded = "".join(result)
    # Normaliza espaços múltiplos gerados pelo processo
    decoded = re.sub(r'  +', ' ', decoded).strip()
    return decoded


def decode_value(v):
    """Decodifica um valor que pode ser str, list de str, ou dict de str."""
    if isinstance(v, str):
        return decode_text_2010(v)
    if isinstance(v, list):
        return [decode_text_2010(s) if isinstance(s, str) else s for s in v]
    if isinstance(v, dict):
        return {k: decode_text_2010(vv) if isinstance(vv, str) else vv
                for k, vv in v.items()}
    return v


CAMPOS_TEXTO = ["enunciado", "alternativas", "comando"]


def decodificar_json(caminho: str, versao: str):
    if not os.path.exists(caminho):
        print(f"[{versao}] Arquivo não encontrado: {caminho}")
        return

    with open(caminho, encoding="utf-8") as f:
        questoes = json.load(f)

    campos_modificados = 0
    for q in questoes:
        for campo in CAMPOS_TEXTO:
            if campo not in q:
                continue
            original = q[campo]
            decodificado = decode_value(original)
            if decodificado != original:
                q[campo] = decodificado
                campos_modificados += 1

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    print(f"[{versao}] {campos_modificados} campo(s) decodificado(s) → {caminho}")


# ─── VERIFICAÇÃO Q007 ─────────────────────────────────────────────────────────

def mostrar_q007(caminho: str, versao: str):
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        questoes = json.load(f)
    q = next((q for q in questoes if q["numero"] == 7), None)
    if not q:
        print(f"[{versao}] Q007 não encontrada")
        return

    print(f"\n{'='*60}")
    print(f"  Q007 — {versao}")
    print(f"{'='*60}")
    enunciado = q["enunciado"]
    if isinstance(enunciado, list):
        for p in enunciado[:5]:
            print(f"  {p[:120]}")
    else:
        print(f"  {str(enunciado)[:300]}")

    alts = q.get("alternativas", {})
    if isinstance(alts, dict):
        for letra, txt in list(alts.items())[:3]:
            print(f"  [{letra}] {str(txt)[:100]}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nMostrando Q007 ANTES da decodificação:")
    mostrar_q007(CAMINHO_V2, "v2")
    mostrar_q007(CAMINHO_V1, "v1")

    print("\n\nAplicando decodificação...")
    decodificar_json(CAMINHO_V2, "v2")
    decodificar_json(CAMINHO_V1, "v1")

    print("\n\nMostrando Q007 DEPOIS da decodificação:")
    mostrar_q007(CAMINHO_V2, "v2")
    mostrar_q007(CAMINHO_V1, "v1")

    print()
