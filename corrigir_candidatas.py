"""
Insere alternativas manualmente nas questões identificadas como
'candidata_imagem' pelo completar_alternativas.py, mas que na verdade
têm alternativas de TEXTO legíveis nas imagens renderizadas.

Transcritas diretamente a partir da leitura visual dos q*_full.jpg.
"""

import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA_JSON = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")

# ─────────────────────────────────────────────────────────────────────────────
# Alternativas transcritas visualmente dos renders (q*_full.jpg)
# chave: (ano, numero)
# ─────────────────────────────────────────────────────────────────────────────
ALTERNATIVAS = {

    # ── 2009 Q033 ─────────────────────────────────────────────────────────────
    # Biologia: coloração de pelagem de ratos × substrato — mecanismo evolutivo
    (2009, 33): {
        "A": "a alimentação, pois pigmentos de terra são absorvidos e alteram a cor da pelagem dos roedores.",
        "B": "o fluxo gênico entre as diferentes populações, que mantém constante a grande diversidade interpopulacional.",
        "C": "a seleção natural, que, nesse caso, poderia ser entendida como a sobrevivência diferenciada de indivíduos com características distintas.",
        "D": "a mutação genética, em certos ambientes, como os de solo mais escuro, têm maior ocorrência e capacidade de alterar significativamente a cor da pelagem dos animais.",
        "E": "a herança de caracteres adquiridos, capacidade de organismos se adaptarem a diferentes ambientes e transmitam suas características genéticas aos descendentes.",
    },

    # ── 2011 Q096 ─────────────────────────────────────────────────────────────
    # Biologia: exercício físico e saúde — aumento da procura por exercícios
    (2011, 96): {
        "A": "exercícios físicos aquáticos (natação/hidroginástica), que são exercícios de baixo impacto, evitando o atrito (não prejudicando as articulações), e que previnem o envelhecimento precoce e melhoram a qualidade de vida.",
        "B": "mecanismos que permitem combinar alimentação e exercício físico, que permitem a aquisição e manutenção de níveis adequados de saúde, sem a preocupação com padrões de beleza instituídos socialmente.",
        "C": "programas saudáveis de emagrecimento, que evitam os prejuízos causados na regulação metabólica, função imunológica, integridade óssea e manutenção da capacidade funcional ao longo do envelhecimento.",
        "D": "exercícios de relaxamento, reeducação postural e alongamentos, que permitem um melhor funcionamento do organismo como um todo, bem como uma dieta alimentar e hábitos saudáveis com base em produtos naturais.",
        "E": "dietas que preconizam a ingestão excessiva ou restrita de um ou mais macronutrientes (carboidratos, gorduras ou proteínas), bem como exercícios que permitam um aumento de massa muscular e/ou modelar o corpo.",
    },

    # ── 2011 Q133 ─────────────────────────────────────────────────────────────
    # Linguagens: charge sobre evolução tecnológica — metáfora evolucionista
    (2011, 133): {
        "A": "o surgimento de um homem dependente de um novo modelo tecnológico.",
        "B": "a mudança do homem em razão dos novos inventos que destroem sua realidade.",
        "C": "a problemática social de grande exclusão digital a partir da interferência da máquina.",
        "D": "a invenção de equipamentos que dificultam o trabalho do homem, em sua esfera social.",
        "E": "o retrocesso do desenvolvimento do homem em face da criação de ferramentas como lança, máquina e computador.",
    },

    # ── 2013 Q096 ─────────────────────────────────────────────────────────────
    # Linguagens: manuscrito escolar de 1911 — função do texto "A nossa bandeira"
    (2013, 96): {
        "A": "funciona como veículo de transmissão de valores patrióticos próprios do período em que foi escrito.",
        "B": "cumpre uma função instrucional de ensinar regras de comportamento em eventos cívicos.",
        "C": "deixa subentendida a ideia de que o brasileiro preserva as riquezas naturais do país.",
        "D": "argumenta em favor da construção de uma nação com igualdade de direitos.",
        "E": "apresenta uma metodologia de ensino restrita a uma determinada época.",
    },

    # ── 2017 Q102 ─────────────────────────────────────────────────────────────
    # Física/Química: datação por carbono-14 — cálculo de idade de fóssil
    (2017, 102): {
        "A": "450.",
        "B": "1 433.",
        "C": "11 460.",
        "D": "17 190.",
        "E": "27 000.",
    },

    # ── 2018 Q130 ─────────────────────────────────────────────────────────────
    # Biologia: gel de eletroforese de DNA — identificação da doadora de pólen
    (2018, 130): {
        "A": "DP1",
        "B": "DP2",
        "C": "DP3",
        "D": "DP4",
        "E": "DP5",
    },

    # ── 2020 Q050 ─────────────────────────────────────────────────────────────
    # Geografia: expansão urbana e aglomerações — resultado do processo
    (2020, 50): {
        "A": "valorização da escala local.",
        "B": "crescimento das áreas periféricas.",
        "C": "densificação do transporte ferroviário.",
        "D": "predomínio do planejamento estadual.",
        "E": "inibição de consórcios intermunicipais.",
    },

    # ── 2020 Q132 ─────────────────────────────────────────────────────────────
    # Química Verde: processo que segue princípios (equações com setas →)
    # Cabeçalho não encontrado pelo PyMuPDF (codificação/fonte especial)
    (2020, 132): {
        "A": "A + B + C → D (a reação ocorre a altas pressões).",
        "B": "A + B → C + D (a reação é fortemente endotérmica).",
        "C": "A + 3B → C (a reação ocorre com uso de solvente orgânico).",
        "D": "3A + 2B → 2C → 3D + 2E (a reação ocorre sob pressão atmosférica).",
        "E": "A + ½B → C (a reação ocorre com o uso de um catalisador contendo um metal não tóxico).",
    },

    # ── 2020 Q107 ─────────────────────────────────────────────────────────────
    # Química: estruturas químicas de óleos essenciais — qual substância usar
    # (alternativas são os números 1-5 que rotulam as fórmulas estruturais)
    (2020, 107): {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
        "E": "5",
    },

    # ── 2020 Q154 ─────────────────────────────────────────────────────────────
    # Matemática: estimativa de pessoas em manifestação por foto aérea
    (2020, 154): {
        "A": "110 000.",
        "B": "104 000.",
        "C": "93 000.",
        "D": "92 000.",
        "E": "87 000.",
    },

    # ── 2021 Q107 ─────────────────────────────────────────────────────────────
    # Linguagens: tirinha Calvin & Hobbes sobre dias úmidos — termorregulação
    # Bloco do cabeçalho começa com chars corrompidos → .match() falha no extrator
    (2021, 107): {
        "A": "a temperatura do vapor-d'água presente no ar é alta.",
        "B": "o suor apresenta maior dificuldade para evaporar do corpo.",
        "C": "a taxa de absorção de radiação pelo corpo torna-se maior.",
        "D": "o ar torna-se mau condutor e dificulta o processo de liberação de calor.",
        "E": "o vapor-d'água presente no ar condensa-se ao entrar em contato com a pele.",
    },

    # ── 2021 Q109 ─────────────────────────────────────────────────────────────
    # Ciências da Natureza: biocombustível a partir de resíduos de suínos
    # Bloco inclui alternativas de Q108 antes do cabeçalho de Q109 → .match() falha
    (2021, 109): {
        "A": "etanol.",
        "B": "biogás.",
        "C": "butano.",
        "D": "metanol.",
        "E": "biodiesel.",
    },

    # ── 2021 Q169 ─────────────────────────────────────────────────────────────
    # Matemática: mediana de terremotos magnitude ≥ 7 (2000–2011)
    # Bloco inclui alternativas de Q168 antes do cabeçalho de Q169 → .match() falha
    (2021, 169): {
        "A": "11.",
        "B": "15.",
        "C": "15,5.",
        "D": "15,7.",
        "E": "17,5.",
    },

    # ── 2021 Q178 — ANULADA ───────────────────────────────────────────────────
    # Matemática: combinatória — quantidade de painéis da CBF (Copa do Brasil)
    # Expressões com fatoriais transcritas do render (Q178 foi anulada)
    (2021, 178): {
        "A": "7!/(5!·2!) · 5!/(1!) · 7!/(5!·2!) · 9!/(4!·5!) · 10!",
        "B": "7! · 5! · 7! · 9! · 10!",
        "C": "30!",
        "D": "7!/(5!·5!) · 7!/(1·2!) · 9!/(5!·4!)",
        "E": "9!/3! · 5! · 7! · 9!/4! · 10!",
    },

    # ── 2022 Q133 ─────────────────────────────────────────────────────────────
    # Física: circuito com pilha invertida — intensidade de corrente na lâmpada
    (2022, 133): {
        "A": "0,25 A",
        "B": "0,33 A",
        "C": "0,75 A",
        "D": "1,00 A",
        "E": "1,33 A",
    },

    # ── 2023 Q092 ─────────────────────────────────────────────────────────────
    # Física: laser para leitura de CD/DVD — região espectral ideal
    (2023, 92): {
        "A": "Violeta.",
        "B": "Azul.",
        "C": "Verde.",
        "D": "Vermelho.",
        "E": "Infravermelho.",
    },

    # ── 2023 Q177 ─────────────────────────────────────────────────────────────
    # Matemática: gráfico de imunização gripe A-H1N1 — categoria mais exposta
    (2023, 177): {
        "A": "indígenas.",
        "B": "gestantes.",
        "C": "doentes crônicos.",
        "D": "adultos entre 20 e 29 anos.",
        "E": "crianças de 6 meses a 2 anos.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
def atualizar_json(ano: int, correcoes: dict) -> int:
    """Aplica as correções ao JSON do ano. Retorna nº de questões atualizadas."""
    json_path = PASTA_JSON / f"enem_{ano}.json"
    with open(json_path, encoding="utf-8") as f:
        questoes = json.load(f)

    n = 0
    for q in questoes:
        num = q["numero"]
        if num in correcoes:
            q["alternativas"] = correcoes[num]
            q["confianca"]    = max(float(q.get("confianca") or 0), 0.85)
            q["revisado"]     = True
            n += 1

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    return n


def main():
    print("=" * 60)
    print("  CORREÇÃO MANUAL DE CANDIDATAS A IMAGEM")
    print("=" * 60)

    # Agrupar por ano
    por_ano: dict[int, dict] = {}
    for (ano, num), alts in ALTERNATIVAS.items():
        por_ano.setdefault(ano, {})[num] = alts

    total = 0
    for ano in sorted(por_ano):
        correcoes = por_ano[ano]
        n = atualizar_json(ano, correcoes)
        total += n
        for num, alts in sorted(correcoes.items()):
            preview = alts.get("A", "")[:60]
            print(f"  {ano} Q{num:03d}  A={preview}")

    print(f"\n  Total atualizado: {total} questoes")
    print("=" * 60)


if __name__ == "__main__":
    main()
