"""
corrigir.py
Pipeline de visão computacional para correção de folhas de resposta.

Fluxo:
  1. Recebe imagem (JPEG/PNG, foto de celular com leve distorção de perspectiva)
  2. Detecta os 4 marcadores de canto (quadrado preto com interior branco)
  3. Aplica transformação de perspectiva (homografia) → retifica a folha
  4. Localiza as bolinhas de cada questão por posição relativa fixa
  5. Para cada questão, determina qual bolinha (A-E) está preenchida
  6. Retorna lista de respostas

Layout esperado da folha de respostas (gerado pelo SimuladoPDF):
  - Margem superior: ~28 pt ≈ 28/842 da altura A4
  - Margem lateral: ~28 pt
  - Marcadores de canto: 8×8 pt nos 4 cantos
  - 5 questões por linha, cada célula com 5 bolinhas (A-E)
  - Linhas separadas a cada 4 grupos
"""

import math
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np


# ── Constantes de layout (coordenadas relativas 0-1 em relação ao A4 retificado) ──
# Baseadas no layout do SimuladoPDF.tsx (tamanho A4: 595×842 pt)
# Margem 28 pt, marcadores 8×8 pt nos cantos

MARKER      = 8             # tamanho físico do marcador de canto (pontos PDF → ~11px a 96DPI)
MARGEM_REL  = 28  / 595   # ~0.047 da largura
MARKER_REL  = MARKER / 842  # ~0.0095 da altura

# Cabeçalho da folha (~18% da altura útil)
HEADER_HEIGHT_REL = 0.20

# Largura de cada célula (questão): área útil / 5 questões por linha
QUESTOES_POR_LINHA = 5
LETRAS = ['A', 'B', 'C', 'D', 'E']


@dataclass
class ResultadoCorrecao:
    sucesso:          bool
    respostas:        list[str | None]   # None = não marcada ou inválida
    total_questoes:   int
    confiancas:       list[float]        # 0-1 por questão
    erro:             Optional[str] = None
    debug_info:       dict              = field(default_factory=dict)


# ── 1. Detecção dos marcadores de canto ───────────────────────────────────────

def _binarizar(img_gray: np.ndarray) -> np.ndarray:
    """Threshold adaptativo para lidar com variações de iluminação."""
    blur = cv2.GaussianBlur(img_gray, (7, 7), 0)
    return cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        blockSize=21, C=8
    )


def _encontrar_marcadores(img_bin: np.ndarray) -> Optional[np.ndarray]:
    """
    Encontra os 4 marcadores de canto (quadrados pequenos nos cantos da folha).
    Estratégia: procura quadriláteros quadrados em cada quadrante da imagem.
    Retorna array shape (4,2) com coords (x,y) ou None se falhar.
    """
    contornos, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = img_bin.shape

    # Tamanho esperado: marcadores entre 0.5% e 5% de cada dimensão
    area_min = (w * 0.004) * (h * 0.004)
    area_max = (w * 0.08)  * (h * 0.08)

    # Divide a imagem em 4 quadrantes e busca o melhor candidato em cada um
    quadrantes = [
        (0,     0,     w // 2, h // 2),   # topo-esq
        (w // 2, 0,    w,      h // 2),   # topo-dir
        (0,     h // 2, w // 2, h),       # baixo-esq
        (w // 2, h // 2, w,    h),        # baixo-dir
    ]

    selecionados = []

    for (qx0, qy0, qx1, qy1) in quadrantes:
        melhor = None
        melhor_dist = float('inf')

        # Canto esperado deste quadrante
        canto_x = (qx0 + qx1) / 2 - (qx1 - qx0) * 0.25 if qx0 == 0 else (qx0 + qx1) / 2 + (qx1 - qx0) * 0.25
        canto_y = (qy0 + qy1) / 2 - (qy1 - qy0) * 0.25 if qy0 == 0 else (qy0 + qy1) / 2 + (qy1 - qy0) * 0.25

        for cnt in contornos:
            area = cv2.contourArea(cnt)
            if area < area_min or area > area_max:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            cx, cy = x + bw // 2, y + bh // 2

            # Deve estar dentro do quadrante
            if not (qx0 <= cx <= qx1 and qy0 <= cy <= qy1):
                continue

            # Forma aproximadamente quadrada
            aspect = bw / max(bh, 1)
            if not (0.5 < aspect < 2.0):
                continue

            # Aproximar para quadrilátero
            peri  = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.06 * peri, True)
            if len(approx) not in (3, 4, 5, 6):
                continue

            # Prefere o candidato mais próximo do canto real do quadrante
            dist = ((cx - canto_x) ** 2 + (cy - canto_y) ** 2) ** 0.5
            if dist < melhor_dist:
                melhor_dist = dist
                melhor = (float(cx), float(cy))

        if melhor is None:
            return None
        selecionados.append(melhor)

    return np.array(selecionados, dtype=np.float32)


def _ordenar_cantos(pts: np.ndarray) -> np.ndarray:
    """
    Ordena 4 pontos: [topo-esq, topo-dir, baixo-esq, baixo-dir].
    """
    pts_sum = pts.sum(axis=1)
    pts_diff = np.diff(pts, axis=1).flatten()

    tl = pts[np.argmin(pts_sum)]   # menor soma x+y
    br = pts[np.argmax(pts_sum)]   # maior soma x+y
    tr = pts[np.argmin(pts_diff)]  # menor y-x
    bl = pts[np.argmax(pts_diff)]  # maior y-x

    return np.array([tl, tr, bl, br], dtype=np.float32)


# ── 2. Retificação de perspectiva ─────────────────────────────────────────────

A4_W = 794   # pixels (A4 a 96 DPI)
A4_H = 1123

def _retificar(img: np.ndarray, marcadores: np.ndarray) -> np.ndarray:
    """Aplica homografia para retificar a perspectiva da folha."""
    src = _ordenar_cantos(marcadores)
    dst = np.array([
        [0,    0],
        [A4_W, 0],
        [0,    A4_H],
        [A4_W, A4_H],
    ], dtype=np.float32)

    M, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if M is None:
        raise ValueError("Não foi possível calcular homografia")

    retificada = cv2.warpPerspective(img, M, (A4_W, A4_H))
    return retificada


# ── 3. Localização das bolinhas ───────────────────────────────────────────────

def _calcular_grid_bolinhas(n_questoes: int) -> list[list[tuple[int, int]]]:
    """
    Calcula posições (cx, cy) de cada bolinha no grid.
    Retorna lista[questão][letra] = (x, y) em pixels no A4 retificado.

    Layout:
      - Área útil começa em x=MARGEM, y=HEADER_HEIGHT (após cabeçalho)
      - 5 questões por linha
      - Cada questão tem 5 bolinhas horizontais (A-E)
      - Bolinha ≈ 10pt de diâmetro → ~14px a 96DPI
    """
    MARGEM_X = int(MARGEM_REL * A4_W)   # ~37 px
    MARGEM_Y = int(HEADER_HEIGHT_REL * A4_H)  # ~225 px
    UTIL_W   = A4_W - 2 * MARGEM_X
    UTIL_H   = A4_H - MARGEM_Y - 50   # reserva rodapé

    CELULA_W = UTIL_W // QUESTOES_POR_LINHA   # ~144 px
    BOLINHA_D = 14   # diâmetro estimado em px
    BOLINHA_ESPACO = 3   # espaço entre bolinhas

    n_linhas = math.ceil(n_questoes / QUESTOES_POR_LINHA)
    ALT_LINHA = UTIL_H // max(n_linhas, 1)

    posicoes = []
    for q in range(n_questoes):
        linha  = q // QUESTOES_POR_LINHA
        coluna = q  % QUESTOES_POR_LINHA

        # Centro da célula
        cx_celula = MARGEM_X + coluna * CELULA_W + CELULA_W // 2
        cy_celula = MARGEM_Y + linha  * ALT_LINHA + ALT_LINHA // 2

        # 5 bolinhas centradas na célula
        total_w = 5 * BOLINHA_D + 4 * BOLINHA_ESPACO
        x0 = cx_celula - total_w // 2

        posicoes_q = []
        for i in range(5):
            bx = x0 + i * (BOLINHA_D + BOLINHA_ESPACO) + BOLINHA_D // 2
            posicoes_q.append((bx, cy_celula))
        posicoes.append(posicoes_q)

    return posicoes


# ── 4. Leitura de cada bolinha ────────────────────────────────────────────────

def _ler_bolinha(img_gray: np.ndarray, cx: int, cy: int, raio: int = 7) -> float:
    """
    Retorna o grau de preenchimento (0=vazia, 1=totalmente preenchida).
    Analisa a média de escuridão em um disco de raio `raio` ao redor de (cx, cy).
    """
    h, w = img_gray.shape
    x1 = max(0, cx - raio)
    x2 = min(w, cx + raio + 1)
    y1 = max(0, cy - raio)
    y2 = min(h, cy + raio + 1)

    if x2 <= x1 or y2 <= y1:
        return 0.0

    roi = img_gray[y1:y2, x1:x2]

    # Máscara circular
    yr, xr = np.ogrid[-raio:raio + 1, -raio:raio + 1]
    mask = (xr * xr + yr * yr <= raio * raio).astype(np.uint8)
    mask = mask[:roi.shape[0], :roi.shape[1]]

    pixels = roi[mask == 1]
    if len(pixels) == 0:
        return 0.0

    # Escuridão relativa (255 = preto, 0 = branco)
    escuridao = 1 - pixels.mean() / 255.0
    return float(escuridao)


THRESHOLD_PREENCHIDA = 0.35   # bolinha com >35% de escuridão = marcada
DIFERENCA_MINIMA     = 0.10   # diferença mínima da melhor para segunda melhor


def _detectar_resposta(preenchimentos: list[float]) -> tuple[str | None, float]:
    """
    Dado vetor de preenchimento (A-E), retorna (letra, confiança).
    Retorna (None, 0.0) se nenhuma ou múltiplas estiverem marcadas.
    """
    if not preenchimentos:
        return None, 0.0

    idx_max = int(np.argmax(preenchimentos))
    val_max = preenchimentos[idx_max]

    if val_max < THRESHOLD_PREENCHIDA:
        return None, 0.0   # nenhuma marcada

    # Verifica se há segunda bolinha muito próxima (resposta ambígua)
    sorted_vals = sorted(preenchimentos, reverse=True)
    if len(sorted_vals) >= 2 and (sorted_vals[0] - sorted_vals[1]) < DIFERENCA_MINIMA:
        return None, 0.5   # ambígua — baixa confiança, mas retorna a melhor

    confianca = min(1.0, (val_max - THRESHOLD_PREENCHIDA) / (1 - THRESHOLD_PREENCHIDA))
    return LETRAS[idx_max], confianca


# ── 5. Pipeline completo ──────────────────────────────────────────────────────

def corrigir_folha(
    img_bytes: bytes,
    n_questoes: int,
) -> ResultadoCorrecao:
    """
    Pipeline principal de correção.

    Parâmetros:
      img_bytes  — bytes da imagem (JPEG/PNG)
      n_questoes — número de questões esperado

    Retorna ResultadoCorrecao com respostas e metadados.
    """
    # Decodifica imagem
    nparr = np.frombuffer(img_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ResultadoCorrecao(
            sucesso=False, respostas=[], total_questoes=n_questoes,
            confiancas=[], erro="Não foi possível decodificar a imagem"
        )

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_bin  = _binarizar(img_gray)

    # Detecta marcadores de canto
    marcadores = _encontrar_marcadores(img_bin)
    if marcadores is None:
        return ResultadoCorrecao(
            sucesso=False, respostas=[], total_questoes=n_questoes,
            confiancas=[],
            erro="Marcadores de canto não encontrados. Fotografe a folha inteira com os 4 cantos visíveis.",
            debug_info={"shape": img.shape}
        )

    # Retifica perspectiva
    try:
        img_ret  = _retificar(img, marcadores)
    except ValueError as e:
        return ResultadoCorrecao(
            sucesso=False, respostas=[], total_questoes=n_questoes,
            confiancas=[], erro=str(e)
        )

    img_gray_ret = cv2.cvtColor(img_ret, cv2.COLOR_BGR2GRAY)

    # Mapa de bolinhas
    grid = _calcular_grid_bolinhas(n_questoes)

    respostas:  list[str | None] = []
    confiancas: list[float]      = []

    for i, posicoes_q in enumerate(grid):
        preenchimentos = [
            _ler_bolinha(img_gray_ret, cx, cy)
            for cx, cy in posicoes_q
        ]
        letra, conf = _detectar_resposta(preenchimentos)
        respostas.append(letra)
        confiancas.append(round(conf, 3))

    n_marcadas  = sum(1 for r in respostas if r)
    n_ambiguas  = sum(1 for r, c in zip(respostas, confiancas) if r and c < 0.8)
    conf_media  = float(np.mean(confiancas)) if confiancas else 0.0

    return ResultadoCorrecao(
        sucesso=True,
        respostas=respostas,
        total_questoes=n_questoes,
        confiancas=confiancas,
        debug_info={
            "n_marcadas":  n_marcadas,
            "n_ambiguas":  n_ambiguas,
            "conf_media":  round(conf_media, 3),
            "img_retif":   img_ret.shape,
        }
    )
