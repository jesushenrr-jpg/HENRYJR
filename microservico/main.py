"""
main.py — Microserviço de correção de folhas de resposta HenryJr
FastAPI + OpenCV

Endpoints:
  POST /corrigir
    Body: multipart/form-data
      - file: imagem (JPEG/PNG) da folha preenchida
      - n_questoes: int (padrão 45)
    Response: JSON com respostas e metadados

  GET /health
    Response: {"status": "ok"}

  GET /
    Documentação rápida
"""

import logging
from io import BytesIO
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from corrigir import corrigir_folha, ResultadoCorrecao

# ── Config ────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HenryJr — Correção de Folhas",
    description="Microserviço de visão computacional para correção automática de folhas de resposta ENEM.",
    version="1.0.0",
)

# CORS — permite chamadas do frontend HenryJr
ORIGENS_PERMITIDAS = [
    "https://henryjr.vercel.app",
    "https://frontend-two-khaki-40.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_PERMITIDAS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Response models ───────────────────────────────────────────────────────────

class RespostaCorrecao(BaseModel):
    sucesso:         bool
    respostas:       list[str | None]   # ex: ["A", "C", None, "B", ...]
    total_questoes:  int
    n_marcadas:      int                # quantas tiveram resposta detectada
    n_ambiguas:      int                # ambíguas (baixa confiança)
    confiancas:      list[float]        # 0-1 por questão
    conf_media:      float
    erro:            Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "servico": "HenryJr — Correção de Folhas",
        "versao":  "1.0.0",
        "uso": {
            "POST /corrigir": "Corrige uma folha. Envie 'file' (JPEG/PNG) + 'n_questoes' (int).",
            "GET /health":    "Verificação de saúde do serviço.",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/corrigir", response_model=RespostaCorrecao)
async def corrigir(
    file:        UploadFile = File(..., description="Foto da folha de respostas (JPEG/PNG)"),
    n_questoes:  int        = Form(45, ge=1, le=180, description="Número de questões na folha"),
):
    """
    Recebe a foto de uma folha de respostas preenchida e retorna as respostas detectadas.

    **Requisitos da foto:**
    - Todos os 4 marcadores de canto devem estar visíveis
    - Iluminação uniforme (evitar sombras fortes)
    - Resolução mínima recomendada: 1000×1400 pixels
    - Formatos aceitos: JPEG, PNG

    **Retorno:**
    - `respostas`: lista de letras (A-E) ou `null` quando não identificada
    - `confiancas`: grau de certeza por questão (0 = inválida, 1 = certeza total)
    - `n_marcadas`: questões com resposta identificada
    - `n_ambiguas`: questões com múltiplas bolinhas parcialmente preenchidas
    """
    # Valida tipo do arquivo
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. Use JPEG ou PNG."
        )

    # Lê bytes
    try:
        img_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler imagem: {e}")

    if len(img_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Imagem muito pequena ou corrompida.")

    logger.info(f"Corrigindo folha: {file.filename} ({len(img_bytes):,} bytes, {n_questoes} questões)")

    # Executa pipeline de visão computacional
    resultado: ResultadoCorrecao = corrigir_folha(img_bytes, n_questoes)

    debug = resultado.debug_info or {}

    return RespostaCorrecao(
        sucesso        = resultado.sucesso,
        respostas      = resultado.respostas,
        total_questoes = resultado.total_questoes,
        n_marcadas     = debug.get("n_marcadas", 0),
        n_ambiguas     = debug.get("n_ambiguas", 0),
        confiancas     = resultado.confiancas,
        conf_media     = debug.get("conf_media", 0.0),
        erro           = resultado.erro,
    )
