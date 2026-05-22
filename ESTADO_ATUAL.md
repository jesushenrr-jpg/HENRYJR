# Estado Atual do Projeto HenryJr

> Atualizar este arquivo ao final de cada sessão de trabalho.

## Fase atual: **Fase 5.5 concluída — Fase 6 próxima**

## Última sessão: 2026-05-22

### O que foi feito nesta sessão
1. **Redesign completo "Biblioteca Cálida"** — paleta quente aplicada em todos os componentes
   - CardQuestao, login, simulado, SimuladoPlayer, resultado, progresso, tira-teima, BuscaIA, ModalReportarErro, FiltroQuestoes
   - Mapeamento: `#7c6af7` → `#D4A853`, `#1a1a2e` → `#161411`, `#2d2d44` → `#2C2820`

2. **Progresso por competência H01–H30** — novo breakdown na página `/progresso`
   - Agrupa H01-H30 por área com barras de progresso individuais
   - Mostra acertos/total e % colorida (verde/dourado/vermelho)

3. **Sincronização Supabase** — 2.880 questões ENEM sincronizadas com sucesso
   - Script `corrigir_e_sincronizar.py` criado (correção mojibake + marcar anuladas + sync)
   - Anuladas verificadas: todas 7 já estavam corretas

4. **Diagnóstico de qualidade** — `diagnostico_v2.py` criado
   - Todos os anos têm 100% competencia, pagina_pdf, anuladas
   - Falsos positivos "Ã" investigados e descartados (texto PT legítimo)

5. **Correção parcial do 2021** — `corrigir_2021_incompletas.py` criado
   - OCR focado apenas nas 14 questões com alternativas ausentes
   - 3 questões recuperadas (Q082, Q115, Q173 — texto coerente)
   - 11 permaneceram sem alternativas (limitação da fonte customizada)
   - Lixo de OCR removido; 2021 ressincronizado

6. **Deploy** — frontend deployado em `https://henryjr.vercel.app`

### Estado dos dados (json_v2)

| Ano | Total | Com alts (5) | Gabaritos | Observação |
|-----|-------|----------|-----------|------------|
| 2009 | 180 | 180 | 180 | ✅ OK |
| 2010 | 185 | 184 | 185 | ⚠️ OCR — 1 questão sem alts |
| 2011-2020 | 180/ano | 180 | 180 | ✅ OK |
| 2021 | 180 | 169 | 179 | ⚠️ 11 sem alts (fonte customizada irrecuperável via OCR) |
| 2022-2024 | 180/ano | 180 | 180 | ✅ OK |

### Questões problemáticas conhecidas (2021 — sem alternativas)
- **dia1**: Q002, Q011, Q016, Q043, Q054, Q069
- **dia2**: Q107, Q151, Q127(?), Q169, Q170
- Causa: fonte customizada que o Tesseract não decodifica
- Status: definitivamente pendente de input manual

## Fase 3 concluída ✅

| Item | Status |
|------|--------|
| Supabase Storage `provas-pdf` (64 PDFs) | ✅ |
| Supabase Storage `imagens-questoes` (569 imgs) | ✅ |
| Tabela `questoes` (2.890 questões importadas) | ✅ |
| Tabelas de usuário (7 tabelas + RLS + triggers) | ✅ |
| Auth email + Google OAuth | ✅ |

## Mobilidade configurada ✅

- ✅ GitHub: `https://github.com/jesushenrr-jpg/HENRYJR` (scripts + JSONs)
- ✅ Supabase Storage `provas-pdf`: 64 PDFs (todos os anos/dias)
- ✅ Supabase Storage `imagens-questoes`: 569 imagens
- ✅ JSONs v2: campo `supabase_url` em todas as 761 imagens
- ✅ `setup_novo_computador.bat` e `requirements.txt` criados

## Status das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Ambiente e ferramentas | ✅ Concluída |
| 2 | Extração e preparação de dados | ✅ Concluída |
| 3 | Banco de dados Supabase | ✅ Concluída |
| 4 | Interface Next.js | ✅ Concluída |
| 5 | PDF imprimível | ✅ Concluída |
| 5.5 | Microserviço correção por foto | ✅ Código pronto — **deploy pendente** no Railway |
| 6 | Simulado completo + progresso | 🔄 Em andamento |
| 7 | Deploy final | ✅ Frontend no Vercel |

## Próximos passos imediatos

### 1. Deploy do microserviço no Railway
```bash
cd microservico
# 1. Criar repo GitHub separado (ou subdir do repo principal)
# 2. Conectar no Railway → New Project → Deploy from GitHub
# 3. Railway detecta Dockerfile automaticamente
# 4. Copiar URL do serviço
# 5. No Vercel: adicionar MICROSERVICO_URL=https://seu-servico.up.railway.app
```

### 2. Questões 2021 problemáticas (11 sem alternativas)
- Revisão manual via `gerenciar_imagens.py` para inserir alternativas corretas

### 3. Frases das capas do ENEM (2009–2024)
- Fornecer as frases reais das capas → atualizar `frontend/lib/frases-capa.ts`

## Configuração de outro computador

```bash
# 1. Clonar repositório
git clone https://github.com/jesushenrr-jpg/HENRYJR.git
cd HENRYJR

# 2. Instalar dependências Python
pip install -r requirements.txt

# 3. Instalar Tesseract-OCR (para re-extração OCR)
# https://github.com/UB-Mannheim/tesseract/wiki

# 4. Restaurar memórias do Claude (opcional)
# Copiar docs/claude-memory/*.md para:
# Windows: %APPDATA%\Claude\projects\<hash-do-projeto>\memory\
# Mac/Linux: ~/.claude/projects/<hash-do-projeto>/memory/

# 5. Abrir o gerenciador
python gerenciar_imagens.py
```

## Arquivos principais

| Arquivo | Função |
|---------|--------|
| `gerenciar_imagens.py` | Gerenciador visual de questões/imagens (Tkinter) |
| `extrair_v2.py` | Extração v2 (2011-2024) |
| `reextrair_ocr.py` | Re-extração OCR para anos com fonte customizada |
| `corrigir_enunciados.py` | Regra do penúltimo ponto |
| `diagnostico_2010.md` | Diagnóstico e solução do 2010 |
| `upload_supabase.py` | Upload de PDFs e imagens para Supabase Storage |
