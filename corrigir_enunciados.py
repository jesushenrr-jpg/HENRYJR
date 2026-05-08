"""
Corrige questões onde enunciado=[] mas comando contém múltiplas frases.

Isso ocorre quando o extrator produziu um único parágrafo para toda a questão
(passagem + comando misturados), e o normalizador moveu esse parágrafo inteiro
para o campo `comando`.

Regra aplicada: "penúltimo ponto"
  - Encontra todas as posições de fim de frase no texto do `comando`
    (`.`, `!`, `?` seguido de espaço+maiúscula ou fim da string)
  - A posição APÓS o penúltimo sinal delimita o início do comando real
  - Tudo antes → enunciado (1 parágrafo)
  - Tudo depois → comando

Condição de aplicação: enunciado=[] E o `comando` tem pelo menos 2 fins de frase.

Aplica a todos os anos em dados/json_v2/, exceto 2009 (já correto).
"""

import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")

# Fim de frase: . ! ? seguido de espaço + maiúscula, aspas, ou fim da string
# Exclui abreviações comuns do contexto ENEM (ex.: "Art. 70", "Fig. 1", "pág. 3")
PAT_FIM = re.compile(
    r'[.!?](?=\s+[A-ZÁÀÃÂÉÊÍÓÕÔÚÇÑ"«“‘]|\s*$)'
)

# Abreviações que NÃO terminam frase — o ponto depois não é fim de sentença
ABREVIACOES = re.compile(
    r'\b(Art|Fig|Pág|pág|vol|Vol|op|cit|Dr|Dra|Sr|Sra|Prof|Profa|'
    r'ed|Ed|cap|Cap|sec|Sec|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.',
    re.IGNORECASE,
)


def fins_de_frase(texto: str) -> list[int]:
    """
    Retorna lista de posições (final do sinal) onde há fim de frase real,
    ignorando abreviações conhecidas.
    """
    posicoes = []
    for m in PAT_FIM.finditer(texto):
        pos = m.start()
        # Verificar se é abreviação: olhar o token que precede o ponto
        trecho_antes = texto[max(0, pos - 10) : pos]
        if ABREVIACOES.search(trecho_antes):
            continue
        posicoes.append(m.end())   # posição APÓS o sinal
    return posicoes


def separar_pelo_penultimo_ponto(texto: str) -> tuple[list[str], str]:
    """
    Divide o texto no penúltimo fim de frase.
    Retorna (lista_de_paragrafos_enunciado, texto_comando).
    Se não houver penúltimo ponto, retorna ([], texto) — sem divisão.
    """
    fins = fins_de_frase(texto)

    if len(fins) < 2:
        return [], texto.strip()

    split_pos = fins[-2]   # posição após o penúltimo sinal de fim de frase

    enun_texto = texto[:split_pos].strip()
    cmd_texto  = texto[split_pos:].strip()

    return ([enun_texto] if enun_texto else []), cmd_texto


def corrigir_ano(ano: int) -> dict:
    jp = PASTA / f"enem_{ano}.json"
    if not jp.exists():
        return {}

    with open(jp, encoding="utf-8") as f:
        questoes = json.load(f)

    corrigidos = 0

    for q in questoes:
        enun = q.get("enunciado") or []
        cmd  = (q.get("comando") or "").strip()

        # Só age quando enunciado está vazio E comando tem pelo menos 2 frases
        if enun or not cmd:
            continue

        fins = fins_de_frase(cmd)
        if len(fins) < 2:
            continue   # apenas 1 frase — não há como separar, deixa como está

        novos_enun, novo_cmd = separar_pelo_penultimo_ponto(cmd)

        if novos_enun and novo_cmd:
            q["enunciado"] = novos_enun
            q["comando"]   = novo_cmd
            corrigidos += 1

    with open(jp, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    return {"total": len(questoes), "corrigidos": corrigidos}


def main():
    print("=" * 68)
    print("  CORREÇÃO DE ENUNCIADOS — regra do penúltimo ponto")
    print("=" * 68)

    total_corr = 0

    for jp in sorted(PASTA.glob("enem_*.json")):
        ano = int(jp.stem.split("_")[1])
        if ano == 2009:
            print(f"  {ano}: ignorado (estrutura correta)")
            continue

        stats = corrigir_ano(ano)
        c = stats.get("corrigidos", 0)
        total_corr += c
        print(f"  {ano}: {c:>3} questão(ões) corrigida(s)  (total={stats.get('total',0)})")

    print(f"\n  Total geral corrigido: {total_corr}")
    print("=" * 68)


if __name__ == "__main__":
    main()
