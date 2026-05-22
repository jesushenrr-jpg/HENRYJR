# HenryJr — Microserviço de Correção por Foto

FastAPI + OpenCV para correção automática de folhas de resposta do ENEM.

## Funcionamento

1. Recebe foto da folha preenchida (JPEG/PNG, de celular ou scanner)
2. Detecta os 4 marcadores de canto (quadrados preto+branco gerados pelo SimuladoPDF)
3. Retifica a perspectiva (corrige distorção de ângulo de foto)
4. Mapeia posição de cada bolinha (A-E) por questão
5. Mede o grau de preenchimento de cada bolinha (threshold adaptativo)
6. Retorna JSON com respostas e confiança por questão

## Execução local

```bash
cd microservico

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
uvicorn main:app --reload --port 8000

# Testar
curl http://localhost:8000/health

# Documentação interativa
open http://localhost:8000/docs
```

## Testes

```bash
# Instalar pytest
pip install pytest

# Rodar testes (gera imagens sintéticas, não precisa de foto real)
python -m pytest tests/ -v
```

## Deploy (Railway)

1. Faça push para um repositório GitHub
2. Conecte o repositório no [Railway](https://railway.app)
3. O Dockerfile é detectado automaticamente
4. Defina a variável de ambiente `PORT` (Railway faz isso automaticamente)
5. Copie a URL do serviço e defina `MICROSERVICO_URL` no Vercel

## Variável de ambiente no Vercel

No Vercel, defina:
```
MICROSERVICO_URL = https://seu-servico.up.railway.app
```

## API

### POST /corrigir

Recebe multipart/form-data:
- `file`: imagem JPEG ou PNG da folha preenchida
- `n_questoes`: número de questões (1–180, padrão 45)

Retorna:
```json
{
  "sucesso": true,
  "respostas": ["A", "C", null, "B", "E", ...],
  "total_questoes": 45,
  "n_marcadas": 43,
  "n_ambiguas": 1,
  "confiancas": [0.95, 0.88, 0.0, 0.91, ...],
  "conf_media": 0.87
}
```

### GET /health

```json
{"status": "ok"}
```
