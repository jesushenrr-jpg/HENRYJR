"""
Recorta alternativas individuais das questões com imagens do ENEM 2010.
Questões alvo: Q080, Q084, Q102, Q136, Q137 (q137_2), Q142

Salva q{N:03d}_alt_{LETRA}.jpg e atualiza JSON com imagens_alternativas.
"""

import json
import sys
import numpy as np
from PIL import Image
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA_IMAGENS = Path(r"C:\PROJETOS\HENRYJR\dados\imagens\2010")
JSON_PATH     = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2\enem_2010.json")
LETRAS        = "ABCDE"


# ---------------------------------------------------------------------------
# Deteccao de clusters de pixels escuros em faixa x
# ---------------------------------------------------------------------------

def achar_clusters(arr_gray, x_ini, x_fim, threshold=110, min_sz=20, max_sz=130, gap=30):
    """
    Retorna lista de (y_centro, dark_pixels) para clusters na faixa x_ini:x_fim.
    Ignora clusters em y < 50 (bordas/cabecalho) e y > H-150 (rodape/proxima questao).
    """
    H = arr_gray.shape[0]
    strip = arr_gray[:, x_ini:x_fim]
    dark  = (strip < threshold).any(axis=1)

    clusters, in_c, start = [], False, 0
    for y, d in enumerate(dark):
        if d and not in_c:
            start, in_c = y, True
        elif not d and in_c:
            clusters.append([start, y - 1])
            in_c = False
    if in_c:
        clusters.append([start, H - 1])

    # Fundir clusters proximos
    merged = []
    for s, e in clusters:
        if merged and s - merged[-1][1] < gap:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    resultado = []
    for s, e in merged:
        sz = e - s
        if sz < min_sz or sz > max_sz:
            continue
        cy = (s + e) // 2
        if cy < 50 or cy > H - 150:   # filtra borda superior E rodape
            continue
        dark_px = int((strip[s:e+1, :] < threshold).sum())
        resultado.append((cy, dark_px))

    return resultado


def selecionar_ultimos(clusters, n=5):
    """
    Retorna os n clusters com MAIOR y (os mais abaixo na imagem), ordenados por y.
    As alternativas ficam no final da imagem; falsos positivos do enunciado ficam no topo.
    """
    ordenados = sorted(clusters, key=lambda c: c[0])
    return [c[0] for c in ordenados[-n:]]


def calcular_bordas(centros, altura, margem_topo=60):
    """
    Converte centros dos marcadores em (y_top, y_bot) de cada alternativa.
    Para a ultima alternativa, usa avg_gap*0.55 em vez de ir ate H (evita rodape).
    """
    avg_gap = (centros[-1] - centros[0]) / max(1, len(centros) - 1)
    bordas = []
    for i, cy in enumerate(centros):
        if i == 0:
            y_top = max(0, centros[0] - margem_topo)
        else:
            y_top = (centros[i - 1] + cy) // 2

        if i == len(centros) - 1:
            y_bot = min(altura, cy + int(avg_gap * 0.45))
        else:
            y_bot = (cy + centros[i + 1]) // 2

        bordas.append((y_top, y_bot))
    return bordas


def calcular_bordas_offset(centros, altura, margem_topo=60, offset=100):
    """
    Para questoes onde o CONTEUDO vem ANTES do marcador (imagem de arte acima da letra).
    Boundary = marcador_anterior + offset.
    """
    bordas = []
    prev_bot = max(0, centros[0] - margem_topo)
    for i, cy in enumerate(centros):
        y_top = prev_bot
        if i < len(centros) - 1:
            y_bot = cy + offset
        else:
            y_bot = min(altura, cy + offset * 2)
        bordas.append((y_top, y_bot))
        prev_bot = y_bot
    return bordas


def calcular_bordas_nextmarker(centros, altura, margem_topo=30):
    """
    Usa o marcador SEGUINTE como boundary inferior de cada alternativa.
    Correto para questoes onde o marcador fica no TOPO do conteudo e os
    espacamentos entre alternativas sao variaveis (ex: Q136 lousa).
    """
    gaps = [centros[i + 1] - centros[i] for i in range(len(centros) - 1)]
    avg_gap = sum(gaps) / len(gaps)
    bordas = []
    for i, cy in enumerate(centros):
        y_top = max(0, cy - margem_topo) if i == 0 else centros[i]
        if i < len(centros) - 1:
            y_bot = centros[i + 1]
        else:
            y_bot = min(altura, cy + int(avg_gap))
        bordas.append((y_top, y_bot))
    return bordas


# ---------------------------------------------------------------------------
# Funcoes de recorte por modo
# ---------------------------------------------------------------------------

def recortar_vertical(img, x_ini_mk, x_fim_mk, threshold=110,
                      margem_topo=60, use_offset=False, alt_offset=100,
                      use_nextmarker=False,
                      x_start=0, x_end=None):
    """Recorta 5 alternativas em layout vertical."""
    arr = np.array(img.convert("L"))
    W, H = img.size
    if x_end is None:
        x_end = W

    clusters = achar_clusters(arr, x_ini_mk, x_fim_mk, threshold=threshold)
    print(f"    Clusters detectados: {[(c, d) for c, d in clusters]}")

    centros = selecionar_ultimos(clusters, n=5)
    print(f"    Centros selecionados: {centros}")

    if len(centros) < 5:
        return None

    if use_nextmarker:
        bordas = calcular_bordas_nextmarker(centros, H, margem_topo)
    elif use_offset:
        bordas = calcular_bordas_offset(centros, H, margem_topo, alt_offset)
    else:
        bordas = calcular_bordas(centros, H, margem_topo)

    return {LETRAS[i]: img.crop((x_start, yt, x_end, yb))
            for i, (yt, yb) in enumerate(bordas)}


def recortar_splits_y(img, splits_y, x_start=0, x_end=None):
    """
    Recorta alternativas usando limites verticais explícitos (splits_y).
    splits_y: lista de 6 valores [y0, y1, y2, y3, y4, y5] onde alt i = [y_i, y_{i+1}].
    """
    W, H = img.size
    if x_end is None:
        x_end = W
    ys = splits_y + [H]  # garante que a ultima alt vai ate H se splits_y tiver apenas 5 valores
    if len(splits_y) == 6:
        ys = splits_y  # 6 valores = 5 pares
    resultado = {}
    for i in range(5):
        resultado[LETRAS[i]] = img.crop((x_start, ys[i], x_end, ys[i + 1]))
        print(f"    Alt {LETRAS[i]}: y={ys[i]}-{ys[i+1]} ({ys[i+1]-ys[i]}px)")
    return resultado


def recortar_q137_colunas(img):
    """
    q137_2.jpg tem 2 subcolunas: esq=A,B,C | dir=D,E.
    Splits ajustados para excluir o texto do comando que aparece no topo.
    Margens laterais: esq remove borda da pagina (x_ini=15), dir remove divisor (x_ini=meio+8).
    """
    W, H = img.size
    meio = W // 2   # ~652

    # Limites horizontais sem sobreposicao
    esq_x1, esq_x2 = 30,      meio - 10   # ~30 a ~642  (remove borda esq x=23-26)
    dir_x1, dir_x2 = meio + 10, W - 162   # ~662 a ~1142 (remove linha cinza x≈1144)

    # Splits verticais calibrados (excluem texto do comando no topo)
    esq_splits = [500, 935, 1210]   # A: 500-935, B: 935-1210, C: 1210-H
    dir_splits  = [530, 960]        # D: 530-960, E: 960-H

    print(f"    Q137 esq splits: {esq_splits}  dir splits: {dir_splits}")

    resultado = {}

    # Coluna esquerda: A, B, C
    esq_bounds = [
        (esq_splits[0], esq_splits[1]),
        (esq_splits[1], esq_splits[2]),
        (esq_splits[2], H),
    ]
    for i, (yt, yb) in enumerate(esq_bounds):
        resultado[LETRAS[i]] = img.crop((esq_x1, yt, esq_x2, yb))

    # Coluna direita: D, E
    dir_bounds = [
        (dir_splits[0], dir_splits[1]),
        (dir_splits[1], H),
    ]
    for i, (yt, yb) in enumerate(dir_bounds):
        resultado[LETRAS[3 + i]] = img.crop((dir_x1, yt, dir_x2, yb))

    return resultado


# ---------------------------------------------------------------------------
# Configuracao por questao
# ---------------------------------------------------------------------------

QUESTOES = {
    # Q80: diagrama de refracao — marcador a x=165-200, threshold=100
    # margem_topo=120: exclui texto enunciado (termina em ~y=751) e inclui label
    # "metamaterial" + ponta do raio refratado (~y=865)
    80: {
        "dia": "dia1", "img": "q080_1.jpg", "modo": "vertical",
        "x": (165, 200), "thr": 100,
        "margem_topo": 120, "x_start": 0, "x_end_off": -30,
    },
    # Q84: formulas estruturais — mesmo layout de Q80
    # margem_topo=165: exclui texto enunciado (termina ~y=842) e inclui atomo O
    # acima do P (~y=896)
    84: {
        "dia": "dia1", "img": "q084_1.jpg", "modo": "vertical",
        "x": (165, 200), "thr": 100,
        "margem_topo": 165, "x_start": 0, "x_end_off": -30,
    },
    # Q102: obras de arte — conteudo (pintura) vem ANTES do marcador
    # thr=80 pega apenas circulos pretos; use_offset: boundary = marcador+100
    # margem_topo=340: inicia na pintura de A sem texto do enunciado
    # x_start=30: remove borda esquerda da coluna (x=23-26 na source)
    102: {
        "dia": "dia2", "img": "q102_1.jpg", "modo": "vertical",
        "x": (62, 90), "thr": 80,
        "margem_topo": 340, "use_offset": True, "alt_offset": 70,
        "x_start": 30,
    },
    # Q136: diagramas de lousa — splits_y hardcoded a partir dos midpoints dos gaps entre frames
    # Frames identificados: A=712-855, B=882-1026, C=1053-1197, D=1226-1370, E=1393-1537
    # Gaps: 856-881, 1027-1052, 1198-1225, 1371-1392
    # x_start=42 remove borda esquerda da pagina; x_end_off=-18 inclui borda direita do frame
    136: {
        "dia": "dia2", "img": "q136_1.jpg", "modo": "splits_y",
        "splits_y": [690, 868, 1039, 1211, 1381, 1545],
        "x_start": 42, "x_end_off": -18,
    },
    # Q137: planificacoes geometricas em 2 colunas — tratado separadamente
    137: {"dia": "dia2", "img": "q137_2.jpg", "modo": "colunas"},
    # Q142: graficos de funcao — x_start=120 exclui marcador (letra duplicada)
    # margem_topo=265: exclui ultima linha do enunciado (~y<573) e inclui
    # titulo "Altura (cm)" (~y=575)
    142: {
        "dia": "dia2", "img": "q142_1.jpg", "modo": "vertical",
        "x": (60, 100), "thr": 110,
        "margem_topo": 265, "x_start": 120, "x_end_off": -90,
    },
}

FALLBACK_Y = {80: 860, 84: 980, 102: 760, 136: 580, 142: 720}


def processar_questao(num, cfg):
    dia  = cfg["dia"]
    src  = PASTA_IMAGENS / dia / cfg["img"]

    if not src.exists():
        print(f"  [Q{num:03d}] ERRO: {src} nao encontrado")
        return {}

    img = Image.open(src)
    W, H = img.size
    print(f"\n  Q{num:03d} ({cfg['modo']}) - {src.name}  {img.size}")

    if cfg["modo"] == "colunas":
        recortes = recortar_q137_colunas(img)
    elif cfg["modo"] == "splits_y":
        x_end = W + cfg.get("x_end_off", 0) if cfg.get("x_end_off", 0) < 0 else cfg.get("x_end_off", W)
        recortes = recortar_splits_y(img, cfg["splits_y"], x_start=cfg.get("x_start", 0), x_end=x_end)
    else:
        x_end = W + cfg.get("x_end_off", 0) if cfg.get("x_end_off", 0) < 0 else cfg.get("x_end_off", W)
        recortes = recortar_vertical(
            img,
            cfg["x"][0], cfg["x"][1],
            threshold=cfg.get("thr", 110),
            margem_topo=cfg.get("margem_topo", 60),
            use_offset=cfg.get("use_offset", False),
            alt_offset=cfg.get("alt_offset", 100),
            use_nextmarker=cfg.get("use_nextmarker", False),
            x_start=cfg.get("x_start", 0),
            x_end=x_end,
        )
        if recortes is None:
            fy = FALLBACK_Y.get(num, H // 3)
            print(f"    AVISO: deteccao falhou - fallback y={fy}")
            step = (H - fy) // 5
            x_start = cfg.get("x_start", 0)
            x_end = W + cfg.get("x_end_off", 0) if cfg.get("x_end_off", 0) < 0 else W
            recortes = {
                LETRAS[i]: img.crop((x_start, fy + i * step, x_end, fy + (i + 1) * step))
                for i in range(5)
            }

    pasta = PASTA_IMAGENS / dia
    resultado = {}
    for letra in sorted(recortes):
        crop_img = recortes[letra]
        nome = f"q{num:03d}_alt_{letra}.jpg"
        dest = pasta / nome
        crop_img.save(str(dest), "JPEG", quality=92)
        resultado[letra] = f"2010/{dia}/{nome}"
        print(f"    Alt {letra}: {crop_img.size} -> {dest.name}")

    return resultado


# ---------------------------------------------------------------------------
# Atualizacao do JSON
# ---------------------------------------------------------------------------

def atualizar_json(por_questao):
    with open(JSON_PATH, encoding="utf-8") as f:
        questoes = json.load(f)

    n = 0
    for q in questoes:
        if q["numero"] in por_questao:
            q["imagens_alternativas"] = por_questao[q["numero"]]
            n += 1

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    print(f"\n  JSON atualizado: {n} questoes com imagens_alternativas")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  RECORTE DE ALTERNATIVAS - 2010")
    print("=" * 60)

    todos = {}
    for num, cfg in sorted(QUESTOES.items()):
        res = processar_questao(num, cfg)
        if res:
            todos[num] = res

    print("\n-- Atualizando JSON --")
    atualizar_json(todos)

    print("\n" + "=" * 60)
    print("  CONCLUIDO")
    print("=" * 60)


if __name__ == "__main__":
    main()
