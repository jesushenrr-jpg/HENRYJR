# Estado Atual do Projeto HenryJr

> Atualizar este arquivo ao final de cada sessão de trabalho.

## Fase atual: **Fase 2 — Extração e Preparação de Dados**

## Última sessão: 2026-05-08

### O que foi feito nesta sessão
1. **Corrigido ENEM 2010 (re-extração OCR completa)**
   - Problema original: 155/180 questões com alternativas completamente erradas (fonte customizada no PDF)
   - Solução: `reextrair_ocr.py` com estratégia híbrida de detecção de alternativas
   - Resultado: 184/185 com alternativas, 185/185 gabaritos preservados
   - Script: `reextrair_ocr.py` (generalizado — funciona para qualquer ano)
   
2. **ENEM 2021 também re-extraído** com o script melhorado (54 fragmentos vs 58 antes)

3. **Diagnóstico registrado** em `diagnostico_2010.md` com estatísticas finais

4. **Configuração de mobilidade iniciada**
   - GitHub: `https://github.com/jesushenrr-jpg/HENRYJR`
   - Supabase Storage: upload de PDFs e imagens em andamento

### Estado dos dados (json_v2)

| Ano | Total | Com alts | Gabaritos | Observação |
|-----|-------|----------|-----------|------------|
| 2009 | 180 | 180 | 180 | ✅ OK |
| 2010 | 185 | 184 | 185 | ⚠️ 77 fragmentos (60 c/imagem) — OCR |
| 2011-2020 | 180/ano | ~180 | 180 | ✅ OK (normalizado) |
| 2021 | 185 | 171 | 184 | ⚠️ 13 não localizados no OCR |
| 2022-2024 | 180/ano | ~180 | 180 | ✅ OK |

### Questões problemáticas conhecidas
- **2010 Q108 dia2**: não localizada no OCR — precisa revisão manual
- **2021 dia1**: Q011, Q016, Q043, Q054, Q069, Q082 — não localizadas (imagens?)
- **2021 dia2**: Q107, Q115, Q127, Q151, Q169, Q173 — não localizadas
- **2010**: 17 questões sem imagem com fragmentos de alternativas — revisão manual necessária

## Próximos passos imediatos

- [ ] Obter **service role key** do Supabase (Settings → API → service_role)
- [ ] Upload de PDFs → Supabase Storage bucket `provas-pdf`
- [ ] Upload de imagens → Supabase Storage bucket `imagens-questoes`
- [ ] Modificar `gerenciar_imagens.py` para auto-upload ao adicionar imagens
- [ ] Revisão manual das questões 2010 problemáticas via gerenciador
- [ ] Revisão manual das questões 2021 não localizadas

## Após mobilidade configurada (próximas sessões)
- Continuar validação manual via gerenciador (revisado=True)
- Extrair `pagina_pdf` para todos os anos
- Classificar competências H01-H30 via Groq
- Marcar questões anuladas (lista no CLAUDE.md)

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
