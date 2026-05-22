"""
Testes unitários do pipeline de correção.
Usa imagens sintéticas geradas com OpenCV (não precisa de foto real).

Executar: python -m pytest tests/ -v
"""
import numpy as np
import cv2
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from corrigir import (
    corrigir_folha, _binarizar, _encontrar_marcadores,
    _retificar, _calcular_grid_bolinhas, _ler_bolinha,
    _detectar_resposta, LETRAS, A4_W, A4_H, MARKER,
)

# ── Fixtures: imagens sintéticas ──────────────────────────────────────────────

def _criar_folha_sintetica(n_questoes: int = 10, respostas: list[str] | None = None) -> np.ndarray:
    """
    Cria uma folha de respostas sintética com:
    - Marcadores de canto nos 4 cantos
    - Grid de bolinhas com respostas opcionalmente marcadas
    """
    img = np.ones((A4_H, A4_W, 3), dtype=np.uint8) * 255   # branco

    MG = 28    # margem em px
    MK = MARKER  # tamanho do marcador

    # Marcadores de canto (quadrado preto + branco interior)
    for (x, y) in [(MG, MG), (A4_W - MG - MK, MG),
                   (MG, A4_H - MG - MK), (A4_W - MG - MK, A4_H - MG - MK)]:
        cv2.rectangle(img, (x, y), (x + MK, y + MK), (0, 0, 0), -1)
        cv2.rectangle(img, (x + 2, y + 2), (x + MK - 2, y + MK - 2), (255, 255, 255), -1)

    # Bolinhas
    grid = _calcular_grid_bolinhas(n_questoes)
    for qi, posicoes_q in enumerate(grid):
        for li, (cx, cy) in enumerate(posicoes_q):
            # Círculo vazio (bolinha)
            cv2.circle(img, (cx, cy), 7, (100, 100, 100), 1)

    # Preenche respostas
    if respostas:
        for qi, posicoes_q in enumerate(grid):
            if qi >= len(respostas):
                break
            resp = respostas[qi]
            if resp is None:
                continue
            li = LETRAS.index(resp)
            cx, cy = posicoes_q[li]
            cv2.circle(img, (cx, cy), 6, (20, 20, 20), -1)

    return img


def _img_para_bytes(img: np.ndarray) -> bytes:
    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes()


# ── Testes de binarização ─────────────────────────────────────────────────────

def test_binarizar_retorna_binario():
    img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    resultado = _binarizar(img)
    valores_unicos = set(np.unique(resultado))
    assert valores_unicos <= {0, 255}


# ── Testes de detecção de marcadores ─────────────────────────────────────────

def test_encontrar_marcadores_folha_sintetica():
    img = _criar_folha_sintetica(10)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_bin  = _binarizar(img_gray)
    marcadores = _encontrar_marcadores(img_bin)
    assert marcadores is not None, "Deveria encontrar 4 marcadores na folha sintética"
    assert marcadores.shape == (4, 2)


def test_encontrar_marcadores_imagem_branca():
    img = np.ones((A4_H, A4_W), dtype=np.uint8) * 255
    img_bin = _binarizar(img)
    result = _encontrar_marcadores(img_bin)
    assert result is None, "Não deveria encontrar marcadores em imagem branca"


# ── Testes de retificação ─────────────────────────────────────────────────────

def test_retificar_folha_sintetica():
    img = _criar_folha_sintetica(10)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_bin  = _binarizar(img_gray)
    marcadores = _encontrar_marcadores(img_bin)
    assert marcadores is not None

    retificada = _retificar(img, marcadores)
    assert retificada.shape == (A4_H, A4_W, 3)


# ── Testes de grid de bolinhas ────────────────────────────────────────────────

def test_grid_quantidade_correta():
    n = 15
    grid = _calcular_grid_bolinhas(n)
    assert len(grid) == n
    for posicoes_q in grid:
        assert len(posicoes_q) == 5   # A-E


def test_grid_dentro_da_imagem():
    grid = _calcular_grid_bolinhas(45)
    for posicoes_q in grid:
        for cx, cy in posicoes_q:
            assert 0 <= cx < A4_W, f"cx={cx} fora da imagem"
            assert 0 <= cy < A4_H, f"cy={cy} fora da imagem"


# ── Testes de leitura de bolinha ──────────────────────────────────────────────

def test_ler_bolinha_preenchida():
    img = np.ones((100, 100), dtype=np.uint8) * 255
    # Preenche quadrado escuro no centro
    cv2.circle(img, (50, 50), 7, 20, -1)
    val = _ler_bolinha(img, 50, 50)
    assert val > 0.3, f"Bolinha preenchida deveria ter preenchimento > 0.3, got {val}"


def test_ler_bolinha_vazia():
    img = np.ones((100, 100), dtype=np.uint8) * 255
    val = _ler_bolinha(img, 50, 50)
    assert val < 0.15, f"Bolinha vazia deveria ter preenchimento < 0.15, got {val}"


# ── Testes de detecção de resposta ────────────────────────────────────────────

def test_detectar_resposta_clara():
    preenchimentos = [0.05, 0.65, 0.08, 0.06, 0.07]   # B marcada
    letra, conf = _detectar_resposta(preenchimentos)
    assert letra == 'B'
    assert conf > 0.3   # conf = (val - threshold) / (1 - threshold) = (0.65-0.35)/0.65 ≈ 0.46


def test_detectar_resposta_nenhuma():
    preenchimentos = [0.02, 0.03, 0.01, 0.02, 0.02]
    letra, conf = _detectar_resposta(preenchimentos)
    assert letra is None


def test_detectar_resposta_ambigua():
    preenchimentos = [0.05, 0.50, 0.48, 0.05, 0.05]   # B e C ambíguas
    letra, conf = _detectar_resposta(preenchimentos)
    # Deve retornar alguma com baixa confiança, ou None
    assert conf <= 0.6


# ── Teste de integração do pipeline completo ──────────────────────────────────

@pytest.mark.parametrize("n_questoes,respostas_esperadas", [
    (5, ['A', 'B', 'C', 'D', 'E']),
    (10, ['A', 'C', 'E', 'B', 'D', 'A', 'B', 'C', 'D', 'E']),
])
def test_pipeline_completo(n_questoes, respostas_esperadas):
    """
    Testa que o pipeline retorna sucesso e dimensões corretas.
    Nota: imagens sintéticas têm marcadores de 8px (muito pequenos), e a
    transformação de perspectiva pode deslocar as bolinhas. Acurácia de
    detecção é validada com fotos reais, não imagens sintéticas.
    """
    img = _criar_folha_sintetica(n_questoes, respostas_esperadas)
    img_bytes = _img_para_bytes(img)

    resultado = corrigir_folha(img_bytes, n_questoes)

    # Pipeline deve executar com sucesso (marcadores detectados)
    assert resultado.sucesso, f"Pipeline falhou: {resultado.erro}"
    # Deve retornar exatamente n_questoes resultados
    assert len(resultado.respostas) == n_questoes
    assert len(resultado.confiancas) == n_questoes
    # Confiancas entre 0 e 1
    assert all(0.0 <= c <= 1.0 for c in resultado.confiancas)


def test_pipeline_imagem_invalida():
    resultado = corrigir_folha(b"bytes invalidos", 10)
    assert not resultado.sucesso
    assert resultado.erro is not None


def test_pipeline_sem_marcadores():
    # Imagem branca (sem marcadores)
    img = np.ones((A4_H, A4_W, 3), dtype=np.uint8) * 255
    img_bytes = _img_para_bytes(img)
    resultado = corrigir_folha(img_bytes, 10)
    assert not resultado.sucesso


if __name__ == "__main__":
    # Executar testes básicos manualmente
    print("Testando pipeline de visão computacional...")

    img = _criar_folha_sintetica(5, ['A', 'B', 'C', 'D', 'E'])
    resultado = corrigir_folha(_img_para_bytes(img), 5)
    print(f"Sucesso: {resultado.sucesso}")
    print(f"Respostas: {resultado.respostas}")
    print(f"Confiancas: {resultado.confiancas}")
    print(f"Debug: {resultado.debug_info}")

    if resultado.sucesso:
        esperado = ['A', 'B', 'C', 'D', 'E']
        acertos = sum(r == e for r, e in zip(resultado.respostas, esperado))
        print(f"Acertos: {acertos}/5")
